# Qcamp

Libreta local del productor: foto del ticket de balanza → kg, patente y fecha en SQLite.
Inferencia **solo QVAC on-device**. Cero cloud LLM. Si el modelo 1B inventa toneladas, no se guarda.

Aleph Hackathon 2026 · track QVAC. El jurado ve un **video local** (async), no una URL en la nube.

<p align="left">
  <img src="fixtures/tickets/remito-soja-tucuman.png" alt="Ticket sintético de demo (soja, 18500 kg)" width="420">
</p>

```text
foto → OCR_LATIN → Llama 3.2 1B Q4 + tools
         1. extract_remito   (sin IO)
         2. save_remito      (INSERT solo si kg > 0 y no inventó)
       → SQLite → /resumen
```

## Para el jurado

Empezá por estos archivos. Son links relativos: se ven bien en GitHub.

| Qué | Archivo |
| --- | --- |
| OCR + load de modelos | [app/qvac_client.py](app/qvac_client.py) (`startup`, `ocr`) |
| Agente 2 turnos | [app/qvac_client.py](app/qvac_client.py#L257) (`run_document_agent`) |
| Tools | [app/tools.py](app/tools.py#L181) (`extract_remito`, `save_remito`) |
| Foto → fila | [app/main.py](app/main.py#L443) (`POST /remitos`) |
| Por qué 1B + OCR | [docs/modelos.md](docs/modelos.md) |
| Mapa al brief | [docs/cobertura.md](docs/cobertura.md) |
| Brief oficial | [docs/qvac-track.md](docs/qvac-track.md) |
| Cómo enviar | [docs/submit.md](docs/submit.md) |

- SDK: `tetherto-qvac-sdk` (Python) + worker `@qvac/sdk` 0.17.1
- Modelos: `OCR_LATIN` + `LLAMA_3_2_1B_INST_Q4_0` (`tools: True`, `temp: 0.1`)
- No usamos el HTTP OpenAI-compat de QVAC como camino principal: el premio 2° pide tool calling nativo

## Quick path (3 minutos)

```bash
make demo
# http://127.0.0.1:8000  →  Abrir la app  →  /app
```

1. Arrancar: `make demo` (uvicorn en `127.0.0.1:8000`, nunca `0.0.0.0` en local)
2. Subir `fixtures/tickets/remito-soja-tucuman.png`
3. Confirmar campos y **Guardar remito**
4. Ver la fila (patente, kg, producto)
5. Totales en `/resumen` (`SUM(tonelaje_kg)`)

Banner `ocr_ready` / `llm_ready`. Si ambos son `false`, el formulario manual sigue andando.
CSS 100% local: la landing también carga en modo avión.

## Instalar (clone limpio)

Python ≥ 3.11. Node ≥ 22.17 solo para el worker QVAC. Red **una vez**.

```bash
git clone git@github.com:Juarex9/QCamp.git
cd QCamp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m tetherto.qvac_sdk install-worker
REMITO_QVAC=1 make demo
```

`install-worker` deja `@qvac/sdk` en `~/.cache/qvac/worker/`.
El primer `REMITO_QVAC=1` baja los pesos de `OCR_LATIN` + Llama 1B Q4.

Sin red o si falla el boot:

```bash
REMITO_QVAC=0 make demo
```

```bash
.venv/bin/pytest
.venv/bin/ruff check .
```

## Airplane mode

| Momento | Red | Qué hacer |
| --- | --- | --- |
| Setup | ON | venv + deps + `install-worker` + primer load de pesos |
| Demo | OFF | `REMITO_QVAC=1 make demo` → upload → fila → `/resumen` |
| Sin modelos | OFF | `REMITO_QVAC=0 make demo` → form o `python scripts/seed_demo.py` |

`extract_remito` no toca disco. `save_remito` hace el INSERT.
Si el 1B cambia el kg del extract, no hay INSERT: el operador edita.

Atajo sin foto: `python scripts/seed_demo.py` → 3 filas, `/resumen` = 58500 kg.

## Modelos

| Rol | Constante QVAC | Notas |
| --- | --- | --- |
| Visión → texto | `OCR_LATIN` | El 1B no mira la foto |
| Agente / tools | `LLAMA_3_2_1B_INST_Q4_0` | 1B instruct Q4_0 |

Latencia OCR + 2 turnos: medirla en el video (aún no hay número en el repo).
Detalle: [docs/modelos.md](docs/modelos.md).

## Qué está probado

| Afirmación | Estado |
| --- | --- |
| UI, SQLite, tools, gates | pytest (64 tests, worker mockeado) |
| Worker `@qvac/sdk` 0.17.1 | Instalado en setup local |
| Pesos + foto en vivo | Pendiente (`REMITO_QVAC=1`) |
| Deploy cloud | Opcional. El jurado no lo necesita |

## Variables

| Variable | Default | Efecto |
| --- | --- | --- |
| `REMITO_QVAC=1` | intenta worker fuera de pytest | OCR + LLM locales |
| `REMITO_QVAC=0` | forzado en tests | Formulario / seed |
| `REMITO_DB_PATH` | `data/remitos.db` | SQLite (gitignored) |
| `REMITO_IMAGES_DIR` | `data/images/` | Fotos subidas (gitignored) |

## Tickets de demo

Tres PNGs en [`fixtures/tickets/`](fixtures/tickets/). **No son remitos reales.**

| Archivo | Producto | kg | Patente |
| --- | --- | --- | --- |
| `remito-soja-tucuman.png` | soja | 18500 | AB123CD |
| `remito-maiz-salta.png` | maíz | 24200 | AC456DE |
| `remito-trigo-santiago.png` | trigo | 15800 | AD789FG |

## Docs

Índice: [docs/README.md](docs/README.md)

- [docs/submit.md](docs/submit.md) — DoraHacks + guion de video
- [docs/cobertura.md](docs/cobertura.md) — premios 1° y 2°
- [docs/pitch.md](docs/pitch.md) — usuario = productor
- [docs/arquitectura.md](docs/arquitectura.md) — mapa de archivos
- [docs/deploy.md](docs/deploy.md) — Render/Vercel (opcional)
