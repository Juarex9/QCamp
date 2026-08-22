# Qcamp Specification (agro-qvac-local)

## Outcome

Foto → OCR local → JSON tipado → fila → totales, sin internet. Juez verifica inferencia local, tool use y JSON determinista.

## Actors

| Actor | Goal |
|-------|------|
| Operador de campo | Subir foto, confirmar/editar, guardar |
| Contratista | Listar remitos y ver totales |
| Juez de demo | Airplane mode, tools, JSON determinista <3 min |

## Non-goals

The system MUST NOT implement P2P, cloud LLM/sync, mobile, Postgres, Pear, Zafra, auth, or non-localhost deploy.

---

# remito-ingest Specification

## Purpose

Cargar foto, extraer JSON y persistir tras validación o confirmación.

## Requirements

### Requirement: Upload remito image

The system MUST accept a remito image on localhost, store it, and MUST NOT send it off-host.

#### Scenario: Upload image

- GIVEN Qcamp on `127.0.0.1`
- WHEN the operador uploads a remito photo
- THEN it SHALL persist `image_path` and MUST NOT transmit off-host

### Requirement: OCR then extract remito

The system MUST run local OCR and invoke `extract_remito`. It MUST return typed JSON (`fecha`, `patente`, `tonelaje_kg`, `origen`, `destino`, `producto`, `humedad`) and MUST NOT persist. The system MUST persist `raw_ocr` each ingest.

#### Scenario: OCR and extract

- GIVEN a stored remito image
- WHEN OCR completes and the LLM calls `extract_remito`
- THEN it SHALL return typed JSON, persist `raw_ocr`, and MUST NOT insert

#### Scenario: Persist raw_ocr

- GIVEN noisy or incomplete OCR
- WHEN extract runs
- THEN the system MUST persist `raw_ocr` and SHOULD show it to the operador

### Requirement: Confirm or edit extract

The system MUST show `raw_ocr` plus an edit form if extract is incomplete or the operador disagrees.

#### Scenario: Confirm or edit

- GIVEN extracted JSON plus `raw_ocr`
- WHEN the operador edits fields and confirms
- THEN save SHALL use confirmed values and MUST keep `raw_ocr`

### Requirement: Save remito after validation

The system MUST persist only via `save_remito`, which MUST validate types and INSERT. Invalid extract MUST NOT INSERT.

#### Scenario: Save remito

- GIVEN valid confirmed typed JSON
- WHEN `save_remito` is invoked
- THEN it SHALL INSERT one row and the UI SHALL show it

#### Scenario: Reject invalid extract

- GIVEN extract fails type/numeric validation (non-numeric `tonelaje_kg`)
- WHEN `save_remito` is invoked
- THEN it MUST NOT INSERT and MUST return `raw_ocr` plus the edit form

---

# remito-query Specification

## Purpose

Listar remitos y totales.

## Requirements

### Requirement: List remitos

The system MUST expose `list_remitos` and a UI list.

#### Scenario: List remitos

- GIVEN one or more remitos saved
- WHEN the contratista opens the list
- THEN it SHALL show structured fields including session remitos

### Requirement: Summarize harvest totals

The system MUST expose `summarize_harvest` as `SUM(tonelaje_kg)`. The system MAY filter by `fecha`.

#### Scenario: Summarize totals

- GIVEN remitos with known `tonelaje_kg`
- WHEN the contratista or juez requests totals
- THEN it SHALL return `SUM(tonelaje_kg)` and the UI SHALL show it

---

# local-qvac-runtime Specification

## Purpose

OCR+LLM en localhost, tools on, JSON determinista, cero red.

## Requirements

### Requirement: Local inference only

The system MUST run OCR and LLM on a local QVAC worker, bind `127.0.0.1`, and MUST NOT call cloud LLMs.

#### Scenario: Airplane mode

- GIVEN the host has no internet
- WHEN the juez uploads a remito and requests totals
- THEN ingest and query SHALL complete locally with no cloud LLM or sync

### Requirement: Tool use and deterministic JSON

The LLM MUST run with tools enabled. Ingest MUST use `extract_remito` then `save_remito` as separate tools. Arguments and saved fields MUST be deterministic typed JSON.

#### Scenario: Tool use plus deterministic JSON

- GIVEN the local QVAC worker is ready
- WHEN the LLM processes OCR text
- THEN it SHALL call `extract_remito` with typed JSON and `save_remito` only after valid extract or confirm
- AND the saved row MUST match confirmed JSON types
