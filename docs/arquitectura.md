# Arquitectura (mapa de archivos)

Un proceso Python. FastAPI en `127.0.0.1` orquesta; QVAC carga OCR+LLM
una vez; las tools validan JSON; SQLite guarda filas; Jinja/HTMX pinta.

```
foto → OCR_LATIN
     → Llama 3.2 1B Q4 + tools
        1. extract_remito   (sin IO; arma JSON; parser regex gana si hay match)
        2. save_remito      (solo si kg > 0 y no inventó el kg; INSERT)
     → SQLite / HTMX
```

## Quick path

| Capa | Archivo |
|------|---------|
| HTTP + ingest | `app/main.py` |
| QVAC (ocr / complete / agente) | `app/qvac_client.py` |
| Tools + parser | `app/tools.py` |
| Schema / validación | `app/models.py`, `app/schema.sql` |
| SQLite | `app/db.py` |
| Config local vs cloud | `app/config.py` |
| UI | `app/templates/`, `app/static/app.css` |
| Seed demo | `app/seed.py`, `scripts/seed_demo.py` |

## Decisiones

| Tema | Decisión |
|------|----------|
| Bind local | `127.0.0.1` (`REMITO_HOST=0.0.0.0` solo si se deploya) |
| Inferencia | Solo worker QVAC. Fail → banner `ocr_ready=false`, form manual |
| Duplicados | Aviso 409; “Es otro viaje” confirma INSERT |
| Edit parcial | Campos ausentes se conservan; vacío explícito borra |
| Cloud | Fuera del producto. Ver [deploy.md](deploy.md) |

## Next step

Permalinks listos para el jurado: [submit.md](submit.md).
