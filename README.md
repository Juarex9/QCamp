# Qcamp

Agente local para remitos / tickets de balanza (NOA). Foto → OCR+LLM en
localhost → JSON tipado → fila → totales. Cero cloud LLM. Bind solo
`127.0.0.1`. **MVP en notebook/PC** (app móvil fuera de alcance por ahora).

## Demo en 3 minutos

Happy path del jurado: **upload → fila → `/resumen`**, sin internet
(después del setup).

| Min | Qué | Cómo |
|-----|-----|------|
| 0:00 | Arrancar | `make demo` |
| 0:20 | Abrir UI | http://127.0.0.1:8000 (landing) → **Abrir la app** = `/app` |
| 0:40 | Subir ticket | `fixtures/tickets/remito-soja-tucuman.png` |
| 1:30 | Confirmar | Revisar campos (o editar) y **Confirmar** / **Guardar remito** |
| 2:00 | Ver fila | La tabla lista patente, kg, producto |
| 2:30 | Totales | http://127.0.0.1:8000/resumen — `SUM(tonelaje_kg)` |

```bash
make demo
# equivalente: bash scripts/demo.sh
# uvicorn queda en 127.0.0.1:8000 (nunca 0.0.0.0)
```

Banner en la UI: `ocr_ready` / `llm_ready`. Si ambos son `false`, el
formulario manual sigue andando (degradado).

Rutas: `/` es la landing (pitch, sin estado) y `/app` es la herramienta
(captura, tabla, totales). Todo el CSS es local: no hay webfonts ni CDN,
así que la landing también carga en modo avión.

## Airplane mode

La demo **debe** completar ingest + query con el host sin red. La red
solo se usa **una vez** para instalar.

| Momento | Red | Qué hacer |
|---------|-----|-----------|
| Setup (una vez) | ON | venv + deps + `install-worker` (modelos quedan en disco) |
| Demo jurado | OFF | `make demo` → upload fixture → fila → `/resumen` |
| Sin worker | OFF | `REMITO_QVAC=0 make demo` → mismo upload o form + seed |

Comprobar que no hay cloud: el proceso escucha `127.0.0.1`; no hay
llamadas a APIs de LLM. Tools: `extract_remito` (sin IO) y
`save_remito` (INSERT) son **dos** tools.

Atajo sin foto: `python scripts/seed_demo.py` carga los 3 tickets
sintéticos y `/resumen` ya muestra 58500 kg.

## Instalar (primera vez, con red)

Requisitos: Python ≥ 3.11, Node ≥ 22.17 (solo para el worker QVAC).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m tetherto.qvac_sdk install-worker
```

`install-worker` hace `npm install @qvac/sdk` en
`~/.cache/qvac/worker/<version>` (acá: **0.17.1**, ya instalado). El
primer `REMITO_QVAC=1` todavía baja los pesos de `OCR_LATIN` +
`LLAMA_3_2_1B_INST_Q4_0` (eso sí puede ser grande). Si no hay red o
falla el boot de modelos, seguir con `REMITO_QVAC=0` — UI y SQLite
andan igual.

## Variables

| Variable | Default | Efecto |
|----------|---------|--------|
| `REMITO_QVAC=1` | (fuera de pytest: intenta worker) | OCR + LLM locales |
| `REMITO_QVAC=0` | tests lo fuerzan | Formulario / seed; `ocr_ready=false` |
| `REMITO_DB_PATH` | `data/remitos.db` | SQLite local (gitignored) |
| `REMITO_IMAGES_DIR` | `data/images/` | Fotos subidas (gitignored) |

## Tickets sintéticos

Tres PNGs en `fixtures/tickets/`. **No son remitos reales.**

| Archivo | Producto | kg | Patente |
|---------|----------|----|---------|
| `remito-soja-tucuman.png` | soja | 18500 | AB123CD |
| `remito-maiz-salta.png` | maíz | 24200 | AC456DE |
| `remito-trigo-santiago.png` | trigo | 15800 | AD789FG |

Regenerar: `python scripts/gen_synthetic_tickets.py`.

Brief oficial del track (premios): [docs/track.md](docs/track.md).  
Hoja de pulido (cómo lo cubre Qcamp): [docs/qvac-track.md](docs/qvac-track.md).  
Por qué `OCR_LATIN` + Llama 3.2 1B Q4: [docs/modelos.md](docs/modelos.md).  
Pitch (usuario = productor, **dispositivo = notebook/PC**): [docs/pitch.md](docs/pitch.md).  
Deploy presentación (**Render** backend + **Vercel** landing): [docs/deploy.md](docs/deploy.md).

## DoraHacks / Aleph

| Criterio | Cómo se ve en esta demo |
|----------|-------------------------|
| Greenfield | Código escrito de cero. No hay copia de Zafra ni VitisTrust. |
| Inferencia local | Worker QVAC en este host. `OCR_LATIN` + `LLAMA_3_2_1B_INST_Q4_0`. |
| Tool use | LLM llama `extract_remito` y, aparte, `save_remito`. JSON tipado. |
| Offline | Airplane mode: upload → fila → totales sin cloud. |
| Localhost | FastAPI **solo** `127.0.0.1`. |

El envío a DoraHacks lo hace una persona (riesgo Alto). Este repo no
automatiza submit.

## Tests

```bash
.venv/bin/pytest
.venv/bin/ruff check .
```

Pytest nunca arranca el worker (`REMITO_QVAC=0` en `tests/conftest.py`).
