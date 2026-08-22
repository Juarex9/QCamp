# Qcamp

Agente **local** que lee un ticket de balanza (foto) y deja kg / patente / fecha
en SQLite. Inferencia solo QVAC on-device. Cero cloud LLM. El productor
confirma o edita; el 1B no inventa toneladas.

Aleph Hackathon 2026 · track QVAC. Demo del jurado = **video local** (async),
no una URL en la nube.

## Para el jurado (empezá acá)

| Qué | Dónde |
|-----|--------|
| OCR + load de modelos | [`app/qvac_client.py`](https://github.com/Juarex9/QCamp/blob/main/app/qvac_client.py) — `startup`, `ocr` |
| Agente 2 turnos (extract → save) | [`app/qvac_client.py`](https://github.com/Juarex9/QCamp/blob/main/app/qvac_client.py#L257) — `run_document_agent` |
| Tools (sin IO / con INSERT) | [`app/tools.py`](https://github.com/Juarex9/QCamp/blob/main/app/tools.py#L181) — `extract_remito`, `save_remito` |
| Foto → OCR → agente → fila | [`app/main.py`](https://github.com/Juarex9/QCamp/blob/main/app/main.py#L443) — `POST /remitos` |
| Por qué 1B + OCR separado | [docs/modelos.md](docs/modelos.md) |
| Mapa al brief | [docs/cobertura.md](docs/cobertura.md) |
| Brief oficial | [docs/qvac-track.md](docs/qvac-track.md) |

**SDK:** `tetherto-qvac-sdk` (Python) + worker `@qvac/sdk` 0.17.1.  
**Modelos:** `OCR_LATIN` + `LLAMA_3_2_1B_INST_Q4_0` (`tools: True`, `temp: 0.1`).  
**No usamos** el HTTP OpenAI-compat de QVAC como camino principal: el premio
2° pide tool calling nativo.

## Quick path (3 minutos, localhost)

| Min | Qué | Cómo |
|-----|-----|------|
| 0:00 | Arrancar | `make demo` |
| 0:20 | UI | http://127.0.0.1:8000 → **Abrir la app** (`/app`) |
| 0:40 | Subir ticket | `fixtures/tickets/remito-soja-tucuman.png` |
| 1:30 | Confirmar | Revisar campos y **Guardar remito** |
| 2:00 | Fila | Tabla: patente, kg, producto |
| 2:30 | Totales | http://127.0.0.1:8000/resumen — `SUM(tonelaje_kg)` |

```bash
make demo
# uvicorn en 127.0.0.1:8000 (nunca 0.0.0.0 en local)
```

Banner: `ocr_ready` / `llm_ready`. Si ambos son `false`, el formulario
manual sigue andando (degradado). CSS 100% local: landing también en
modo avión.

## Instalar (clone limpio, con red una vez)

Python ≥ 3.11. Node ≥ 22.17 solo para el worker QVAC.

```bash
git clone git@github.com:Juarex9/QCamp.git
cd QCamp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m tetherto.qvac_sdk install-worker
REMITO_QVAC=1 make demo
```

`install-worker` instala `@qvac/sdk` en `~/.cache/qvac/worker/`. El
**primer** `REMITO_QVAC=1` baja los pesos de `OCR_LATIN` + Llama 1B Q4
(puede ser grande). Sin red o si falla el boot: `REMITO_QVAC=0 make demo`
— UI y SQLite andan igual.

Tests (no arrancan el worker):

```bash
.venv/bin/pytest
.venv/bin/ruff check .
```

## Airplane mode

La red solo se usa **una vez** para instalar. La demo del jurado debe
cerrar ingest + query **sin internet**.

| Momento | Red | Qué hacer |
|---------|-----|-----------|
| Setup | ON | venv + deps + `install-worker` + primer load de pesos |
| Demo | OFF | `REMITO_QVAC=1 make demo` → upload → fila → `/resumen` |
| Sin modelos | OFF | `REMITO_QVAC=0 make demo` → form o `python scripts/seed_demo.py` |

Comprobar que no hay cloud: el proceso escucha `127.0.0.1`; no hay
API keys de LLM. Tools: `extract_remito` (sin IO) y `save_remito`
(INSERT) son **dos** tools. Si el 1B cambia el kg del extract, no hay
INSERT (`invented` → el operador edita).

Atajo sin foto: `python scripts/seed_demo.py` → 3 filas, `/resumen` = 58500 kg.

## Modelos y hardware

| Rol | Constante QVAC | Notas |
|-----|----------------|-------|
| Visión → texto | `OCR_LATIN` | EasyOCR/CRAFT. El 1B no mira la foto. |
| Agente / tools | `LLAMA_3_2_1B_INST_Q4_0` | 1B instruct Q4_0. Piso del brief 1–4B. |

Máquina de desarrollo / demo: notebook Linux, Python 3.11+. Latencia
OCR + 2 turnos LLM: **medir en el video** (aún no hay número en repo).
Un 1B Q4 entra holgado en ~4 GB de RAM de modelo; el techo del brief
para 4B Q4 es ~4 GB.

Detalle y alternativas descartadas: [docs/modelos.md](docs/modelos.md).

## Qué está probado (honestidad)

| Afirmación | Estado |
|------------|--------|
| UI, SQLite, tools, gates, duplicados | Cubierto por pytest (64 tests, worker mockeado) |
| Worker `@qvac/sdk` 0.17.1 | Instalado en setup local |
| Pesos OCR + Llama + foto real | **Pendiente de corrida en vivo** (`REMITO_QVAC=1`) |
| Tasa de acierto en N corridas | No medida todavía |
| Deploy cloud (Render/Vercel) | Opcional. El jurado no lo necesita |

## Variables

| Variable | Default | Efecto |
|----------|---------|--------|
| `REMITO_QVAC=1` | (fuera de pytest: intenta worker) | OCR + LLM locales |
| `REMITO_QVAC=0` | tests lo fuerzan | Formulario / seed; `ocr_ready=false` |
| `REMITO_DB_PATH` | `data/remitos.db` | SQLite (gitignored) |
| `REMITO_IMAGES_DIR` | `data/images/` | Fotos subidas (gitignored) |

## Tickets de demo

Tres PNGs en `fixtures/tickets/`. **No son remitos reales.**

| Archivo | Producto | kg | Patente |
|---------|----------|----|---------|
| `remito-soja-tucuman.png` | soja | 18500 | AB123CD |
| `remito-maiz-salta.png` | maíz | 24200 | AC456DE |
| `remito-trigo-santiago.png` | trigo | 15800 | AD789FG |

Regenerar: `python scripts/gen_synthetic_tickets.py`.

## Docs

Índice: [docs/README.md](docs/README.md).

| Doc | Para qué |
|-----|----------|
| [docs/submit.md](docs/submit.md) | Envío DoraHacks + guion de video |
| [docs/cobertura.md](docs/cobertura.md) | Cómo Qcamp cubre 1° y 2° premio |
| [docs/pitch.md](docs/pitch.md) | Usuario = productor, dispositivo = notebook |
| [docs/arquitectura.md](docs/arquitectura.md) | Mapa de archivos |
| [docs/modelos.md](docs/modelos.md) | Por qué OCR + 1B Q4 |
| [docs/qvac-track.md](docs/qvac-track.md) | Brief oficial del track |
| [docs/deploy.md](docs/deploy.md) | Render/Vercel (opcional, no es el producto) |
