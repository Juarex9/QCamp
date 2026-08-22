# Tasks: Qcamp (agro-qvac-local)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 530–800 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Slice 0 → 1 → 2 → 3 → 4 |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 0 | Scaffold + SQLite + `/health` | PR 1 | first apply; pytest+ruff |
| 1 | Ingest/list mock (sin QVAC) | PR 2 | base = PR 1 |
| 2 | QvacRuntime JS-contrato | PR 3 | OCR_LATIN + tools |
| 3 | HTMX list/edit/resumen | PR 4 | spec query |
| 4 | Demo README + fixtures | PR 5 | 3 min jurado |

## Phase 1: Slice 0 — foundation

- [x] 1.1 `pyproject.toml`: Py≥3.11, fastapi, uvicorn, jinja2, python-multipart, pytest, httpx, ruff, tetherto-qvac-sdk
- [x] 1.2 `.gitignore`: `.venv/`, `data/`, `__pycache__/`
- [x] 1.3 `app/schema.sql` + `app/db.py`: WAL, `remitos` + indexes (`IF NOT EXISTS`)
- [x] 1.4 `app/main.py`: bind `127.0.0.1`, lifespan DB, `GET /health` → `{ok,ocr_ready,llm_ready,db}`
- [x] 1.5 Tests: `tests/test_schema.py` crea tabla; `/health` 200. Verify: `pytest` + `ruff check`

## Phase 2: Slice 1 — ingest mock

- [x] 2.1 `app/models.py` + `app/tools.py`: `extract_remito` (no IO), `save_remito` (kg>0), `list_remitos`, `summarize_harvest`
- [x] 2.2 `POST /remitos` campos o foto (guarda `data/images/{uuid}`); `GET /remitos`
- [x] 2.3 Degradado: sin QVAC → form + `save_remito`; 422 si kg inválido (spec reject)
- [x] 2.4 Tests: `tests/test_tools.py` + `tests/test_routes.py` TestClient, sin worker

## Phase 3: Slice 2 — QVAC (contrato JS)

- [x] 3.1 `app/qvac_client.py` fachada JS: `ocr(path)`, `complete(history,tools)`, `startup/shutdown`
- [x] 3.2 Load: `OCR_LATIN` + `LLAMA_3_2_1B_INST_Q4_0` via `load_model(t, model_src=…)`; fail → flags false
- [x] 3.3 OCR: `ocr_stream` + `OcrStreamRequest` image `{type:filePath,value}`; concat `text`/`confidence`
- [x] 3.4 LLM: `completion` tools+handlers; leer `run.events`/`run.final`; `toolCall.invoke()`; extract≠save
- [x] 3.5 Wire `POST /remitos` foto → ocr → complete; mock runtime en tests; spike 1 foto fixture (placeholder; live worker skipped)

## Phase 4: Slice 3 — UI query

- [x] 4.1 Templates HTMX: upload, form, row, list, banner, resumen (`HX-Request`)
- [x] 4.2 `POST /remitos/{id}` edit conserva `raw_ocr`; `GET /resumen` = `SUM(tonelaje_kg)`
- [x] 4.3 Tests partials + scenario confirm/edit

## Phase 5: Slice 4 — demo

- [x] 5.1 `fixtures/tickets/` 3 fotos + seed opcional
- [x] 5.2 README: `install-worker`, uvicorn, airplane mode, 3 min (upload→fila→totales)
- [x] 5.3 Banner `ocr_ready`/`llm_ready`; smoke happy path local

## Implementation order

0→1 (API sin worker) → 2 (SDK) → 3 (UI) → 4 (demo). All slices 0–4 done. Next = `sdd-verify` full. After verify: pause (DoraHacks submit = Alto). Do not archive yet.

**What**: Marked slice 4 tasks 5.1–5.3 complete after apply.
**Why**: Fifth apply batch — demo README, synthetic tickets, `make demo`.
**Where**: .atl/sdd/agro-qvac-local-tasks.md
**Learned**: Worker npm (`@qvac/sdk@0.17.1`) installed; model weights still download on first REMITO_QVAC=1 boot.
