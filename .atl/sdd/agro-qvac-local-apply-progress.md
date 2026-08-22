# Apply progress: agro-qvac-local

**Change**: agro-qvac-local
**Mode**: Standard (`strict_tdd: false`)
**Batch**: 5 (MERGE with batch 1 / slice 0 + batch 2 / slice 1 + batch 3 / slice 2 + batch 4 / slice 3)
**Delivery**: auto-chain / stacked-to-main
**Work unit**: Slice 4 — demo README, synthetic fixtures, airplane-mode notes

## Completed Tasks

### Slice 0 (batch 1 — preserved)

- [x] 1.1 `pyproject.toml`: Py≥3.11, fastapi, uvicorn, jinja2, python-multipart, pytest, httpx, ruff, tetherto-qvac-sdk
- [x] 1.2 `.gitignore`: `.venv/`, `data/`, `__pycache__/`
- [x] 1.3 `app/schema.sql` + `app/db.py`: WAL, `remitos` + indexes (`IF NOT EXISTS`)
- [x] 1.4 `app/main.py`: bind `127.0.0.1`, lifespan DB, `GET /health` → `{ok,ocr_ready,llm_ready,db}`
- [x] 1.5 Tests: `tests/test_schema.py` crea tabla; `/health` 200. Verify: `pytest` + `ruff check`

### Slice 1 (batch 2 — preserved)

- [x] 2.1 `app/models.py` + `app/tools.py`: `extract_remito` (no IO), `save_remito` (kg>0), `list_remitos`, `summarize_harvest`
- [x] 2.2 `POST /remitos` campos o foto (guarda `data/images/{uuid}`); `GET /remitos`
- [x] 2.3 Degradado: sin QVAC → form + `save_remito`; 422 si kg inválido (spec reject)
- [x] 2.4 Tests: `tests/test_tools.py` + `tests/test_routes.py` TestClient, sin worker

### Slice 2 (batch 3 — preserved)

- [x] 3.1 `app/qvac_client.py` fachada JS: `ocr(path)`, `complete(history,tools)`, `startup/shutdown`
- [x] 3.2 Load: `OCR_LATIN` + `LLAMA_3_2_1B_INST_Q4_0` via `load_model(t, model_src=…)`; fail → flags false (independientes)
- [x] 3.3 OCR: `ocr_stream` + `OcrStreamRequest` image `{type:filePath,value}`; concat `text`/`confidence`
- [x] 3.4 LLM: `completion` tools+handlers; leer `run.events`/`run.final`; `toolCall.invoke()`; extract≠save
- [x] 3.5 Wire `POST /remitos` foto → ocr → complete; mock runtime en tests; spike 1 foto fixture (placeholder; live worker skipped)

### Slice 3 (batch 4 — preserved)

- [x] 4.1 Templates HTMX: upload, form, row, list, banner, resumen (`HX-Request`)
- [x] 4.2 `POST /remitos/{id}` edit conserva `raw_ocr`; `GET /resumen` = `SUM(tonelaje_kg)`
- [x] 4.3 Tests partials + scenario confirm/edit

### Slice 4 (batch 5 — this apply)

- [x] 5.1 `fixtures/tickets/` 3 fotos sintéticas + seed opcional
- [x] 5.2 README: `install-worker`, uvicorn, airplane mode, 3 min (upload→fila→totales)
- [x] 5.3 Banner existente; `scripts/demo.sh` + `make demo` (uvicorn 127.0.0.1:8000)

## Remaining Tasks

