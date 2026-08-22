"""FastAPI entrypoint. Local bind 127.0.0.1; cloud via REMITO_HOST / PORT."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import UndefinedError
from starlette.datastructures import UploadFile

from app.config import (
    bind_host,
    bind_port,
    cors_origins,
    public_banner_label,
    seed_demo_on_empty,
)
from app.db import connect, init_schema
from app.models import RemitoIn, RemitoOut
from app.qvac_client import QvacRuntime
from app.seed import seed_if_empty
from app.tools import (
    DuplicateRemitoError,
    RemitoNotFoundError,
    RemitoValidationError,
    extract_remito,
    list_remitos,
    llm_tools,
    save_remito,
    summarize_harvest,
    update_remito,
)

logger = logging.getLogger("qcamp.web")

# Default for tests and `from app.main import BIND_HOST`.
BIND_HOST = bind_host()
APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _fmt_kg(value: object) -> str:
    """Drop the trailing .0 so whole kilos read as scale weights, not floats.

    Blank, missing, and undefined values all render as an empty field.
    """
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, UndefinedError):
        return ""
    if number == int(number):
        return str(int(number))
    return f"{number:g}"


templates.env.filters["kg"] = _fmt_kg
FORM_FIELDS = (
    "fecha",
    "patente",
    "tonelaje_kg",
    "origen",
    "destino",
    "producto",
    "humedad",
    "raw_ocr",
    "confidence",
)


def db_path() -> Path:
    return Path(os.environ.get("REMITO_DB_PATH", "data/remitos.db"))


def images_dir() -> Path:
    env = os.environ.get("REMITO_IMAGES_DIR")
    if env:
        return Path(env)
    return db_path().parent / "images"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # No-op if the host (uvicorn, pytest) already configured logging.
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    conn = connect(db_path())
    init_schema(conn)
    dest = images_dir()
    dest.mkdir(parents=True, exist_ok=True)
    runtime = QvacRuntime()
    await runtime.startup()
    if seed_demo_on_empty():
        inserted = seed_if_empty(conn)
        if inserted:
            logger.info("seeded %s demo remito(s) (REMITO_SEED_DEMO)", inserted)
    app.state.db = conn
    app.state.images_dir = dest
    app.state.qvac = runtime
    app.state.ocr_ready = runtime.ocr_ready
    app.state.llm_ready = runtime.llm_ready
    logger.info(
        "startup db=%s images=%s ocr_ready=%s llm_ready=%s",
        db_path(),
        dest,
        runtime.ocr_ready,
        runtime.llm_ready,
    )
    try:
        yield
    finally:
        await runtime.shutdown()
        conn.close()


app = FastAPI(title="Qcamp", lifespan=lifespan)

_origins = cors_origins()
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _flags() -> dict:
    return {
        "ocr_ready": bool(getattr(app.state, "ocr_ready", False)),
        "llm_ready": bool(getattr(app.state, "llm_ready", False)),
    }


def _page_ctx(
    form: dict | None = None,
    error: str | None = None,
    image_path: str | None = None,
    remito: RemitoOut | None = None,
    remitos: list[RemitoOut] | None = None,
    resumen=None,
    fecha: str | None = None,
    duplicates: list[RemitoOut] | None = None,
) -> dict:
    values = form or {}
    return {
        **_flags(),
        "form": values,
        "error": error,
        "image_path": image_path or values.get("image_path"),
        "remito": remito,
        "duplicates": duplicates,
        "banner_host": public_banner_label(),
        "remitos": remitos
        if remitos is not None
        else list_remitos(app.state.db),
        "resumen": resumen
        if resumen is not None
        else summarize_harvest(app.state.db, fecha=fecha),
    }


def _is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request", "").lower() == "true"


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept


def _template(
    request: Request, name: str, context: dict, status: int = 200
):
    return templates.TemplateResponse(
        request, name, context, status_code=status
    )


def _respond_form(
    request: Request,
    json_body: dict,
    *,
    form: dict | None = None,
    error: str | None = None,
    image_path: str | None = None,
    status: int = 200,
    duplicates: list[RemitoOut] | None = None,
):
    ctx = _page_ctx(
        form=form, error=error, image_path=image_path, duplicates=duplicates
    )
    if _is_htmx(request):
        return _template(request, "partials/form.html", ctx, status)
    if _wants_html(request):
        return _template(request, "app.html", ctx, status)
    if status != 200:
        return JSONResponse(json_body, status_code=status)
    return json_body


def _respond_duplicate(
    request: Request,
    exc: DuplicateRemitoError,
    form: dict | None,
    image_path: str | None,
):
    """409: same fecha+patente+kg already saved. Confirm or discard."""
    first = exc.duplicates[0]
    return _respond_form(
        request,
        {
            "detail": "duplicate_remito",
            "duplicates": [dup.model_dump() for dup in exc.duplicates],
            "hint": "re-send with confirm_duplicate=1 to save anyway",
        },
        form=form,
        image_path=image_path,
        status=409,
        duplicates=exc.duplicates,
        error=(
            f"Ya cargaste un remito idéntico (#{first.id}: "
            f"{first.patente or 'sin patente'}, {_fmt_kg(first.tonelaje_kg)} kg)."
        ),
    )


def _respond_saved(
    request: Request,
    remito: RemitoOut,
    extra: dict | None = None,
    *,
    insert_row: bool = True,
):
    payload = {"remito": remito.model_dump(), **(extra or {})}
    ctx = _page_ctx(remito=remito)
    if _is_htmx(request):
        response = _template(request, "partials/row.html", ctx)
        response.headers["HX-Trigger"] = "remitoSaved"
        if insert_row:
            response.headers["HX-Retarget"] = "#remitos-table-body"
            response.headers["HX-Reswap"] = "afterbegin"
        return response
    if _wants_html(request):
        return _template(request, "app.html", ctx)
    return payload


def _blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _parse_kg(value: object) -> float | None:
    if _blank(value):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise RemitoValidationError(
            "tonelaje_kg must be a number greater than 0"
        ) from exc


def _parse_optional_float(value: object) -> float | None:
    if _blank(value):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _parse_humedad(value: object) -> float | None:
    """User-typed humidity: reject garbage instead of silently dropping it.

    Accepts the Argentine comma decimal ("13,4").
    """
    if _blank(value):
        return None
    text = str(value).strip()
    if text.count(",") == 1 and "." not in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except (TypeError, ValueError) as exc:
        raise RemitoValidationError("humedad must be a number") from exc


def _payload_from_fields(fields: dict, image_path: str | None) -> RemitoIn:
    return RemitoIn(
        fecha=None if _blank(fields.get("fecha")) else str(fields.get("fecha")),
        patente=None if _blank(fields.get("patente")) else str(fields.get("patente")),
        tonelaje_kg=_parse_kg(fields.get("tonelaje_kg")),
        origen=None if _blank(fields.get("origen")) else str(fields.get("origen")),
        destino=None if _blank(fields.get("destino")) else str(fields.get("destino")),
        producto=None
        if _blank(fields.get("producto"))
        else str(fields.get("producto")),
        humedad=_parse_humedad(fields.get("humedad")),
        raw_ocr=None if _blank(fields.get("raw_ocr")) else str(fields.get("raw_ocr")),
        image_path=image_path
        or (
            None
            if _blank(fields.get("image_path"))
            else str(fields.get("image_path"))
        ),
        confidence=_parse_optional_float(fields.get("confidence")),
    )


def _has_save_fields(fields: dict) -> bool:
    keys = (
        "fecha",
        "patente",
        "tonelaje_kg",
        "origen",
        "destino",
        "producto",
        "humedad",
    )
    return any(not _blank(fields.get(key)) for key in keys)


def _reject(
    request: Request,
    exc: RemitoValidationError,
    fields: dict,
    image_path: str | None,
):
    raw = exc.raw_ocr or str(fields.get("raw_ocr") or "")
    return _respond_form(
        request,
        {"detail": str(exc), "raw_ocr": raw, "form": True, "image_path": image_path},
        form=fields,
        error=str(exc),
        image_path=image_path,
        status=422,
    )


async def _read_fields(
    request: Request,
) -> tuple[dict, UploadFile | None, frozenset[str]]:
    """Return (fields, photo, provided).

    `provided` is the set of field names the client actually sent, so edits
    can distinguish "absent: keep stored value" from "empty: clear it".
    """
    photo: UploadFile | None = None
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        fields = body if isinstance(body, dict) else {}
        return fields, None, frozenset(fields)
    form = await request.form()
    fields = {
        name: form.get(name)
        for name in (*FORM_FIELDS, "image_path", "confirm_duplicate")
    }
    provided = frozenset(
        name for name in (*FORM_FIELDS, "image_path") if name in form
    )
    uploaded = form.get("photo")
    if isinstance(uploaded, UploadFile) and uploaded.filename:
        photo = uploaded
    return fields, photo, provided


@app.get("/health")
def health() -> dict:
    db_status = "error"
    try:
        app.state.db.execute("SELECT 1").fetchone()
        db_status = "ok"
    except Exception:
        logger.warning("health: db check failed", exc_info=True)
        db_status = "error"
    return {
        "ok": db_status == "ok",
        "ocr_ready": bool(getattr(app.state, "ocr_ready", False)),
        "llm_ready": bool(getattr(app.state, "llm_ready", False)),
        "db": db_status,
        "host": bind_host(),
    }


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return _template(request, "landing.html", {})


@app.get("/app", response_class=HTMLResponse)
def workspace(request: Request):
    return _template(request, "app.html", _page_ctx())


@app.get("/remitos/nuevo")
def remito_nuevo(request: Request):
    """Blank capture form; target of the 'Descartar' button on a duplicate."""
    ctx = _page_ctx()
    if _is_htmx(request):
        return _template(request, "partials/form.html", ctx)
    return _template(request, "app.html", ctx)


@app.get("/remitos")
def get_remitos(
    request: Request, fecha: str | None = None, producto: str | None = None
):
    items = list_remitos(app.state.db, fecha=fecha, producto=producto)
    ctx = _page_ctx(remitos=items)
    if _is_htmx(request):
        return _template(request, "partials/list.html", ctx)
    if _wants_html(request):
        return _template(request, "app.html", ctx)
    return {"remitos": [item.model_dump() for item in items]}


@app.get("/resumen")
def get_resumen(request: Request, fecha: str | None = None):
    summary = summarize_harvest(app.state.db, fecha=fecha)
    ctx = _page_ctx(resumen=summary, fecha=fecha)
    if _is_htmx(request):
        return _template(request, "partials/resumen.html", ctx)
    if _wants_html(request):
        return _template(request, "app.html", ctx)
    return summary.model_dump()


@app.post("/remitos")
async def post_remitos(request: Request):
    fields, photo, _provided = await _read_fields(request)

    image_path = (
        None if _blank(fields.get("image_path")) else str(fields.get("image_path"))
    )
    if photo is not None:
        dest = Path(app.state.images_dir) / str(uuid.uuid4())
        dest.write_bytes(await photo.read())
        image_path = str(dest)

    raw_ocr = None if _blank(fields.get("raw_ocr")) else str(fields.get("raw_ocr"))
    confidence = _parse_optional_float(fields.get("confidence"))
    ocr_ready = bool(getattr(app.state, "ocr_ready", False))
    llm_ready = bool(getattr(app.state, "llm_ready", False))
    runtime: QvacRuntime | None = getattr(app.state, "qvac", None)

    if (
        photo is not None
        and image_path
        and runtime is not None
        and ocr_ready
        and not _has_save_fields(fields)
    ):
        try:
            ocr_result = await runtime.ocr(image_path)
            raw_ocr = ocr_result.text or raw_ocr
            if ocr_result.confidence is not None:
                confidence = ocr_result.confidence
            if llm_ready and raw_ocr:
                tools = llm_tools(
                    app.state.db,
                    image_path=image_path,
                    default_raw_ocr=raw_ocr,
                    confidence=confidence,
                )
                completed = await runtime.run_document_agent(raw_ocr, tools)
                extra = {
                    "invoked": completed.invoked,
                    "turns": completed.turns,
                    "invented": completed.invented,
                    "needs_judgment": completed.needs_judgment,
                }
                if completed.saved:
                    return _respond_saved(
                        request,
                        RemitoOut.model_validate(completed.saved),
                        extra,
                    )
                extract_body = completed.extracted
                form_values = extract_body or {"raw_ocr": raw_ocr}
                error = None
                if completed.invented:
                    error = "El modelo cambió el kg del extract. No se guardó."
                body = {
                    "degraded": False,
                    "form": True,
                    "image_path": image_path,
                    "ocr_ready": True,
                    "llm_ready": True,
                    "raw_ocr": raw_ocr,
                    "extract": extract_body,
                    **extra,
                }
                return _respond_form(
                    request,
                    body,
                    form=form_values,
                    error=error,
                    image_path=image_path,
                )
            form_values = {"raw_ocr": raw_ocr, "confidence": confidence}
            body = {
                "degraded": not llm_ready,
                "form": True,
                "image_path": image_path,
                "ocr_ready": ocr_ready,
                "llm_ready": llm_ready,
                "raw_ocr": raw_ocr,
                "extract": None,
            }
            return _respond_form(
                request, body, form=form_values, image_path=image_path
            )
        except DuplicateRemitoError as exc:
            # The agent never confirms a duplicate on its own: hand the
            # decision to the user with the deterministic extract prefilled.
            extracted = extract_remito(raw_ocr).model_dump() if raw_ocr else None
            return _respond_duplicate(
                request, exc, extracted or {"raw_ocr": raw_ocr}, image_path
            )
        except Exception:
            # The manual form still works, but leave a trace: a silent
            # fallback here means debugging a dead demo blind.
            logger.exception(
                "QVAC pipeline failed for %s; falling back to manual form",
                image_path,
            )
            ocr_ready = bool(getattr(app.state, "ocr_ready", False))
            llm_ready = bool(getattr(app.state, "llm_ready", False))

    if not _has_save_fields(fields):
        extracted = extract_remito(raw_ocr).model_dump() if raw_ocr else None
        body = {
            "degraded": True,
            "form": True,
            "image_path": image_path,
            "ocr_ready": ocr_ready,
            "llm_ready": llm_ready,
            "extract": extracted,
        }
        return _respond_form(
            request, body, form=extracted, image_path=image_path
        )

    try:
        payload = _payload_from_fields(fields, image_path)
    except RemitoValidationError as exc:
        if raw_ocr:
            exc.raw_ocr = raw_ocr
        return _reject(request, exc, fields, image_path)

    confirmed = fields.get("confirm_duplicate") not in (None, "", "0", False)
    try:
        remito = save_remito(app.state.db, payload, allow_duplicate=confirmed)
    except DuplicateRemitoError as exc:
        return _respond_duplicate(request, exc, fields, image_path)
    except RemitoValidationError as exc:
        return _reject(request, exc, fields, image_path)

    return _respond_saved(request, remito)


@app.post("/remitos/{remito_id}")
async def post_remito_edit(remito_id: int, request: Request):
    fields, _photo, provided = await _read_fields(request)
    image_path = (
        None if _blank(fields.get("image_path")) else str(fields.get("image_path"))
    )
    try:
        payload = _payload_from_fields(fields, image_path)
        remito = update_remito(
            app.state.db, remito_id, payload, provided=provided
        )
    except RemitoNotFoundError:
        if _is_htmx(request) or _wants_html(request):
            return _respond_form(
                request,
                {"detail": "remito not found"},
                error="remito not found",
                status=404,
            )
        return JSONResponse({"detail": "remito not found"}, status_code=404)
    except RemitoValidationError as exc:
        return _reject(request, exc, fields, image_path)
    return _respond_saved(request, remito, insert_row=False)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=bind_host(), port=bind_port())
