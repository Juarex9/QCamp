# Exploration: agro-qvac-local

**Outcome:** MVP de 48h = FastAPI en `127.0.0.1` + Jinja/HTMX + SQLite + pipeline **OCR QVAC → LLM 1–4B con tools**. No Next.js, no Postgres, no cloud LLM, no P2P.

**Why:** En el NOA los remitos/tickets de balanza viven en papel hasta que alguien llega a un pueblo con internet. Aleph (22–23 Aug 2026) premia inferencia 100% local + tool use determinista. El repo es greenfield (solo harness); el código se escribe de cero.

## Quick path (demo happy path)

1. `python -m tetherto.qvac_sdk install-worker` (una vez; Node >= 22.17).
2. `uvicorn` sirve UI en `http://127.0.0.1:8000`.
3. Operador sube foto de un ticket de balanza.
4. QVAC OCR (`modelType: "ocr"`, pipeline `easyocr`) devuelve bloques `{text, bbox, confidence}`.
5. LLM local (`LLAMA_3_2_1B_INST_Q4_0`, `modelConfig.tools: true`) llama `extract_remito` → `save_remito`.
6. UI lista remitos y `summarize_harvest` muestra toneladas del día.

Criterio de jueces: foto → JSON estructurado → persistido → total consultable, **sin red**.

## Problem

La logística agrícola del NOA depende de remitos físicos. Sin conectividad, el productor/contratista no digitaliza tonelaje, patente, origen/destino ni humedad hasta trasladarse a un centro urbano. Eso retrasa liquidación, control de cosecha y decisiones de flete.

Fuente canónica: vault `Propuestas Aleph Ago 2026.md` — **Proyecto 1 QVAC**. Proyecto 2 Pear queda fuera.

## Users

| Persona | Necesidad en 48h | Fuera de MVP |
|---------|------------------|--------------|
| Operador de balanza / contratista (demo) | Cargar foto, ver campos extraídos, confirmar, consultar totales | App móvil, sync multi-finca |
| Productor (narrativa) | Ver toneladas por día/producto sin internet | Dashboard cloud, Zafra |
| Jurado Aleph | Ver offline + tools + persistencia en <3 min | P2P, OTA, mesh |

## Constraints

| Tipo | Regla |
|------|--------|
| Hackathon | 48h (22–23 Aug 2026). Código desde cero. Copiar `zafra-ai` / `vitistrust` = descalificación (riesgo Alto). |
| Offline | Cero cloud LLM. Worker QVAC local. Bind `127.0.0.1`. |
| Runtime | Python >= 3.11 (SDK pide >= 3.10). Node >= 22.17 para el worker. |
| Modelos | LLM 1–4B + OCR addon. `modelConfig.tools: true` obligatorio para tools. |
| Vertical | Solo agro remitos. Cambiar a Pear = riesgo Alto. |
| Secretos | No leer ni copiar `Credenciales.md`. |
| Quality | `strict_tdd: false` (no hay pytest en disco). Runner planeado: pytest + ruff. Pre-commit: NOT CONFIGURED. |
| Persistencia SDD | Engram `sdd/agro-qvac-local/*`. No crear `openspec/`. MCP puede bindir a `cosillas`. |

Dominio Zafra (NOA, agritech) se usa como **contexto**. Cero reuso de código.

## Current State

Repo `/home/agustin/Escritorio/projects/aleph-1`: git + `AGENTS.md` + `.cursor/rules/` + `.atl/` (init, testing-capabilities, skill-registry). **Cero código de aplicación.**

| Presente | Ausente |
|----------|---------|
| Harness SDD, `aleph-harness.mdc` | `pyproject.toml`, FastAPI, SQLite, UI |
| Defaults de stack (decididos) | `tetherto-qvac-sdk`, worker, modelos |
| Vault de producto (fuera del repo) | Tests, ruff, hooks, `.gitignore` |