None. All 20 tasks (5+4+5+3+3) complete.

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `README.md` | Created (s4) | 3-min happy path first; airplane; REMITO_QVAC; DoraHacks |
| `Makefile` | Created (s4) | `demo` → `scripts/demo.sh` |
| `scripts/demo.sh` | Created (s4) | uvicorn `--host 127.0.0.1 --port 8000` |
| `scripts/gen_synthetic_tickets.py` | Created (s4) | stdlib PNG remitos (labeled SINTETICO) |
| `scripts/seed_demo.py` | Created (s4) | optional 3-row seed (58500 kg) |
| `fixtures/tickets/README.md` | Created (s4) | synthetic label + table |
| `fixtures/tickets/remito-soja-tucuman.png` | Created (s4) | synthetic ticket 18500 kg soja |
| `fixtures/tickets/remito-maiz-salta.png` | Created (s4) | synthetic ticket 24200 kg maíz |
| `fixtures/tickets/remito-trigo-santiago.png` | Created (s4) | synthetic ticket 15800 kg trigo |
| `fixtures/tickets/spike-placeholder.png` | Preserved (s2) | 1×1 PNG from slice 2 |
| `tests/test_demo_fixtures.py` | Created (s4) | 3 PNGs + README + launcher + seed |
| `pyproject.toml` | Modified (s3) | package-data for templates + static |
| `.gitignore` | Created (s0) | `.venv/`, `data/`, `__pycache__/`, caches |
| `app/__init__.py` | Created (s0) | Package marker |
| `app/schema.sql` | Created (s0) | `remitos` + indexes, `IF NOT EXISTS` |
| `app/db.py` | Created (s0) | connect WAL + `row_factory`; `init_schema`; `check_same_thread=False` |
| `app/main.py` | Modified (s3) | Jinja2 + HX-Request; GET /resumen; POST /remitos/{id} |
| `app/models.py` | Created (s1) | Pydantic fields; `RemitoSave.tonelaje_kg > 0` |
| `app/tools.py` | Modified (s3) | `get_remito` + `update_remito` (never overwrites `raw_ocr`) |
| `app/qvac_client.py` | Created (s2) | JS-like `QvacRuntime`; Python SDK mapping |
| `app/templates/*` | Created (s3) | base/index + partials banner/form/list/row/resumen |
| `app/static/*` | Created (s3) | app.css + local htmx.js |
| `tests/conftest.py` | Modified (s2) | `REMITO_QVAC=0` autouse; `FakeQvacRuntime` |
| `tests/test_schema.py` | Created (s0) | schema/indexes/WAL + health 200 + bind host |
| `tests/test_tools.py` | Modified (s3) | `update_remito` preserves raw_ocr |
| `tests/test_routes.py` | Modified (s2) | photo+mock extract; degradado intacto |
| `tests/test_qvac.py` | Created (s2) | mock Client/ocr_stream/completion |
| `tests/test_ui.py` | Created (s3) | partials HX-Request + confirm/edit + GET /resumen |

Recovery: `.atl/sdd/agro-qvac-local-apply-progress.md`

## Verification

- `pytest`: 38 passed
- `ruff check .`: All checks passed
- `pre_commit_status`: NOT CONFIGURED
- `python -m tetherto.qvac_sdk install-worker`: **ok** — `@qvac/sdk@0.17.1` in `~/.cache/qvac/worker/0.17.1` (~3 min npm)
- Model weights (`OCR_LATIN` + Llama 3.2 1B Q4) **not** downloaded this slice
- Slice 4 tests: PNG magic + README keywords + demo bind + seed SUM=58500

## Deviations from Design

- `sqlite3.connect(..., check_same_thread=False)` — from slice 0; kept.
- Live OCR+LLM spike skipped (slice 2): wrapper + mocks + placeholder fixture. Unchanged. Worker npm is now installed; first live boot still needs model download.
- `REMITO_QVAC=0` in pytest autouse. Unchanged.
- Local `app/static/htmx.js` instead of CDN HTMX (airplane mode).
- `TemplateResponse(request, name, context)` — Starlette request-first API.
- Tickets are **synthetic PNGs** (stdlib bitmap font), not photos of real scale tickets. Labeled SINTETICO on-image and in `fixtures/tickets/README.md`.
- `make demo` + `scripts/demo.sh` added (task 5.3); banner already existed from slice 3.

## Issues Found

- Host Python is 3.14.4. Using existing `.venv/`.
- Starlette warns TestClient+httpx is deprecated in favor of `httpx2`. Kept `httpx`.
- Bitmap font is coarse (slash/colon glyphs look 8-bit). Good enough for a labeled synthetic remito.
- First `REMITO_QVAC=1` boot will still download model weights (not done here; can be large).

## Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main)
- Current work unit: Slice 4 demo docs + fixtures
- Boundary: starts after slice 3 UI; ends at README + 3 synthetic tickets + `make demo` + optional seed
- Estimated review budget impact: ~200–280 lines (under 400)
- Next: `sdd-verify` **full** (all slices). Then **pause** — DoraHacks submit is Alto (humano). Do **not** archive.

## Status

20/20 tasks complete (5 + 4 + 5 + 3 + 3). Ready for `sdd-verify` full. After verify: pause (DoraHacks = Alto). Do not archive.

**What**: Slice 4 demo docs/fixtures implemented and merged with slices 0–3.
**Why**: auto-chain apply batch 5 — 3-min airplane README, synthetic tickets, `make demo`.
**Where**: README.md, Makefile, scripts/*, fixtures/tickets/*, tests/test_demo_fixtures.py
**Learned**: install-worker is npm `@qvac/sdk` into `~/.cache/qvac/worker/<ver>`; model download is a later boot step. DoraHacks submit stays human/Alto.
