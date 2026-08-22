## Testing Capabilities

**Project**: aleph-1
**Strict TDD Mode**: disabled
**strict_tdd**: false
**Detected**: 2026-08-22

Reason: no test runner on disk (no `pyproject.toml`, `pytest.ini`, `package.json` test script, `Makefile`, or `go.mod`). Planned runner `pytest` when `sdd-apply` scaffolds the project. Do not inject Strict TDD until a real runner exists.

### Test Runner
- Command: `—`
- Framework: none detected
- Planned: `pytest` (`pytest` / `python -m pytest`)

### Test Layers
| Layer | Available | Tool |
|-------|-----------|------|
| Unit | ❌ | — (planned: pytest) |
| Integration | ❌ | — (planned: pytest + FastAPI TestClient / httpx) |
| E2E | ❌ | — |

### Coverage
- Available: ❌
- Command: `—`
- Planned: `pytest --cov` when pytest-cov is added

### Quality Tools
| Tool | Available | Command |
|------|-----------|---------|
| Linter | ❌ | — (planned: `ruff check`) |
| Type checker | ❌ | — |
| Formatter | ❌ | — (planned: `ruff format`) |

### Pre-commit
- Enabled: no
- Tool: none
- Command: `—`
- Staged-only command: `—`

Detected absent: `.pre-commit-config.yaml`, `.husky/`, lint-staged (`package.json`), `lefthook.yml`, `.githooks/`. Only git sample hooks under `.git/hooks/*.sample` (not active).
