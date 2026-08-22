"""Schema bootstrap and GET /health (slice 0)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import bind_host
from app.db import connect, init_schema
from app.main import app

EXPECTED_COLUMNS = {
    "id",
    "created_at",
    "fecha",
    "patente",
    "tonelaje_kg",
    "origen",
    "destino",
    "producto",
    "humedad",
    "raw_ocr",
    "image_path",
    "confidence",
}


def test_schema_creates_remitos_table_and_indexes(tmp_path: Path) -> None:
    conn = connect(tmp_path / "remitos.db")
    try:
        init_schema(conn)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "remitos" in tables

        columns = {row[1] for row in conn.execute("PRAGMA table_info(remitos)")}
        assert EXPECTED_COLUMNS <= columns

        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
        }
        assert "idx_remitos_fecha" in indexes
        assert "idx_remitos_producto" in indexes

        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert journal.lower() == "wal"
    finally:
        conn.close()


def test_schema_is_idempotent(tmp_path: Path) -> None:
    conn = connect(tmp_path / "remitos.db")
    try:
        init_schema(conn)
        init_schema(conn)
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='remitos'"
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_health_returns_200_without_qvac(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["ocr_ready"] is False
    assert body["llm_ready"] is False
    assert body["db"] == "ok"


def test_bind_host_is_localhost_by_default() -> None:
    assert bind_host() == "127.0.0.1"
