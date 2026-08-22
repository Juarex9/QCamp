# Design: Qcamp (agro-qvac-local)

**Decision:** un proceso Python. FastAPI `127.0.0.1` orquesta; `QvacRuntime` carga OCR+LLM una vez; tools validan JSON; SQLite `data/remitos.db`; Jinja/HTMX. Greenfield. REST `/remitos` (no `/upload`).

Happy path: lifespan DB + QVAC (best-effort) → `POST /remitos` guarda imagen → `QvacRuntime.ocr()` (contrato JS) → `completion(tools)` → validate → INSERT → partial HTMX. OCR/LLM down → form manual.

Fuente SDK: https://docs.qvac.tether.io/js-ts-sdk/ + https://docs.qvac.tether.io/ai-capabilities/ocr/ + https://docs.qvac.tether.io/reference/api/ + https://docs.qvac.tether.io/python-sdk/

## Directory tree

```
app/main.py db.py schema.sql models.py tools.py qvac_client.py
app/templates/{base,index}.html  partials/{row,list,resumen,form,banner}.html  static/app.css
tests/{conftest,test_schema,test_tools,test_routes}.py
data/{remitos.db,images/}   fixtures/tickets/   pyproject.toml README.md .gitignore
```

## Sequence

```mermaid
sequenceDiagram
  participant B as HTMX
  participant F as FastAPI
  participant D as Disk+SQLite
  participant Q as QvacRuntime
  B->>F: POST /remitos (foto)
  F->>D: save data/images/{uuid}
  F->>Q: ocr(path)  %% JS ocr(); Py ocr_stream+filePath
  Q-->>F: blocks text+bbox+conf
  F->>Q: completion(ocr, tools)  %% events/final + invoke
  Q->>D: extract_remito (no IO) then save_remito INSERT
  F-->>B: 200 partial row
```

## Modules

| Module | Role |
|--------|------|
| `main.py` | Bind 127.0.0.1. Lifespan. HTMX vs full (`HX-Request`). |
| `qvac_client.py` | Wrapper JS-like. Py: `Client()`+transport+`install-worker`. Load OCR_LATIN + LLM once. |
| `tools.py` | 4 handlers: LLM **y** routes (slice 1 / degradado). |
| `db.py` | sqlite3 + WAL + `row_factory`. Schema on startup. |
| `models.py` | Pydantic. `tonelaje_kg` numérico obligatorio en save. |

## Decisions

| Topic | Choice | Rejected | Why |
|-------|--------|----------|-----|
| Process | FastAPI + worker sidecar | Next.js | 48h |
| Pipeline | OCR → LLM tools → SQL | VLM; parseo libre | tools+JSON; extract ≠ save |
| QVAC | Singleton lifespan | Client/request | RAM; Python `Client()` |
| Routes | `/`, `/remitos`, `/{id}`, `/resumen`, `/health` | `/upload` `/summary` | REST + HTMX |
| Degraded | Form manual | Bloquear ingest | Demo sin worker |
| Slice 2 | Spike OCR+LLM | PRs OCR/LLM split | Un worker, un SDK risk |
| DB | SQLite archivo | Postgres | Cero ops |
| Tests | Unit + TestClient mock | Live QVAC CI | `strict_tdd: false` |

## QVAC wrapper (mismo contrato JS/TS)

JS worker es **in-process**. Python **no**: `Client()` + `client.transport` + `python -m tetherto.qvac_sdk install-worker` (Node ≥22.17). Mismo worker `@qvac/sdk`.

| JS/TS (canónico) | Python (mapear 1:1) |
|------------------|---------------------|
| `loadModel({ modelSrc: OCR_LATIN, modelConfig })` | `load_model(t, model_src=OCR_LATIN, model_config=…)` |
| `loadModel({ modelSrc: LLAMA_3_2_1B_INST_Q4_0 })` | `load_model(t, model_src=LLAMA_3_2_1B_INST_Q4_0, …)` |
| `ocr({ modelId, image: path })` → `{ blocks }` | `ocr_stream(t, OcrStreamRequest)`; image `{type:"filePath","value": path}` (JS envuelve el string; Py no) |
| `completion({ modelId, history, tools })` | `completion(t, model_id=…, history=…, tools=…)` |
| `run.events` / `run.final` + `toolCall.invoke()` | `CompletionRun.events` / `.final` + `ToolCall` (tokenStream deprecado) |
| `unloadModel` / `close()` | `unload_model(t, id)` + exit del `Client()` |

