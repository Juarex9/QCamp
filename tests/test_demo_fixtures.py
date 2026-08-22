"""Slice 4: synthetic tickets, README demo notes, seed optional."""

from __future__ import annotations

import runpy
from pathlib import Path

from app.db import connect, init_schema
from app.tools import summarize_harvest

ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "fixtures" / "tickets"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

EXPECTED = (
    "remito-soja-tucuman.png",
    "remito-maiz-salta.png",
    "remito-trigo-santiago.png",
)


def test_three_synthetic_ticket_pngs_exist() -> None:
    for name in EXPECTED:
        path = TICKETS / name
        assert path.is_file(), f"missing {path}"
        data = path.read_bytes()
        assert data.startswith(PNG_MAGIC)
        assert len(data) > 1024


def test_readme_documents_three_minute_airplane_demo() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "install-worker" in readme
    assert "127.0.0.1" in readme
    assert "airplane" in readme.lower() or "Airplane" in readme
    assert "REMITO_QVAC=0" in readme
    assert "REMITO_QVAC=1" in readme
    assert "make demo" in readme
    assert "/resumen" in readme


def test_demo_launcher_binds_localhost() -> None:
    script = (ROOT / "scripts" / "demo.sh").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "--host 127.0.0.1" in script
    assert "--port 8000" in script
    assert "scripts/demo.sh" in makefile


def test_seed_demo_inserts_three_rows(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "remitos.db"
    monkeypatch.setenv("REMITO_DB_PATH", str(db))
    runpy.run_path(str(ROOT / "scripts" / "seed_demo.py"), run_name="__main__")
    conn = connect(db)
    try:
        init_schema(conn)
        summary = summarize_harvest(conn)
        assert summary.count == 3
        assert summary.total_kg == 58500
    finally:
        conn.close()
