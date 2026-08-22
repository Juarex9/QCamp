# AGENTS.md — aleph-1

Máquinas primero. Narrativa y porqués viven en el vault Obsidian.

## Producto activo

Agente local QVAC para logística agrícola (remitos / tickets de balanza) en el NOA, 100% offline. Producto: **Qcamp**. **MVP: notebook/PC en `127.0.0.1`** — app móvil fuera de alcance.

## Stack

- Python 3.11+
- FastAPI en `127.0.0.1`
- SQLite
- `tetherto-qvac-sdk` + worker local
- Tests: pytest (cuando exista runner)

## Nunca

- Llamar LLMs en la nube
- Copiar código de `zafra-ai` o `vitistrust` a este repo
- Meter secretos del vault (`Credenciales.md`) en el código
- Pedir confirmación por defaults ya fijados en `.cursor/rules/aleph-harness.mdc`

## Artefactos SDD

Engram topic keys `sdd/agro-qvac-local/*`. No crear `openspec/` salvo pedido.

## Docs (jurado)

Índice en `docs/README.md`. Envío DoraHacks: `docs/submit.md` (humano; riesgo Alto).
