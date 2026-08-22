# Proposal: Qcamp (agro-qvac-local)

## Intent

Digitalizar remitos/tickets de balanza del NOA 100% offline. Hoy el papel no se carga hasta que hay internet urbano; liquidación y control de cosecha se atrasan.

**Why now:** Aleph 22–23 Aug 2026 (48h). Jurado premia inferencia local + tool use + JSON determinista. Repo greenfield — código de cero.

Producto: **Qcamp**.

## Scope

### In Scope

- FastAPI en `127.0.0.1` + Jinja/HTMX + SQLite
- Pipeline OCR QVAC → LLM 1–4B con tools
- Tools: `extract_remito`, `save_remito`, `list_remitos`, `summarize_harvest`
- Tabla `remitos` (fecha, patente, tonelaje_kg, origen, destino, producto, humedad, raw_ocr, image_path, confidence)
- Demo 3 min: upload foto → fila estructurada → totales, airplane mode
- pytest + ruff (Strict TDD off hasta que exista runner)

### Out of Scope

- P2P, cloud LLM/sync, mobile, Postgres, Zafra, Pear, auth, multi-user, deploy no-localhost
- Next.js, VLM-only, copia de `zafra-ai` / `vitistrust`

## Capabilities

### New Capabilities

- `remito-ingest`: upload foto → OCR → `extract_remito` → `save_remito` (JSON tipado)
- `remito-query`: `list_remitos` + `summarize_harvest` (`SUM(tonelaje_kg)`)
- `local-qvac-runtime`: worker local, OCR+LLM con `tools: true`, bind localhost, cero red

### Modified Capabilities

- None (greenfield)

## Approach

Un proceso Python. FastAPI orquesta. QVAC worker en localhost. UI mínima.

Happy path: `install-worker` → uvicorn → upload ticket → bloques OCR → LLM llama extract+save → lista + totales.

`extract_remito` y `save_remito` son dos tools: extract sin side effect; save valida tipos e INSERT. Si extract falla, UI muestra `raw_ocr` + form HTMX.

Modelo: `LLAMA_3_2_1B_INST_Q4_0` + OCR `easyocr` (recognizer Latin / `es` si el SDK lo expone). No reabrir alternativas de explore.

Slices `auto-chain`: 0 scaffold → 1 persist API → 2 OCR → 3 LLM tools → 4 query+demo.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pyproject.toml` | New | fastapi, uvicorn, jinja2, pytest, ruff, tetherto-qvac-sdk |
| `app/main.py` | New | `/health`, `/upload`, list, `/summary` |
| `app/db.py` + `app/schema.sql` | New | tabla `remitos` |
| `app/qvac_client.py` | New | `Client()` OCR + `completion` + tools |
| `app/tools.py` | New | 4 handlers |
| `app/templates/` + `app/static/` | New | upload, tabla, totales |
| `data/` | New | `remitos.db` + images (gitignore) |
| `tests/` | New | schema, tools, parse (QVAC mocked) |
| `README.md` | New | demo 3 min |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| OCR sucio / tickets malos | High | 3 fotos fixture + `raw_ocr` + edit HTMX |
| Llama 1B alucina kg/patente | Med | schema estricto, temp baja, validar numérico |
| RAM / primer boot de modelos | High | precargar worker hoy; no VLM |
| Python SDK vs docs TS | Med | spike 30–60 min en slice 2 |
| `langList` ES ausente | Med | Latin recognizer; probar foto ES |
| Copia zafra-ai | Low | greenfield only |

## Rollback Plan

1. Parar uvicorn y worker QVAC.
2. Borrar `data/` (db + imágenes).
3. Borrar venv (`.venv/` o equivalente).
4. Deshacer commits de apply solo si el humano lo pide.
5. No hay migraciones ni secretos que revertir.

## Dependencies

- Python >= 3.11, Node >= 22.17
- `tetherto-qvac-sdk` + `install-worker`
- Modelos locales: OCR addon + `LLAMA_3_2_1B_INST_Q4_0`
- Engram `sdd/agro-qvac-local/*`; no `openspec/`

## Success Criteria

- [ ] Inferencia 100% local (airplane mode); cero cloud LLM
- [ ] Tool use + JSON determinista (`extract_remito` → `save_remito`)
- [ ] Demo: upload remito → fila estructurada → query totales
- [ ] Bind `127.0.0.1`; persistencia SQLite en `data/remitos.db`
- [ ] Código greenfield (cero zafra-ai/vitistrust)