Init cache (`sdd-init/aleph-1`, obs #155 bajo `cosillas`): `strict_tdd: false`, delivery `auto-chain`, artifact store `engram`.

## Affected Areas (planned, not on disk)

| Path | Por qué |
|------|---------|
| `pyproject.toml` | Deps: fastapi, uvicorn, jinja2, sqlite3 stdlib, pytest, ruff, tetherto-qvac-sdk |
| `app/main.py` | FastAPI localhost, upload, list, summarize |
| `app/db.py` + `app/schema.sql` | Tabla `remitos` |
| `app/qvac_client.py` | `Client()` asyncio, load OCR + LLM, `ocr`/`ocr_stream`, `completion` + tools |
| `app/tools.py` | Handlers: extract_remito, save_remito, list_remitos, summarize_harvest |
| `app/templates/` + `app/static/` | Jinja/HTMX: upload, tabla, totales |
| `data/remitos.db` + `data/images/` | Persistencia local (gitignore) |
| `tests/` | pytest: schema, tool handlers, extract parsing (mocks QVAC) |
| `README.md` | Demo: install-worker, run, foto de ejemplo |

## Approaches

Defaults **ya decididos**. Tabla = chosen vs rechazados (no reabrir).

| Decisión | Chosen | Rechazado | Por qué chosen | Effort |
|----------|--------|-----------|----------------|--------|
| DB | **SQLite** embebido | Postgres local | Cero ops, un archivo, demo offline | Low |
| App + UI | **FastAPI + Jinja/HTMX** | Next.js; CLI-only | Judges ven foto→tabla en browser; 48h no alcanza para Next | Med |
| Extracción | **OCR → LLM tools** | VLM-only; cloud OCR | Criterio Aleph: tool use + JSON; OCR da texto; 1–4B no es VLM fiable | Med |
| Inferencia | **tetherto-qvac-sdk local** | OpenAI/Gemini; llama.cpp solo | Track QVAC; worker oficial | Med |
| Tools | **extract / save / list / summarize** | MCP remoto; tools de sync | Cubren captura + consulta; deterministas | Low |
| Sync | **Ninguno** | P2P QVAC, cloud, Zafra | Fuera de MVP; Pear es otro proyecto | — |

### 1. OCR then LLM tools (recomendado — chosen)

OCR QVAC (`easyocr` o `doctr`) → concatenar bloques → `completion(..., tools=[...])` con handlers locales.

- Pros: encaja el track (OCR addon + tool use); JSON vía schema de tool, no parseo libre; fallback si LLM falla (mostrar raw_ocr).
- Cons: dos modelos en RAM; OCR latino puede fallar en tickets sucios/mano; docs públicas son TS-first (Python: `Client()`, `ocr_stream`).
- Effort: Medium

### 2. VLM-only (rechazado)

`completion` con `attachments: [{path}]` y un multimodal + projection model.

- Pros: un paso, menos glue.
- Cons: modelos 1–4B del track no son VLM; projection extra; JSON menos estable; no demuestra OCR addon.
- Effort: High (y riesgoso en 48h)

### 3. Cloud OCR / LLM (rechazado)

- Pros: accuracy.
- Cons: descalifica offline; no hay conectividad NOA; viola AGENTS.md.
- Effort: Low técnico / High de reglas

### 4. Next.js + API (rechazado)

- Pros: UI rica.
- Cons: dos runtimes, más superficie, 48h.
- Effort: High

### 5. CLI-only (rechazado)

- Pros: más rápido de codear.
- Cons: demo débil para jurado; upload de foto incómodo.
- Effort: Low

## Recommendation

**Arquitectura:** proceso único Python. FastAPI orquesta. QVAC worker en localhost. SQLite archivo. UI mínima.

```
[Browser Jinja/HTMX]
        │ HTTP 127.0.0.1
        ▼
[FastAPI]
   ├─ POST /upload → disk image → OCR → LLM tools → SQLite
   ├─ GET  /        → list remitos
   └─ GET  /summary → summarize_harvest
        │                 │
        ▼                 ▼
 [QVAC Client]      [SQLite remitos]
  OCR model          data/remitos.db
  LLM 1–4B + tools
```

### Tools (contrato)

| Tool | Input | Side effect |
|------|-------|-------------|
| `extract_remito` | texto OCR (+ opcional hints) | Ninguno. Devuelve campos tipados. |
| `save_remito` | campos + `raw_ocr` + `image_path` + `confidence` | INSERT SQLite |
| `list_remitos` | filtros opcionales (`fecha`, `producto`) | Read |
| `summarize_harvest` | `fecha` opcional | Agrega `SUM(tonelaje_kg)` |

`extract_remito` y `save_remito` son **dos tools** (no un solo insert): el LLM extrae; el handler de save valida tipos y persiste. Si extract es basura, la UI muestra raw_ocr y permite corrección manual mínima (1 form HTMX) — no bloquea la demo.

### Schema sketch (chosen)

```
remitos(
  id INTEGER PK,
  created_at TEXT,
  fecha TEXT,
  patente TEXT,
  tonelaje_kg REAL,
  origen TEXT,
  destino TEXT,
  producto TEXT,
  humedad REAL,
  raw_ocr TEXT,
  image_path TEXT,
  confidence REAL
)
```

### QVAC wiring (docs verificadas)

- Load OCR: `modelType: "ocr"`, `pipelineMode: "easyocr"` (default) o `"doctr"`. Bloques: `text`, `bbox [x1,y1,x2,y2]`, `confidence`. Stream: `ocr(..., stream: true)` / Python `ocr_stream`.
- Load LLM: `LLAMA_3_2_1B_INST_Q4_0`, `modelType: "llm"`, `modelConfig: { tools: true, ctx_size: 4096 }`.
- Tools: `{name, description, parameters, handler}` — invocar `toolCall.invoke()` / `call()`.
- Attachments existen en `history[].attachments` — **no** usarlos como path primario del MVP.
- Worker: `python -m tetherto.qvac_sdk install-worker`. Docs públicas son JS/TS; Python es `asyncio Client()`.

OCR `langList` en ejemplos es `en`/`fr`. Tickets NOA están en español: usar recognizer **Latin** (`OCR_CRAFT_LATIN_RECOGNIZER` o equivalente) y probar `es` si el SDK lo expone. No asumir EasyOCR cloud.

### Out of MVP

P2P / delegate remoto, cloud sync, mobile, Postgres, integración Zafra, Pear, auth, multi-user, deploy no-localhost.

## 48h slices (`auto-chain`)

Estimado >400 líneas totales → slices, no un PR monstruo. Commits solo si el humano lo pide.

| Slice | Entrega demoable | Verificación |
|-------|------------------|--------------|
| 0. Scaffold | `pyproject`, FastAPI hello, SQLite schema, pytest+ruff, `.gitignore` | `GET /health`, test schema |
| 1. Persist API | CRUD remitos sin QVAC (form + seed) | pytest + UI lista |
| 2. OCR local | Upload → `raw_ocr` + confidence en fila | Foto de ticket de prueba |
| 3. LLM tools | extract + save sobre OCR | JSON estable en 2–3 fotos |
| 4. Query + demo | list + summarize + README 3 min | Happy path frente a jurado |

Slice 0–1 no dependen del worker (mitiga download de modelos). Slice 2 es el riesgo de tiempo.

## Risks

- **OCR sucio:** tickets de balanza reales son fotos malas, números con polvo. Mitigación: 3 fotos de fixture + raw_ocr visible + edit HTMX.
- **Español en 1B:** Llama 3.2 1B + tools puede alucinar patente/kg. Mitigación: schema estricto, temp baja, validar `tonelaje_kg` numérico antes de save.
- **RAM / primer boot:** OCR + LLM + download. Mitigación: precargar worker/modelos **hoy**; documentar tamaño; no cargar VLM.
- **Python SDK vs docs TS:** surface Python menos documentada (`ocr_stream`, `Client()`). Mitigación: spike de 30–60 min en slice 2; no inventar API JS en Python.
- **langList ES:** ejemplos QVAC son en/fr. Mitigación: Latin recognizer; probar una foto ES en el spike.
- **Descalificación:** cualquier copia de zafra-ai/vitistrust. Mitigación: greenfield only; vault solo narrativa.
- **Engram project:** MCP cwd `$HOME` → `cosillas`; `project: aleph-1` = `unknown_project`. Retrieval sin filtro de proyecto + recovery `.atl/`.
- **Sin hooks/tests aún:** verify usará pytest cuando exista; `pre_commit_status` = NOT CONFIGURED.
- **Cambio de vertical (Pear):** riesgo Alto — no explorar.

## Ready for Proposal

**Yes.** Stack, tools, schema y slices están cerrados. `sdd-propose` debe fijar el mismo recorte (OCR→tools→SQLite→Jinja) sin reabrir alternativas.

### Checklist para propose

- [ ] Producto = agente local remitos NOA (QVAC), no Pear
- [ ] Stack = Python 3.11 + FastAPI + SQLite + Jinja/HTMX + qvac-sdk
- [ ] Tools = extract_remito, save_remito, list_remitos, summarize_harvest
- [ ] Schema = columnas listadas arriba
- [ ] Out of MVP = P2P, cloud, mobile, Postgres, Zafra
- [ ] Demo = happy path de 6 pasos
- [ ] No `openspec/`; Engram `sdd/agro-qvac-local/*`

### Next step

`sdd-propose` — proposal con scope, no-goals y rollback (borrar `data/` + venv).
