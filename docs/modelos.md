# Por qué estos modelos

Usamos **dos** modelos QVAC, no uno. El LLM no “mira” la foto. El OCR lee el papel; el 1B solo estructura y encadena tools.

| Rol | Constante QVAC | Qué es | Por qué este y no otro |
|-----|----------------|--------|------------------------|
| Visión → texto | `OCR_LATIN` | Pipeline OCR (EasyOCR/CRAFT), no un LLM | El track lista OCR como tarea nativa. Un 1–4B **no** es un VLM fiable. Separar visión de juicio es el truco para que el modelo chico haga trabajo real. |
| Agente / tools | `LLAMA_3_2_1B_INST_Q4_0` | Llama 3.2 **1B** instruct, quant **Q4_0** | El brief del track: *the craft is getting a 1–4B model to do real work reliably*. 1B es el piso de esa banda: si el agente funciona acá, el premio 2° (tool use) queda demostrado. |

Código: `app/qvac_client.py` (`tools: True`, `temp: 0.1`, `ctx_size: 2048`).

## Quick path (qué decirle al jurado)

1. El brief **prohíbe** el atajo de un modelo grande en la nube. El craft es el modelo chico.
2. Elegimos el **1B oficial del SDK** (es el ejemplo de `loadModel` + tools en las docs de QVAC), no un 8B/70B ni un endpoint OpenAI remoto.
3. Q4_0 entra en una notebook de campo: menos RAM, primer load viable en 48 h, sigue siendo on-device.
4. `INST` = instruct + tool calling. Sin eso el 1B no encadena `extract_remito` → `save_remito`.
5. La confiabilidad **no** la pedimos al modelo solo: schema Pydantic, `tonelaje_kg > 0` o no hay INSERT, el host no invoca `save` si extract no trajo kg. Eso es “without inventing an answer”.

## Alineado al brief ([track.md](track.md))

| Frase del track | Decisión de modelo |
|-----------------|--------------------|
| *no cloud, no API keys, no data leaving the machine* | Worker local. Remito/kg/patente no salen del host. |
| *1–4B model to do real work reliably* | 1B, no 4B “para que sea más fácil”. El trabajo real es extraer un remito y persistirlo. |
| *back-office… reading documents and making judgment calls* | OCR lee; el 1B decide qué fields van a qué tool. El operador confirma/edita. |
| *chain tools… without inventing an answer* | Dos tools, extract ≠ save, gate de kg en `QvacRuntime.complete`. |
| OpenAI-compatible en localhost | Existe en QVAC; **no** lo usamos como camino principal. El premio 2° pide tools nativas, no un wrapper chat. |

## Qué descartamos (y por qué)

| Alternativa | Por qué no |
|-------------|------------|
| Solo VLM / attachments en el LLM | Los 1–4B del track no son buenos en visión. No demuestra el addon OCR. |
| Cloud OCR o GPT | Rompe *no data leaving the machine* y el track entero. |
| Llama/Qwen 3–4B o 8B | Más calidad, menos “craft”. Docs QVAC: *larger models offer better quality at the expense of latency*. En 48 h y en el campo, el 1B Q4 es el punto. |
| Qwen3 600M (también en el SDK) | Más chico que 1B; peor tool calling. El piso del brief es 1B. |
| DocTR (`OCR_DOCTR`) | Otro OCR oficial. Latin/CRAFT cubre dígitos y patentes de un ticket de balanza. |
| Endpoint OpenAI-compat como único API | Esconde el tool use. Lo guardamos como compat, no como arquitectura. |

## Cómo se ve en el flujo

```
foto → OCR_LATIN (texto + confidence)
     → Llama 3.2 1B Q4 + tools
        1. extract_remito  (sin IO; arma el JSON)
        2. save_remito     (solo si kg > 0; INSERT)
     → SQLite / HTMX
```

Si el 1B se inventa 12 toneladas, `save_remito` o el gate del runtime lo paran. El operador ve `raw_ocr` y edita. Eso es el juicio humano que el 1° premio pide *además* del agente.

## Hardware y latencia (completar en el video)

| Campo | Valor |
|-------|--------|
| Modelo LLM | Llama 3.2 1B Instruct, Q4_0 (`LLAMA_3_2_1B_INST_Q4_0`) |
| OCR | `OCR_LATIN` (CRAFT / Latin recognizer) |
| RAM de modelo (guía del brief) | 1B Q4 ≪ 4 GB; techo 4B Q4 ≈ 4 GB |
| Máquina de la demo | anotar en [submit.md](submit.md) al grabar |
| Latencia OCR / 2 turnos | **no medida en repo** — decirla en el video |

## Gap (no es la elección del modelo)

La elección está alineada. Falta **probarla en vivo**: pesos de `OCR_LATIN` + Llama todavía no se bajaron; pytest mockea el worker. Hasta `REMITO_QVAC=1` + una foto (fixture y, mejor, una real), el argumento de “1B fiable” es arquitectura, no evidencia.

Envío: [submit.md](submit.md). Mapa a premios: [cobertura.md](cobertura.md).
