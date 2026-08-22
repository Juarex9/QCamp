"""Optional seed: insert the three synthetic tickets into SQLite.

Use when you want list + /resumen populated without uploading photos.
Does not start QVAC. Default DB: data/remitos.db.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.db import connect, init_schema
from app.seed import seed_if_empty

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    db = Path(os.environ.get("REMITO_DB_PATH", ROOT / "data" / "remitos.db"))
    conn = connect(db)
    try:
        init_schema(conn)
        inserted = seed_if_empty(conn)
        print(f"seeded {inserted} row(s); db={db}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
