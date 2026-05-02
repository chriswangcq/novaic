# PR-182B — Remove unused Cortex compatibility helpers

Status: `[closed]` — 2026-05-03

## Finding

Cortex still has compatibility helpers/comments that describe old names or old call shapes:

- `_drop_skill_lock` alias over `_drop_scope_lock`
- `StepTree.get_scope_nodes()` retained for hypothetical trace callers, but no active caller remains
- `tool_schemas.py` says it is kept for backward-compatible imports even though it is the current Cortex projection of Common schemas

## Scope

- Remove `_drop_skill_lock` alias and call `_drop_scope_lock` directly.
- Remove unused `StepTree.get_scope_nodes()`.
- Rewrite tool schema wording to describe the current boundary instead of compatibility.
- Add focused tests/guard through existing Cortex suites.

## Tests

- Cortex focused tests covering DFS/context and boundary.
- Full Cortex test suite.

## Deployment / Git

- Deploy Cortex.
- Commit/push `novaic-cortex` and root docs/pointer.

## Closure

- Removed `_drop_skill_lock` alias and now call `_drop_scope_lock` directly.
- Removed unused `StepTree.get_scope_nodes()`.
- Reworded Cortex tool schema module as a current Common-schema projection, not a compatibility import surface.
- Reworded queue scope lookup comments to describe the current resolver boundary.
- Updated active docs and PR-39 historical note so old helper retention is not presented as current architecture.
- Tests:
  - `novaic-cortex`: `PYTHONPATH=.:../novaic-common pytest -q tests/test_context_engine_dfs.py tests/test_pr75_proxy_boundary.py tests/test_pr76_boundary_guard.py`
  - `novaic-cortex`: `PYTHONPATH=.:../novaic-common pytest -q`
- Deploy/smoke:
  - `./deploy cortex`
  - remote Cortex `/health` and `/ready` healthy
