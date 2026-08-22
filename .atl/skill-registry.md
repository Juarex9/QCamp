# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

**Project**: aleph-1  
**Generated**: 2026-08-22  
**Scan**: `~/.cursor/skills` (preferred) + `~/.config/opencode/skills` (duplicates skipped). No project-level skills. Skipped `sdd-*`, `_shared`, `skill-registry`.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| implementation, commit splitting, chained PRs, or keeping tests and docs with code | work-unit-commits | `/home/agustin/.cursor/skills/work-unit-commits/SKILL.md` |
| PR feedback, issue replies, reviews, Slack messages, or GitHub comments | comment-writer | `/home/agustin/.cursor/skills/comment-writer/SKILL.md` |
| writing guides, READMEs, RFCs, onboarding, architecture, or review-facing docs | cognitive-doc-design | `/home/agustin/.cursor/skills/cognitive-doc-design/SKILL.md` |
| PRs over 400 lines, stacked PRs, review slices | chained-pr | `/home/agustin/.cursor/skills/chained-pr/SKILL.md` |
| creating GitHub issues, bug reports, or feature requests | issue-creation | `/home/agustin/.cursor/skills/issue-creation/SKILL.md` |
| creating, opening, or preparing PRs for review | branch-pr | `/home/agustin/.cursor/skills/branch-pr/SKILL.md` |
| new skills, agent instructions, documenting AI usage patterns | skill-creator | `/home/agustin/.cursor/skills/skill-creator/SKILL.md` |
| Go tests, go test coverage, Bubbletea teatest, golden files | go-testing | `/home/agustin/.cursor/skills/go-testing/SKILL.md` |
| judgment day, dual review, adversarial review, juzgar | judgment-day | `/home/agustin/.cursor/skills/judgment-day/SKILL.md` |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### work-unit-commits
- Commit by deliverable behavior (fix, feature, migration, docs unit), never by file type (`models` then `services` then `tests`).
- Tests and user-visible docs belong in the same commit as the code they verify.
- Each commit must leave the repo coherent alone and be a candidate chained PR.
- Messages explain the outcome, not the file list; prefer Conventional Commits.
- If SDD forecasts >400 changed lines, group commits into chained PR slices before implementation.
- Follow `delivery_strategy`: auto-slice on `auto-chain` (this project), ask on `ask-on-risk`, require `size:exception` on over-budget `single-pr`.
- Rollback of one unit must not revert unrelated work.

### comment-writer
- Lead with the actionable point; do not recap the whole PR first.
- Warm and direct; 1–3 short paragraphs or a tight bullet list.
- Explain the technical why when asking for a change; comment only the highest-value issue.
- Match thread language. Spanish → Rioplatense/voseo (`podés`, `tenés`, `fijate`, `dale`).
- No em dashes; use commas, periods, or parentheses.
- Formula: observation/request → why (if needed) → concrete next action.

### cognitive-doc-design
- Lead with the decision, action, or outcome; context comes after.
- Progressive disclosure: happy path first, then details, edge cases, references.
- Prefer tables, checklists, examples, and templates over prose that must be remembered.
- Default shape: outcome title → one-paragraph why → Quick path → Details table → Checklist → Next step.
- PR docs: what to review first, what is out of scope, previous/next PR links when chained.
- Keep flat lists short; one decision per section.

### chained-pr
- Split PRs over 400 changed lines unless a maintainer accepts `size:exception`.
- One deliverable work unit per PR; tests/docs stay with the unit they verify; review target ≤60 minutes.
- ≤400 and focused → single PR. >400 independent slices → Stacked PRs to main. >400 must integrate first → Feature Branch Chain + draft tracker.
- Every child PR includes a dependency diagram with `📍` on the current PR.
- Feature Branch Chain: tracker is draft/no-merge; PR #1 targets tracker; later children target the immediate parent.
- Polluted diffs are base bugs: retarget/rebase until only the current unit appears. Do not mix strategies after choosing one.
- This project uses `delivery_strategy: auto-chain` — auto-slice without asking.

