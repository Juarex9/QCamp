# Cómo pulimos Qcamp contra el track QVAC

Fuente del track (premios y brief): [track.md](track.md). Este archivo no lo reemplaza: mapea ese brief al repo. How-to de correr la app: [README](../README.md).

## Quick path (qué tiene que ver el jurado)

El brief pide **agentes locales que reemplazan trabajo operativo** (1°) y **modelos chicos que encadenan tools sin inventar** (2°). Qcamp apunta a los dos:

1. Operación de back-office: gente leyendo tickets de balanza → agente on-device (OCR + tools + SQLite).
2. Tool use: `extract_remito` (sin IO) ≠ `save_remito` (INSERT). JSON tipado, kg inválido = 422, no alucinación persistida.
3. Inferencia **solo** QVAC (`@qvac/sdk` worker + `tetherto-qvac-sdk`). Cero cloud LLM.
4. Demo 3 min, airplane mode: upload → fila → `/resumen`. Greenfield (regla Aleph).

## Premios (desde track.md)

Pool hasta $2,000 USDt. $1,500 en dos premios de proyecto + $500 Vault Guardian (no es el nuestro).

| Premio | Qué piden | Cómo lo atacamos | Gap |
|--------|-----------|------------------|-----|
| 1° $1,000 — local agents that replace operations | Automatizar lectura de documentos + juicio, on-device | Remito / ticket de balanza del NOA: foto → kg/patente/fecha → totales | Foto **real** + boot `REMITO_QVAC=1` |
| 2° $500 — small models, hard tasks: tool use & reliability | 1–4B que encadene tools sin saltear, ignorar o inventar | `run_document_agent`: turno 1 solo extract, turno 2 save; si el 1B cambia el kg → no INSERT | Demo live de la cadena |
| Vault Guardian $500 | Jailbreak de un agente local con wallet WDK | **Fuera de este repo** | No mezclar |

Constraint del brief: *the craft is getting a 1–4B model to do real work reliably.*  
Por qué 1B + `OCR_LATIN` (no un 4B ni un VLM): [modelos.md](modelos.md).

Tether en Aleph también trae WDK y Pears. Este repo es **solo QVAC**. Pear (proyecto 2 del vault) no se toca acá.

## Usuario (no negociable para el pitch)

**Productor** (o capataz / contratista con su copia). No la balanza ni el acopio.

La planta suele tener sistema. El offline no es “la balanza no tiene Wi‑Fi”: es la **copia que se lleva el productor** y el **total del día**, que hoy es papel en la guantera. MVP en **notebook/PC** en la camioneta (`127.0.0.1`); celular nativo fuera de alcance. Hoja de pitch: [pitch.md](pitch.md).

## Por qué tickets de balanza (y no otro caso agro)

QVAC es fuerte en OCR + SLM + tools + offline. Es débil en satélite, ARCA y UIs cloud.

Documento = ticket de balanza (neto kg, patente, humedad, lote), no el remito AFIP de oficina.

Extensiones **después** del demo (misma SQLite): parte de cosecha, horómetro, bitácora por voz (STT). No pivotear en las 48 h.

## Contrato SDK que usamos

Docs canónicas: [JS/TS SDK](https://docs.qvac.tether.io/js-ts-sdk/), [OCR](https://docs.qvac.tether.io/ai-capabilities/ocr/), [Python](https://docs.qvac.tether.io/python-sdk/).

El worker es **el mismo** (`@qvac/sdk`). JS lo corre in-process. Python habla por `Client()` + `install-worker`.

| JS/TS (hablar así en el pitch) | Python (código real) |
|--------------------------------|----------------------|
| `loadModel({ modelSrc: OCR_LATIN })` | `load_model(t, model_src=OCR_LATIN)` |
| `loadModel({ modelSrc: LLAMA_3_2_1B_INST_Q4_0 })` | `load_model(t, model_src=LLAMA_3_2_1B_INST_Q4_0)` |
| `ocr({ modelId, image: path })` | `ocr_stream` + image `{type:"filePath","value": path}` |
| `completion({ history, tools })` | `completion(..., tools=...)` → `run.events` / `run.final` + `invoke()` |

Fachada del repo: `app/qvac_client.py` → `ocr(path)` y `complete(history, tools)`.

Modelos: `OCR_LATIN` (EasyOCR/CRAFT, `langList` oficial `en`; dígitos/patentes alcanzan) + Llama 3.2 1B Q4. No VLM como primario.

## Arquitectura (una frase)

Un proceso FastAPI en `127.0.0.1` orquesta; el worker QVAC corre al lado; tools validan e insertan en SQLite; HTMX degrada a form manual si el worker no levantó.

```
foto → disco → ocr() → completion(tools) → save_remito → fila / SUM(kg)
```

## Qué pulir (prioridad)

Ordenado para el resto del hackathon. Tachar al cerrar.

### P0 — demo creíble

- [ ] Primer boot `REMITO_QVAC=1` y confirmar banner `ocr_ready` / `llm_ready`
- [ ] Airplane mode real: cortar red y repetir upload → fila → `/resumen`
- [ ] Al menos **un** ticket de papel real (o foto de remito de campo), no solo `fixtures/tickets/*`
- [ ] Ensayo de 3 minutos en voz alta (problema NOA → foto → tools → totales)

### P1 — evidencia para Tether / DoraHacks

- [ ] Log de una corrida: load/unload, TTFT, tokens/s (JSON o CSV). El hackathon QVAC de junio lo pedía; acá suma
- [ ] Video ≤5 min + README ya existente
- [ ] One-liner + 3 bullets de impacto (privacidad, offline, kg del día)
- [ ] Submit DoraHacks lo hace una **persona** (riesgo Alto; no automatizar)

### P2 — producto, no track

- [ ] Otro tipo de papel (parte / horómetro) sobre las mismas tools
- [ ] STT bitácora (QVAC transcribe) si sobra tiempo
- [ ] No satélite, no ARCA, no Pear en este repo

## Pitch

Texto y persona: [pitch.md](pitch.md).

Frases del brief: *on-device*, *no data leaving the machine*, *1–4B doing real work*, *tool use without inventing an answer*.

Frases a evitar: “las balanzas no tienen internet”; “API de visión en la nube”; “fork de Zafra”.

## Fuera de este track

| Cosa | Dónde va |
|------|----------|
| Pear / mesh / triage | Proyecto 2 del vault — otro repo |
| WDK / wallets | Otro track Tether |
| Zafra (satélite, ARCA, padrones) | Producto aparte; no copiar |
| VitisTrust (RWA / chain) | Producto aparte; no copiar |

## Referencias

| Recurso | URL / path |
|---------|------------|
| Brief del track (vos) | [track.md](track.md) |
| Aleph 2026 | https://alephhackathon.crecimiento.build/ |
| Docs QVAC | https://docs.qvac.tether.io/js-ts-sdk/ |
| Propuesta vault | `~/Escritorio/projects/obsidian-vault/Propuestas Aleph Ago 2026.md` |
| Cómo correr | [README](../README.md) |

## Next step

Cerrar P0 (boot live + una foto real + ensayo 3 min). Después P1 (log + video). Submit = decisión humana.
