#!/usr/bin/env bash
# Arranca Qcamp en 127.0.0.1:8000 (demo jurado, 3 min).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "Qcamp → http://127.0.0.1:8000"
echo "Happy path: subir fixtures/tickets/remito-soja-tucuman.png → confirmar fila → /resumen"
echo "REMITO_QVAC=${REMITO_QVAC:-unset}  (1=worker local, 0=formulario manual)"
exec "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
