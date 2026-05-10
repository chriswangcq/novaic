# Cut Context Status Default Stack To SQLite

## Problem Definition

`context_status(include_usage=False)` still calls `_collect_active_stack`, so the runtime status stack remains file-walk authority. It must use the SQLite active-stack read adapter while preserving response shape and leaving `include_usage=True` semantic context status unchanged.

## Proposed Solution

- Import/use `read_active_stack_projection` in `context_status`.
- For default status, return `stack_depth`, `current_skill`, and `frames` from SQLite projection.
- Keep usage counters zero in the default path.
- Leave `include_usage=True` on `ContextEventReadModel`.
- Add tests that monkeypatch `_collect_active_stack` to fail while default status still succeeds from SQLite, and that `include_usage=True` still uses the event projection.

## Acceptance Criteria

- Default `context_status` reads frames from SQLite active-stack projection.
- Empty projection returns compatible empty stack response.
- `include_usage=True` behavior remains semantic ContextEvent backed.
- Tests prove default status no longer depends on `_collect_active_stack`.

## Verification Plan

- Update status tests.
- Run targeted status/lifecycle tests.
- Run full Cortex tests.

## Risks

- Existing tests may expect status to reflect file state immediately; Phase 3B write projection should make SQLite authoritative.

## Assumptions

- `scope_create`, `skill_begin`, `skill_end`, and finalize already keep the projection current.
