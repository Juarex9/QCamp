#!/usr/bin/env bash
# Bake REMITO_BACKEND_URL into the static Vercel landing (public/index.html).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/public/index.template.html"
OUT="$ROOT/public/index.html"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "missing $TEMPLATE" >&2
  exit 1
fi

BACKEND="${REMITO_BACKEND_URL:-https://qcamp.onrender.com}"
BACKEND="${BACKEND%/}"

sed "s|__BACKEND_URL__|${BACKEND}|g" "$TEMPLATE" > "$OUT"
echo "wrote $OUT (backend=$BACKEND)"
