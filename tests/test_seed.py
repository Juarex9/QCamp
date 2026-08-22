"""Demo seed rows."""

from __future__ import annotations

from pathlib import Path

from app.db import connect, init_schema
from app.seed import seed_if_empty


def test_seed_if_empty_inserts_three_rows(tmp_path: Path) -> None:
    conn = connect(tmp_path / "remitos.db")
    init_schema(conn)
    try:
        assert seed_if_empty(conn) == 3
        assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 3
        assert seed_if_empty(conn) == 0
    finally:
        conn.close()
