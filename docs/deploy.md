# Deploy — Vercel + Render (opcional)

**No es el envío.** El jurado QVAC mira video local + repo
([submit.md](submit.md)). Render/Vercel solo sirven si alguien quiere
clickear la UI **sin** el agente (formulario + seed, `REMITO_QVAC=0`).

El producto offline (QVAC + modo avión) sigue siendo `make demo` en notebook.

## Arquitectura

| Plataforma | Rol | URL típica |
|------------|-----|------------|
| **Render** | Backend: FastAPI, HTMX, SQLite en disco persistente | `https://qcamp.onrender.com` |
| **Vercel** | Landing estática que enlaza a Render | `https://qcamp.vercel.app` |
| **Local** | Demo QVAC on-device, airplane mode | `http://127.0.0.1:8000` |

En cloud **no corre el worker QVAC** (`REMITO_QVAC=0`): Render no trae Node + pesos de modelos en el free tier. La presentación online usa formulario manual + seed de demo; el pitch de inferencia local lo mostrás en el notebook.

## 1. Render (backend)

1. Conectá el repo en [Render](https://render.com) → **New Blueprint** o Web Service.
2. Usá `render.yaml` (incluye disco en `/var/data`, seed demo, QVAC off).
3. Primer deploy: anotá la URL pública (`https://….onrender.com`).
4. Opcional: en Environment → `REMITO_BACKEND_URL` = esa URL (para health/links).

**Start command** (ya en blueprint):

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Variables clave**

| Variable | Valor cloud |
|----------|-------------|
| `REMITO_HOST` | `0.0.0.0` |
| `REMITO_QVAC` | `0` |
| `REMITO_SEED_DEMO` | `1` (3 remitos de ejemplo si la DB está vacía) |
| `REMITO_DB_PATH` | `/var/data/remitos.db` |
| `REMITO_CORS_ORIGINS` | URL de Vercel si algún día separás API cross-origin |

Probar: `GET /health` → `{ "ok": true, "db": "ok", … }` y `GET /app` → UI.

## 2. Vercel (landing)

1. Importá el mismo repo en [Vercel](https://vercel.com).
2. En **Environment Variables** → `REMITO_BACKEND_URL` = URL de Render (sin slash final).
3. Build: `bash scripts/build-vercel-landing.sh` (configurado en `vercel.json`).
4. Output: `public/index.html` con links a `…/app`.

Local:

```bash
REMITO_BACKEND_URL=https://tu-app.onrender.com bash scripts/build-vercel-landing.sh
# abrir public/index.html o npx serve public
```

## 3. Qué decir en la presentación

- **Online (Vercel + Render):** “Así se ve el flujo completo — cargar remito, tabla, total del día — sin instalar nada.”
- **Local (notebook):** “Acá está QVAC: OCR + agente 1B on-device, modo avión. Eso es el producto de campo.”

No mezclar: en cloud no prometas inferencia QVAC si `ocr_ready=false`.

## 4. Local sin cambios

```bash
make demo   # sigue en 127.0.0.1:8000
REMITO_QVAC=1 make demo   # con worker (post install-worker)
```

`render.yaml` no afecta el entorno local.
