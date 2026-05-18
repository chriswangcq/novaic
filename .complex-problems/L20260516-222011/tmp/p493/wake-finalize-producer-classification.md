# P493 wake_finalize producer classification

## Raw Evidence

- Raw search: `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-raw.txt` (`258` lines)
- File list: `.complex-problems/L20260516-222011/tmp/p493/wake-finalize-producer-files.txt`

## Production Producers

### Explicit stack provider

- `novaic-agent-runtime/task_queue/contracts/react_actions.py:392-425`
  - `build_trigger_finalize_payload()` sets `remaining_stack` from `_remaining_stack_snapshot(decision)`.
  - It also still sends `stack_depth_at_finalize` and `stack_known_at_finalize`, but those are redundant once `remaining_stack` is mandatory.

### Conditional / missing provider

- `novaic-agent-runtime/queue_service/saga_repo.py:1278-1312`
  - `_build_wake_finalize_compensation_effect()` creates a `wake_finalize` saga when a wake saga fails.
  - It copies `remaining_stack` only if it already exists in the failed saga context.
  - Failed wake saga contexts such as `react_think` do not necessarily have `remaining_stack`, so this producer is missing an explicit stack contract for compensation.
  - P494 should fix this producer by adding an explicit unknown-stack snapshot instead of relying on `wake_finalize.py` fallback.

### Recovery archive producer, not wake_finalize producer

- `novaic-agent-runtime/queue_service/session_recovery.py:137-183`
  - Builds a direct `CORTEX_SCOPE_END` recovery archive effect, not a `wake_finalize` saga.
  - It currently synthesizes stack diagnostics when recovery metadata lacks `remaining_stack`.
  - This belongs to P491, not P494.

## Adapter / Dispatcher Boundaries

- `novaic-agent-runtime/queue_service/session_outbox.py:128-193`
  - Publishes session-created wake sagas from durable outbox context. It does not itself construct finalize context.
- `novaic-agent-runtime/queue_service/saga_repo.py:1267-1274`
  - Publishes saga outbox effects; creation is a generic saga outbox adapter.

## Test Fixtures

- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
- `novaic-agent-runtime/tests/test_pr311_saga_compensation_outbox_cutover.py`
- `novaic-agent-runtime/tests/test_finalize_summary_boundary.py`

These tests intentionally exercise finalize, compensation, and contract boundaries.

## Required Next Change

P494 should:

- Make `wake_finalize.py` require `remaining_stack` to be a dict.
- Update `_build_wake_finalize_compensation_effect()` to include an explicit unknown-stack snapshot when the failed saga context lacks `remaining_stack`.
- Remove redundant legacy fallback fields from the finalizer contract if no longer needed.