`QvacRuntime.ocr(path)` y `.complete(history, tools)` son la fachada JS. Adentro: `OCR_LATIN` (EasyOCR/CRAFT; no path onnx suelto), `langList: ["en"]` oficial (Latin cubre dígitos/patentes). LLM: `ctx_size` 2048–4096, tools on, temp baja. Fail → `ocr_ready`/`llm_ready` false. No VLM/`attachments` como primario.

## Tools

| Tool | Input | Side effect | Caller |
|------|-------|-------------|--------|
| `extract_remito` | `raw_ocr` | None. Campos + confidence | LLM |
| `save_remito` | campos + ocr + path + conf | Validate + INSERT | LLM y POST |
| `list_remitos` | fecha?, producto? | Read | LLM y GET |
| `summarize_harvest` | fecha? | `SUM(tonelaje_kg)`, count | LLM y `/resumen` |

Save rechaza kg no numérico/≤0. Extract basura → `raw_ocr` + edit.

## SQLite

```sql
CREATE TABLE remitos (
  id INTEGER PRIMARY KEY, created_at TEXT NOT NULL,
  fecha TEXT, patente TEXT, tonelaje_kg REAL,
  origen TEXT, destino TEXT, producto TEXT, humedad REAL,
  raw_ocr TEXT, image_path TEXT, confidence REAL
);
CREATE INDEX idx_remitos_fecha ON remitos(fecha);
CREATE INDEX idx_remitos_producto ON remitos(producto);
```

`IF NOT EXISTS` only. No versioned migrations.

## Routes + degraded

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/health` | `{ok, ocr_ready, llm_ready, db}` |
| GET | `/` | Shell: upload + form + tabla |
| POST | `/remitos` | Foto y/o campos. Pipeline o save directo. Partial row |
| GET | `/remitos` | Lista. Partial list si HTMX |
| POST | `/remitos/{id}` | Edit (OCR sucio / alucinación) |
| GET | `/resumen` | Totales. Partial resumen |

| Failure | UX |
|---------|----|
| Worker/OCR/LLM down | Banner + form; `save_remito` igual |
| OCR vacío | Path + form; no inventar kg |
| LLM sin tools / JSON inválido | Guardar `raw_ocr`; edit |
| Validate fail | 422 + form; no INSERT |

## File changes (all Create)

Create: `pyproject.toml` (fastapi, uvicorn, jinja2, python-multipart, pytest, httpx, ruff, tetherto-qvac-sdk, Py≥3.11), `app/*`, `tests/*`, `fixtures/tickets/` (3 fotos), `.gitignore` (`.venv/`,`data/`), `README.md` (slice 4). Delete: none.

## Testing

| Layer | What | How |
|-------|------|-----|
| Unit | Schema/indexes; tools; reject kg | tmp sqlite; **no worker** |
| Integration | CRUD + degradado + HTMX | `TestClient` + mock `QvacRuntime` |
| Spike | 1–3 fotos → OCR → tools | Slice 2 manual; no CI live |

pytest planeado. Pre-commit NOT CONFIGURED.

## 48h slices (`auto-chain`)

| Slice | Entrega | Verify | Lines |
|-------|---------|--------|-------|
| **0** scaffold+db | pyproject, `/health`, schema, pytest+ruff | health + `test_schema` | 80–120 |
| **1** ingest mock | POST/GET `/remitos` sin QVAC | TestClient + lista | 150–200 |
| **2** qvac spike | wrapper JS-like: OCR_LATIN + ocr_stream + tools/invoke | fotos + mocks | 150–250 |
| **3** ui query | HTMX list/edit + `/resumen` | TestClient partials | 100–150 |
| **4** demo/readme | polish + README 3 min | happy path jurado | 50–80 |

0–1 no worker. **First apply = slice 0 only.**

## Review workload forecast

Total ≫400 → chained.

```
Decision needed before apply: No
Chained PRs recommended: Yes
400-line budget risk: High
```

`auto-chain`. No `size:exception`. Stacked to main. Rollback: stop procs; wipe `data/` + `.venv`.

## Open questions (non-blocking)

Cerrados por docs: `ocr` (JS) vs `ocr_stream`+`filePath` (Py); `OCR_LATIN`; `events`/`final`+`invoke`. Spike 2 solo verifica wheel real (`ToolCall` handler shape, `langList` ES si existe).

## Next

`sdd-apply` slice 0 only (`auto-chain`).
