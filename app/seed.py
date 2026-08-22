"""Demo seed rows (synthetic tickets). Shared by CLI and cloud startup."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models import RemitoIn
from app.tools import save_remito

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "tickets"

SEED_ROWS: tuple[dict, ...] = (
    {
        "fecha": "2026-08-20",
        "patente": "AB123CD",
        "tonelaje_kg": 18500,
        "origen": "Tucumán",
        "destino": "Rosario",
        "producto": "soja",
        "humedad": 13.5,
        "raw_ocr": "SINTETICO remito soja TUCUMAN 18500 KG AB123CD",
        "image_path": str(FIXTURES / "remito-soja-tucuman.png"),
        "confidence": 1.0,
    },
    {
        "fecha": "2026-08-21",
        "patente": "AC456DE",
        "tonelaje_kg": 24200,
        "origen": "Salta",
        "destino": "Timbúes",
        "producto": "maíz",
        "humedad": 14.2,
        "raw_ocr": "SINTETICO remito maiz SALTA 24200 KG AC456DE",
        "image_path": str(FIXTURES / "remito-maiz-salta.png"),
        "confidence": 1.0,
    },
    {
        "fecha": "2026-08-22",
        "patente": "AD789FG",
        "tonelaje_kg": 15800,
        "origen": "Santiago del Estero",
        "destino": "San Lorenzo",
        "producto": "trigo",
        "humedad": 12.8,
        "raw_ocr": "SINTETICO remito trigo SANTIAGO 15800 KG AD789FG",
        "image_path": str(FIXTURES / "remito-trigo-santiago.png"),
        "confidence": 1.0,
    },
)


def seed_if_empty(conn: sqlite3.Connection) -> int:
    """Insert demo remitos when the table is empty. Returns rows inserted."""
    count = conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0]
    if count:
        return 0
    inserted = 0
    for row in SEED_ROWS:
        save_remito(conn, RemitoIn.model_validate(row))
        inserted += 1
    return inserted
