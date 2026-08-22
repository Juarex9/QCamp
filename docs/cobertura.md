# Cómo Qcamp cubre el track QVAC

El brief oficial está en [qvac-track.md](qvac-track.md). Acá: qué
construimos contra cada premio, sin inflar.

## Quick path

Qcamp automatiza **leer tickets de balanza y anotar kg** (1°) con un
**1B que encadena dos tools y no persiste un kg inventado** (2°).

## Premio 1° — agentes locales de operaciones

El brief: gente leyendo documentos, spotting discrepancies, escalating.
Datos que no pueden ir a un API de terceros.

| Pedido del track | En Qcamp |
|------------------|----------|
| Back-office on-device | Productor / capataz: copia del ticket → total del día, sin nube |
| OCR de fotos / scans | `OCR_LATIN` sobre PNG del ticket |
| Structured output | JSON tipado (`RemitoIn` / `extract_remito`) → SQLite |
| Humano audita en 5 s | Formulario + `raw_ocr` + confirmar / editar |
| Honestidad ante duda | `needs_judgment`; kg inventado no se guarda; humedad basura → 422 |
| Inputs sucios | Fixtures sintéticos hoy; el brief pide **también** foto real / mala luz |

No hacemos: conciliación contra OC / extracto bancario, credit risk,
categorización de merchants. El documento de campo del NOA **es** el
ticket de balanza, no la factura AFIP.

## Premio 2° — tool use y 1–4B fiable

El brief: el 1–4B no debe olvidar un paso, ignorar el tool, ni inventar.

| Pedido del track | En Qcamp |
|------------------|----------|
| Multi-step tools | Turno 1 `extract_remito`; turno 2 `save_remito` con el JSON del 1 |
| Usar lo que volvió el tool | Host mergea campos locked (`fecha`, `patente`, `tonelaje_kg`) |
| No inventar | Si el save cambia el kg del extract → `invented`, sin INSERT |
| Validation / structured output | Pydantic + `tonelaje_kg > 0` + parser regex del texto OCR |
| Evidencia N corridas | **Pendiente** — pytest cubre gates con worker mockeado |

El HTTP OpenAI-compat de QVAC **cuenta** como inferencia local. No es
nuestro camino: esconde el tool use que el 2° premio pide ver.

## Must-use (tech requirements)

| Regla | Cumplimos |
|-------|-----------|
| QVAC como capa de inferencia | `tetherto-qvac-sdk` + worker `@qvac/sdk` |
| Todo local; cloud LLM = descarte | Bind `127.0.0.1`; `REMITO_QVAC=0` no llama APIs |
| Integración QVAC escrita este weekend | Greenfield. No hay capa cloud “y QVAC al lado” |
| No VisionPsy / image gen | Solo OCR + text + tools |
| No copiar Zafra / VitisTrust | Código nuevo en este repo |

## Qué nos puede descartar (el brief es explícito)

- README que describe capacidades que no corren.
- Demo de **una** foto limpia y nada más.
- Métodos de SDK inventados (revisar `qvac_client.py` contra docs oficiales).
- “QVAC bolted on” junto a un LLM en la nube — no es el caso.

## Vault Guardian

Challenge aparte ($500 split). No es Qcamp. No va en el video del proyecto.

## Next step

[submit.md](submit.md) para el envío. [modelos.md](modelos.md) para el
porqué del 1B.
