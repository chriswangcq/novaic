# Migrate hooks and metrics tests off runtime lifecycle helpers

## Problem Definition

Hook and metric tests still call removed runtime lifecycle helpers. The hook behavior itself still belongs to Workspace lifecycle projections, but runtime `CortexMetrics.scopes_created/scopes_archived` was only incremented by the removed runtime helpers and is now obsolete coverage.

## Proposed Solution

- Rewrite hook callback tests to call Workspace projection methods directly where the hook is emitted by Workspace.
- Remove or replace expectations for `cortex.metrics.scopes_created` and `cortex.metrics.scopes_archived` because runtime no longer owns structural lifecycle.
- Keep runtime metrics coverage for remaining runtime-owned behavior:
  - `skills_installed`,
  - `total_files_read`,
  - `total_files_written`,
  - shell metrics.
- Update test names/docstrings to avoid implying runtime lifecycle ownership.
- If no production code increments scope lifecycle metrics anymore, remove those fields from `CortexMetrics` and adjust chaos/metrics tests accordingly only if this can be done within the focused scope.

## Acceptance Criteria

- `tests/test_hooks_metrics.py`, `tests/test_hooks_limits.py`, and `tests/test_wave4_metrics.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Hook tests still verify callback success/failure isolation through the component that emits those hooks.
- Runtime metrics tests only assert metrics that runtime still owns.
- Focused hooks/metrics tests pass.

## Verification Plan

- Static scan:
  - `rg -n "\\.scope_create\\(|\\.scope_end\\(" tests/test_hooks_metrics.py tests/test_hooks_limits.py tests/test_wave4_metrics.py`
- Run focused tests:
  - `pytest tests/test_hooks_metrics.py tests/test_hooks_limits.py tests/test_wave4_metrics.py -q`

## Risks

- Scope lifecycle metrics may require broader cleanup if `CortexMetrics` still exposes dead fields.
- Workspace hook tests must not accidentally reintroduce runtime lifecycle helpers.

## Assumptions

- Workspace hook emission remains a valid projection concern during the event-source transition.
- Runtime structural lifecycle metrics are obsolete once runtime lifecycle helpers are removed.
