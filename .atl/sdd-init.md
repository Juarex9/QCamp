# sdd-init/aleph-1

**Project**: aleph-1
**Detected**: 2026-08-22
**Persistence**: engram
**Delivery strategy**: auto-chain
**strict_tdd**: false

## What
Greenfield SDD bootstrap for aleph-1 (hackathon Aleph 22–23 Aug 2026). Repo has git + `AGENTS.md` + `.cursor/rules/`; no application code, no test runner, no quality tools, no hooks.

## Why
Cache stack, product, and testing capabilities so later SDD phases do not reopen decided defaults.

## Where
Workspace: `/home/agustin/Escritorio/projects/aleph-1`
On disk: `AGENTS.md`, `.cursor/rules/` (SDD harness + `aleph-harness.mdc`), `.git`. Absent: `pyproject.toml`, `pytest.ini`, `package.json`, `ruff.toml`, `openspec/`, `.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`, `.githooks/`, `.gitignore`.

## Stack (planned, not on disk)
- Python 3.11+
- FastAPI on `127.0.0.1`
- SQLite
- `tetherto-qvac-sdk` + local worker
- Tests: pytest (when apply scaffolds)
- Lint/format: ruff (planned)
- UI: HTML/Jinja mínima (no Next.js in 48h MVP)

## Product
- Active vertical: agro QVAC remitos / tickets de balanza, NOA, 100% offline
- Vault guide: `/home/agustin/Escritorio/projects/obsidian-vault`
- Canonical note: `Propuestas Aleph Ago 2026.md`
- Hackathon: Aleph 22–23 Aug 2026, greenfield only (no copy from zafra-ai/vitistrust)
- Next change name: `agro-qvac-local`
- Inference: local QVAC only (OCR + LLM 1–4B + tool use). Zero cloud LLM
- Sync/P2P/Postgres: out of MVP

## Never
- Cloud LLMs
- Copy code from `zafra-ai` or `vitistrust`
- Vault secrets (`Credenciales.md`) in code
- Create `openspec/` unless the user asks
- Confirm defaults already in `.cursor/rules/aleph-harness.mdc`

## Strict TDD
`strict_tdd: false` — no test runner on disk. Planned runner `pytest` when apply scaffolds the project. Do not enable Strict TDD until a real runner exists.

## Persistence
- artifact_store.mode: engram
- Topic keys: `sdd-init/aleph-1`, `sdd/aleph-1/testing-capabilities`, `sdd/agro-qvac-local/*`
- Skill registry: `.atl/skill-registry.md`

## Learned
Engram MCP cwd is `$HOME` and auto-detects project `cosillas`. `project: aleph-1` was rejected (`unknown_project`). Observations were saved without project (auto → `cosillas`). This file is the recovery copy. Downstream retrieval should search topic keys without a project filter and also read `.atl/` if Engram project filter misses aleph-1.

## Engram IDs (saved under project `cosillas`)
- `sdd-init/aleph-1`: observation id 155
- `sdd/aleph-1/testing-capabilities`: observation id 156
- `skill-registry`: observation id 157
