# Use Workspace lifecycle projections for hook tests

## Problem Definition

Hook tests use removed `Cortex.scope_create/end` methods even though hook callbacks are emitted by Workspace scope lifecycle/projection methods. This keeps tests attached to a deleted runtime abstraction.

## Proposed Solution

- Replace hook test setup with `make_workspace_with_store(..., hooks=hooks)` where runtime tool methods are not needed.
- Call `workspace.create_scope_projection(...)` and `workspace.archive_root_scope_projection(...)` for hook create/archive cases.
- Remove runtime scope lifecycle metric assertions from hook tests; those belong to P053.
- Keep assertions for hook firing, warning behavior, and callback isolation.

## Acceptance Criteria

- `tests/test_hooks_metrics.py` no longer calls runtime lifecycle helpers.
- Hook-focused cases in `tests/test_hooks_limits.py` no longer call runtime lifecycle helpers.
- Focused hook tests pass.

## Verification Plan

- Static scan the two hook test files for `.scope_create(` and `.scope_end(`.
- Run `pytest tests/test_hooks_metrics.py tests/test_hooks_limits.py -q` or the subset that remains hook-focused after metric cleanup.

## Risks

- `tests/test_hooks_limits.py` also contains metric-continuity cases that may still need P053 cleanup.

## Assumptions

- Workspace projection methods are the correct component-level surface for hook emission during event-source transition.
