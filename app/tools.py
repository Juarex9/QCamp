"""Remito tools. extract_remito has no IO; save_remito validates and INSERTs."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime

from pydantic import ValidationError

from app.models import ExtractResult, HarvestSummary, RemitoIn, RemitoOut, RemitoSave


class RemitoValidationError(ValueError):
    """Raised when save_remito rejects payload (no INSERT)."""

    def __init__(self, message: str, raw_ocr: str | None = None) -> None:
        super().__init__(message)
        self.raw_ocr = raw_ocr or ""


class RemitoNotFoundError(LookupError):
    """Raised when a remito id does not exist."""


class DuplicateRemitoError(ValueError):
    """An identical remito (fecha + patente + kg) already exists.

    Not a hard block: a truck can legitimately do two identical trips in one
    day. The caller must re-submit with explicit confirmation to insert.
    """

    def __init__(self, message: str, duplicates: list[RemitoOut]):
        super().__init__(message)
        self.duplicates = duplicates


# --- deterministic ticket-text parser ---------------------------------------
# The LLM orchestrates, but the values that get persisted should come from the
# ticket text whenever a regex can find them. Labels cover the synthetic
# fixtures (TONELAJE:) and common balanza layouts (NETO / PESO NETO).

_STOP_LABELS = (
    r"(?:FECHA|PATENTE|TONELAJE|NETO|BRUTO|TARA|ORIGEN|DESTINO"
    r"|PRODUCTO|HUMEDAD|CHOFER|PESO|TICKET)"
)
_KG_LABEL_RE = re.compile(
    r"(?:PESO\s+NETO|NETO|TONELAJE|KILOS?\s+NETOS?)\s*:?\s*([\d][\d.,]*)",
    re.IGNORECASE,
)
_KG_GENERIC_RE = re.compile(r"([\d][\d.,]*)\s*(?:KGS?|KILOS)\b", re.IGNORECASE)
_PATENTE_LABEL_RE = re.compile(
    r"PATENTE\s*:?\s*([A-Z]{2}\s?\d{3}\s?[A-Z]{2}|[A-Z]{3}\s?\d{3})",
    re.IGNORECASE,
)
_PATENTE_LOOSE_RE = re.compile(r"\b([A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d{3})\b")
_FECHA_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_FECHA_DMY_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
_HUMEDAD_RE = re.compile(r"HUMEDAD\s*:?\s*([\d][\d.,]*)", re.IGNORECASE)
_PRODUCTO_RE = re.compile(
    rf"PRODUCTO\s*:?\s*([^\n]+?)(?=\s+{_STOP_LABELS}\b|\s*$|\n)",
    re.IGNORECASE | re.MULTILINE,
)
_ORIGEN_RE = re.compile(
    rf"ORIGEN\s*:?\s*([^\n]+?)(?=\s+{_STOP_LABELS}\b|\s*$|\n)",
    re.IGNORECASE | re.MULTILINE,
)
_DESTINO_RE = re.compile(
    rf"DESTINO\s*:?\s*([^\n]+?)(?=\s+{_STOP_LABELS}\b|\s*$|\n)",
    re.IGNORECASE | re.MULTILINE,
)
_CROP_RE = re.compile(
    r"\b(soja|ma[ií]z|trigo|girasol|sorgo|cebada|algod[oó]n"
    r"|poroto|garbanzo|ca[ñn]a|lim[oó]n)\b",
    re.IGNORECASE,
)


def _parse_localized_number(text: str) -> float | None:
    """Parse '28.740', '28,740', '1.234,5' and '13,4' the Argentine way.

    A single separator followed by exactly 3 digits is treated as a
    thousands separator: scale tickets print whole kilos.
    """
    cleaned = text.strip().strip(".,")
    if not cleaned:
        return None
    has_dot = "." in cleaned
    has_comma = "," in cleaned
    if has_dot and has_comma:
        if cleaned.rfind(".") > cleaned.rfind(","):
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif has_dot or has_comma:
        sep = "." if has_dot else ","
        head, _, tail = cleaned.rpartition(sep)
        if head and len(tail) == 3:
            cleaned = cleaned.replace(sep, "")
        elif sep == ",":
            cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _find_kg(text: str) -> float | None:
    labeled = _KG_LABEL_RE.search(text)
    if labeled:
        return _parse_localized_number(labeled.group(1))
    values = {
        parsed
        for match in _KG_GENERIC_RE.finditer(text)
        if (parsed := _parse_localized_number(match.group(1))) is not None
    }
    # Several distinct "<n> kg" without a NETO label (bruto/tara/neto):
    # guessing here is how totals get corrupted, so refuse.
    if len(values) == 1:
        return values.pop()
    return None


def _find_patente(text: str) -> str | None:
    labeled = _PATENTE_LABEL_RE.search(text)
    if labeled:
        return labeled.group(1).replace(" ", "").upper()
    loose = _PATENTE_LOOSE_RE.search(text)
    return loose.group(1) if loose else None


def _find_fecha(text: str) -> str | None:
    iso = _FECHA_ISO_RE.search(text)
    if iso:
        return iso.group(0)
    dmy = _FECHA_DMY_RE.search(text)
    if not dmy:
        return None
    day, month, year = (int(part) for part in dmy.groups())
    if year < 100:
        year += 2000
    if month > 12 and day <= 12:
        day, month = month, day
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _find_labeled(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = " ".join(match.group(1).split()).strip("-: ")
    return value or None


def _find_producto(text: str) -> str | None:
    labeled = _find_labeled(_PRODUCTO_RE, text)
    if labeled:
        return labeled
    crop = _CROP_RE.search(text)
    return crop.group(1) if crop else None


def _parse_ticket_text(raw_ocr: str) -> dict:
    humedad_match = _HUMEDAD_RE.search(raw_ocr)
    return {
        "fecha": _find_fecha(raw_ocr),
        "patente": _find_patente(raw_ocr),
        "tonelaje_kg": _find_kg(raw_ocr),
        "origen": _find_labeled(_ORIGEN_RE, raw_ocr),
        "destino": _find_labeled(_DESTINO_RE, raw_ocr),
        "producto": _find_producto(raw_ocr),
        "humedad": _parse_localized_number(humedad_match.group(1))
        if humedad_match
        else None,
    }


def extract_remito(raw_ocr: str) -> ExtractResult:
    """Parse typed fields from raw_ocr. No disk or database access.

    JSON input is trusted as-is; anything else goes through the
    deterministic ticket-text parser.
    """
    parsed: dict = {}
    text = raw_ocr.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            parsed = data
    if not parsed:
        parsed = _parse_ticket_text(raw_ocr)
    return ExtractResult(
        fecha=_as_str(parsed.get("fecha")),
        patente=_as_str(parsed.get("patente")),
        tonelaje_kg=_as_float(parsed.get("tonelaje_kg")),
        origen=_as_str(parsed.get("origen")),
        destino=_as_str(parsed.get("destino")),
        producto=_as_str(parsed.get("producto")),
        humedad=_as_float(parsed.get("humedad")),
        raw_ocr=raw_ocr,
        confidence=_as_float(parsed.get("confidence")),
    )


def find_duplicate_remitos(
    conn: sqlite3.Connection, payload: RemitoSave
) -> list[RemitoOut]:
    """Rows matching fecha + patente + tonelaje_kg (NULL-safe on fecha/patente)."""
    rows = conn.execute(
        """
        SELECT * FROM remitos
        WHERE tonelaje_kg = ? AND fecha IS ? AND patente IS ?
        ORDER BY id DESC
        """,
        (payload.tonelaje_kg, payload.fecha, payload.patente),
    ).fetchall()
    return [RemitoOut.model_validate(dict(row)) for row in rows]


def save_remito(
    conn: sqlite3.Connection,
    payload: RemitoIn,
    *,
    allow_duplicate: bool = False,
) -> RemitoOut:
    """Validate types/kg>0 and INSERT one remito row.

    Without `allow_duplicate`, an existing row with the same fecha + patente +
    kg raises DuplicateRemitoError so double-scanning a ticket cannot silently
    inflate the day total.
    """
    try:
        saved = RemitoSave.model_validate(payload.model_dump())
    except ValidationError as exc:
        raise RemitoValidationError(
            "tonelaje_kg must be a number greater than 0",
            raw_ocr=payload.raw_ocr,
        ) from exc
    if not allow_duplicate:
        duplicates = find_duplicate_remitos(conn, saved)
        if duplicates:
            raise DuplicateRemitoError(
                "identical remito already saved (same fecha, patente, kg)",
                duplicates,
            )
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO remitos (
          created_at, fecha, patente, tonelaje_kg, origen, destino,
          producto, humedad, raw_ocr, image_path, confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            saved.fecha,
            saved.patente,
            saved.tonelaje_kg,
            saved.origen,
            saved.destino,
            saved.producto,
            saved.humedad,
            saved.raw_ocr,
            saved.image_path,
            saved.confidence,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM remitos WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return RemitoOut.model_validate(dict(row))


def get_remito(conn: sqlite3.Connection, remito_id: int) -> RemitoOut:
    row = conn.execute(
        "SELECT * FROM remitos WHERE id = ?", (remito_id,)
    ).fetchone()
    if row is None:
        raise RemitoNotFoundError(f"remito {remito_id} not found")
    return RemitoOut.model_validate(dict(row))


UPDATABLE_FIELDS = (
    "fecha",
    "patente",
    "tonelaje_kg",
    "origen",
    "destino",
    "producto",
    "humedad",
)


def update_remito(
    conn: sqlite3.Connection,
    remito_id: int,
    payload: RemitoIn,
    provided: set[str] | frozenset[str] | None = None,
) -> RemitoOut:
    """Update confirmed fields, merging over the existing row.

    `provided` names the fields the caller actually sent: absent fields keep
    their stored value, while a provided-but-empty field clears it. Without
    `provided` the full payload replaces every updatable field (a complete
    RemitoIn means the caller stated every value). raw_ocr from the existing
    row is never overwritten.
    """
    existing = get_remito(conn, remito_id)
    incoming = payload.model_dump()
    keys = set(UPDATABLE_FIELDS) if provided is None else set(provided)
    data = existing.model_dump()
    for field_name in UPDATABLE_FIELDS:
        if field_name in keys:
            data[field_name] = incoming[field_name]
    data["raw_ocr"] = existing.raw_ocr
    if incoming.get("image_path"):
        data["image_path"] = incoming["image_path"]
    if incoming.get("confidence") is not None:
        data["confidence"] = incoming["confidence"]
    try:
        saved = RemitoSave.model_validate(data)
    except ValidationError as exc:
        raise RemitoValidationError(
            "tonelaje_kg must be a number greater than 0",
            raw_ocr=existing.raw_ocr,
        ) from exc
    conn.execute(
        """
        UPDATE remitos SET
          fecha = ?, patente = ?, tonelaje_kg = ?, origen = ?, destino = ?,
          producto = ?, humedad = ?, image_path = ?, confidence = ?
        WHERE id = ?
        """,
        (
            saved.fecha,
            saved.patente,
            saved.tonelaje_kg,
            saved.origen,
            saved.destino,
            saved.producto,
            saved.humedad,
            saved.image_path,
            saved.confidence,
            remito_id,
        ),
    )
    conn.commit()
    return get_remito(conn, remito_id)


def list_remitos(
    conn: sqlite3.Connection,
    fecha: str | None = None,
    producto: str | None = None,
) -> list[RemitoOut]:
    rows = conn.execute(
        """
        SELECT * FROM remitos
        WHERE (? IS NULL OR fecha = ?)
          AND (? IS NULL OR producto = ?)
        ORDER BY id DESC
        """,
        (fecha, fecha, producto, producto),
    ).fetchall()
    return [RemitoOut.model_validate(dict(row)) for row in rows]


def summarize_harvest(
    conn: sqlite3.Connection,
    fecha: str | None = None,
) -> HarvestSummary:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(tonelaje_kg), 0), COUNT(*)
        FROM remitos
        WHERE (? IS NULL OR fecha = ?)
        """,
        (fecha, fecha),
    ).fetchone()
    return HarvestSummary(total_kg=float(row[0]), count=int(row[1]), fecha=fecha)


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def llm_tools(
    conn: sqlite3.Connection,
    *,
    image_path: str | None,
    default_raw_ocr: str,
    confidence: float | None,
) -> list[dict]:
    """Tool defs for QVAC completion. extract_remito has no IO; save_remito INSERTs."""

    async def extract_handler(args: dict) -> dict:
        raw = str(args.get("raw_ocr") or default_raw_ocr or "")
        result = extract_remito(raw).model_dump()
        # Deterministic parse wins; model args only fill fields the ticket
        # text did not yield. The kg that gets persisted never depends on
        # the LLM when a regex could read it off the ticket.
        for key in (
            "fecha",
            "patente",
            "tonelaje_kg",
            "origen",
            "destino",
            "producto",
            "humedad",
            "confidence",
        ):
            if result.get(key) is None and args.get(key) not in (None, ""):
                if key in {"tonelaje_kg", "humedad", "confidence"}:
                    result[key] = _as_float(args.get(key))
                else:
                    result[key] = _as_str(args.get(key))
        result["raw_ocr"] = raw
        if result.get("confidence") is None:
            result["confidence"] = confidence
        return result

    async def save_handler(args: dict) -> dict:
        payload = RemitoIn(
            fecha=_as_str(args.get("fecha")),
            patente=_as_str(args.get("patente")),
            tonelaje_kg=_as_float(args.get("tonelaje_kg")),
            origen=_as_str(args.get("origen")),
            destino=_as_str(args.get("destino")),
            producto=_as_str(args.get("producto")),
            humedad=_as_float(args.get("humedad")),
            raw_ocr=_as_str(args.get("raw_ocr")) or default_raw_ocr,
            image_path=_as_str(args.get("image_path")) or image_path,
            confidence=_as_float(args.get("confidence"))
            if args.get("confidence") not in (None, "")
            else confidence,
        )
        return save_remito(conn, payload).model_dump()

    return [
        {
            "name": "extract_remito",
            "description": (
                "Parse typed remito fields from OCR text. Does not persist. "
                "Call this before save_remito."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_ocr": {"type": "string"},
                    "fecha": {"type": "string"},
                    "patente": {"type": "string"},
                    "tonelaje_kg": {"type": "number"},
                    "origen": {"type": "string"},
                    "destino": {"type": "string"},
                    "producto": {"type": "string"},
                    "humedad": {"type": "number"},
                    "confidence": {"type": "number"},
                },
                "required": ["raw_ocr"],
            },
            "handler": extract_handler,
        },
        {
            "name": "save_remito",
            "description": (
                "Validate types and INSERT one remito. Call only after "
                "extract_remito with tonelaje_kg > 0."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha": {"type": "string"},
                    "patente": {"type": "string"},
                    "tonelaje_kg": {"type": "number"},
                    "origen": {"type": "string"},
                    "destino": {"type": "string"},
                    "producto": {"type": "string"},
                    "humedad": {"type": "number"},
                    "raw_ocr": {"type": "string"},
                    "image_path": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["tonelaje_kg"],
            },
            "handler": save_handler,
        },
    ]


def _as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
