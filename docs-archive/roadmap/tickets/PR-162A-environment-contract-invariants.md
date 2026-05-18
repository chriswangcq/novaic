# PR-162A — Environment Contract and Invariant Test Matrix

> Historical ticket archive: this closed ticket predates the PR-229 chat
> projection cleanup. `message_lifecycle.json` references here are archaeology,
> not current architecture.

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-162 |
| Repos | `novaic-common`, docs |
| Depends on | PR-162 analysis |

## Goal

Create the shared Environment contract before any storage or runtime cutover.

This ticket is intentionally non-invasive: define vocabulary, notification lifecycle, event kinds, resource-ref shape, and ownership exclusions. Add tests so later services cannot silently redefine Environment as memory, prompt assembly, Cortex scope state, or business domain truth.

## Implementation Plan

1. Add `common/contracts/environment.json`.
2. Add `common/contracts/environment.py` loader/helpers.
3. Add tests proving:
   - notification states and allowed transitions are explicit;
   - Environment-owned concepts are present;
   - excluded concepts such as memory/profile/prompt/Cortex summary are not accidentally owned;
   - required resource-ref fields are stable.
4. Update PR-162 evidence when tests pass.

## Tests

- Unit: `PYTHONPATH=. pytest tests/test_environment_contract.py` — 5 passed.
- Broader contract smoke: `PYTHONPATH=. pytest tests/test_environment_contract.py tests/test_message_lifecycle_contract.py` — 7 passed.
- Full common smoke: `PYTHONPATH=.:../novaic-agent-runtime pytest` — 108 passed.

## Deploy / Git

- Deploy: `./deploy services` — all backend services restarted successfully.
- Production smoke: `PYTHONPATH=/opt/novaic/services/novaic-common python3 -c ...` returned `['claimed', 'failed', 'pending', 'processed']`.
- Git: `novaic-common` commit `aa35585 feat(common): add environment contract`.

## Done Criteria

- [x] Contract and tests exist.
- [x] Tests pass locally.
- [x] Root roadmap documents link the small ticket.
- [x] Commit/deploy evidence is added before closing.

## Evidence

- Files added:
  - `common/contracts/environment.json`
  - `common/contracts/environment.py`
  - `tests/test_environment_contract.py`
- No live runtime behavior was changed by this ticket.
