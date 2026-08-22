# Envío DoraHacks / Aleph

El jurado es **100% online y async**. Cierre del hackathon: domingo 12:00 ARG.
Juzgan desde las 13:00 (~4 h). No hace falta URL de Render ni Vercel.

El envío lo hace **una persona** del equipo (identidad / cuenta DoraHacks =
riesgo Alto). Este repo no automatiza el submit.

## Quick path

1. Repo público: https://github.com/Juarex9/QCamp
2. README de producto + este doc (permalinks y video).
3. Video local: airplane mode → upload → fila → `/resumen`.
4. En DoraHacks: pegar repo, video, 1 párrafo de pitch, permalinks.

## Qué pide el brief (must include)

| Requisito | Dónde está |
|-----------|------------|
| Repo público + README (qué, QVAC, modelos) | [README.md](../README.md) |
| Permalinks a la inferencia | Tabla abajo + README |
| Video demo local, punta a punta | Grabar; adjuntar en DoraHacks |
| Modelo, quant, máquina, latencia | [modelos.md](modelos.md) + anotar en el video |
| Setup desde clone limpio | README → Instalar |

## Permalinks (lo primero que miran)

Repo: `https://github.com/Juarex9/QCamp`

| Pieza | Link |
|-------|------|
| Load OCR + LLM | https://github.com/Juarex9/QCamp/blob/main/app/qvac_client.py#L117 |
| `ocr()` filePath | https://github.com/Juarex9/QCamp/blob/main/app/qvac_client.py#L180 |
| `complete()` + `toolCall.invoke()` | https://github.com/Juarex9/QCamp/blob/main/app/qvac_client.py#L216 |
| Agente extract → save | https://github.com/Juarex9/QCamp/blob/main/app/qvac_client.py#L257 |
| `extract_remito` (sin IO) | https://github.com/Juarex9/QCamp/blob/main/app/tools.py#L181 |
| `save_remito` (INSERT + gate kg) | https://github.com/Juarex9/QCamp/blob/main/app/tools.py#L226 |
| HTTP foto → agente | https://github.com/Juarex9/QCamp/blob/main/app/main.py#L443 |

Pegá estos links en el campo de “QVAC integration” de DoraHacks.

## Texto corto para el formulario

> Qcamp es la libreta del productor en el notebook: foto del ticket de
> balanza → OCR_LATIN + Llama 3.2 1B Q4 con tools (`extract_remito` →
> `save_remito`) → SQLite local → total del día. Si el 1B cambia el kg,
> no hay INSERT. Sin API keys; los kg no salen del equipo. Demo en
> modo avión.

## Guion de video (~90 s)

Grabar en el **notebook**, no en un deploy.

1. Mostrar airplane mode (o desconectar Wi-Fi).
2. Terminal: `REMITO_QVAC=1 make demo`. Banner `ocr_ready=true` `llm_ready=true`.
3. Abrir http://127.0.0.1:8000 → `/app`.
4. Subir `fixtures/tickets/remito-soja-tucuman.png` (y, si hay, **una foto real**).
5. Mostrar extract; confirmar o editar; fila en la tabla.
6. `/resumen` con el total.
7. Decir en voz: modelo 1B Q4, OCR separado, dos tools, kg inventado no se guarda.
8. Si el modelo falla: **dejarlo** y editar a mano. El brief premia honestidad.

Anotar en una slide o en la descripción del video:

| Campo | Completar en la grabación |
|-------|---------------------------|
| Máquina | (ej. ThinkPad, 16 GB RAM, Linux) |
| Latencia OCR | ___ s |
| Latencia 2 turnos LLM | ___ s |
| Foto extra (no fixture) | sí / no |

## Checklist antes de submit

- [ ] `REMITO_QVAC=1` corrió al menos una vez con banner en `true`
- [ ] Video muestra localhost, no Render
- [ ] README no promete cloud inference
- [ ] Permalinks abren las líneas de `qvac_client.py` / `tools.py`
- [ ] Pitch: productor + notebook, no “app en el celular”
- [ ] Vault Guardian **no** está mezclado en el proyecto
- [ ] Identidad de equipo / DoraHacks: lo carga un humano

## Qué no enviar como “la demo”

- Landing de Vercel sin backend (botón muerto).
- Render con `ocr_ready=false` presentado como agente QVAC.
- Un solo cherry-pick si podés mostrar un segundo input (foto real o fixture distinto).

## Next step

Correr local, grabar, pegar en DoraHacks. Detalle de premios:
[cobertura.md](cobertura.md). Brief: [qvac-track.md](qvac-track.md).