### issue-creation
- Use only when filing GitHub issues in repos that follow Gentle AI issue-first workflow (aleph-1 has no issue templates yet).
- Search duplicates first. Questions go to Discussions, not issues.
- Must use a template (bug report or feature request); blank issues are disabled in that workflow.
- New issues get `status:needs-review`; a maintainer must add `status:approved` before any PR.
- Bug: description, repro steps, expected vs actual, OS, agent, shell. Feature: problem, proposed solution, affected area.

### branch-pr
- Use when opening PRs in repos that follow Gentle AI checks. aleph-1 has no `.github/` templates yet — do not invent labels or block on missing issue workflow.
- Branch: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)/[a-z0-9._-]+$`.
- Commits: `type(scope): description` (Conventional Commits). Commits only if the human asks.
- When the Gentle AI workflow applies: PR body has `Closes/Fixes/Resolves #N` on an approved issue and exactly one `type:*` label.
- Do not add `Co-Authored-By` trailers. Never `git commit --no-verify` unless explicitly requested.

### skill-creator
- Create a skill only for reusable, non-trivial patterns; not one-offs or generic docs.
- Prefer `docs/skill-style-guide.md` if present; otherwise inline LLM-first rules.
- Required sections: Activation Contract, Hard Rules, Decision Gates, Execution Steps, Output Contract, References.
- `description`: one quoted line, trigger words first, ≤250 chars (target ≤160). No `Keywords` section.
- Body target 180–450 tokens (hard max 1000). Templates → `assets/`; edge cases → `references/` (local files only).
- Frontmatter must include `name`, `description`, `license`, `metadata.author`, `metadata.version`.
- Register project skills in `AGENTS.md`.

### go-testing
- Not the stack of this project (Python/pytest planned). Load only if Go tests appear.
- Table-driven tests with `t.Run(tt.name, ...)`; test behavior, not implementation trivia.
- Filesystem tests use `t.TempDir()` only; never a real home directory.
- Skip slow/external integration with `testing.Short()`.
- Bubbletea: test `Model.Update()` directly; `teatest` only for interactive flows.
- Golden files must be deterministic; update only via repo `-update`, then rerun without it.

### judgment-day
- Launch only when the user explicitly asks (Judgment Day, dual/adversarial review, `juzgar`).
- Inject the same Project Standards into both blind judges; never review the code yourself.
- Launch two judges in parallel; wait for both; never accept a partial verdict.
- `WARNING (real)` only if normal intended use can trigger it; otherwise INFO / theoretical.
- Ask before fixing Round 1 confirmed issues; re-launch both judges after any fix.
- Terminal states: `JUDGMENT: APPROVED` or `JUDGMENT: ESCALATED`. After 2 fix iterations, ask whether to continue.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | `/home/agustin/Escritorio/projects/aleph-1/AGENTS.md` | Index — product, stack, never-rules, SDD keys |
| aleph-harness | `/home/agustin/Escritorio/projects/aleph-1/.cursor/rules/aleph-harness.mdc` | Referenced by AGENTS.md — defaults, Alto pauses, agro stack |
| Vault guide | `/home/agustin/Escritorio/projects/obsidian-vault` | Product narrative source (outside repo) |
| Canonical note | `/home/agustin/Escritorio/projects/obsidian-vault/Propuestas Aleph Ago 2026.md` | Referenced by aleph-harness |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.

### aleph-1 conventions (inject on every code/SDD delegation)
- Greenfield only: never copy `zafra-ai` or `vitistrust`. Domain context from the vault is OK.
- Offline-only inference: `tetherto-qvac-sdk` local worker. Zero cloud LLMs.
- Stack (decided, not yet on disk): Python 3.11+, FastAPI `127.0.0.1`, SQLite, pytest, ruff, HTML/Jinja (no Next.js in MVP).
- Artifact store: `engram`. Delivery: `auto-chain`. Next change: `agro-qvac-local`. Do not create `openspec/`.
- No vault secrets (`Credenciales.md`) in code. Commits only if the human asks.
- Vertical is agro QVAC remitos. Changing vertical (Pear, etc.) is riesgo Alto.
