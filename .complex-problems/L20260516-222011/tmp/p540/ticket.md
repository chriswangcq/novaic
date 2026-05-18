# Delete unimplemented saga optional-step API

## Problem Definition

The saga substrate exposes `optional` parameters and a `SagaStep.optional` field, while the active DAG and task execution code do not implement optional-step behavior. `wake_finalize.py` uses `optional=True`, creating a misleading contract about `cortex_scope_end` failure handling.

## Proposed Solution

Remove the unused optional-step API instead of implementing a new compatibility behavior. Delete the `optional` field and constructor parameters from saga definitions, remove `optional=True` from wake_finalize, and adjust tests/documentation that referenced the old field. Then run focused saga/wake_finalize tests plus residue scans to confirm the stale surface is gone.

## Acceptance Criteria

- `SagaStep` no longer has an `optional` field.
- `SagaDefinition.add_task_step()` and `add_parallel_step()` no longer accept `optional`.
- `wake_finalize.py` no longer passes `optional=True`.
- No production `task_queue` code retains the stale `optional` saga-step API.
- Focused tests covering saga definition and wake_finalize lifecycle pass.

## Verification Plan

Run a focused `rg` scan for `optional` in `novaic-agent-runtime/task_queue`, then run tests that cover saga DAG construction, wake_finalize lifecycle, and saga/task execution contracts.

## Risks

- Some tests may have accidentally encoded the stale API.
- If any current caller relies on `optional=` outside wake_finalize, removal will reveal it at test or import time.
- The cleanup must not change wake_finalize dependency order or session finalize ownership.

## Assumptions

- The intended direction is AI-era cleanup: remove misleading compatibility residue rather than preserving unimplemented behavior.
- If optional-step behavior is genuinely needed later, it should be reintroduced as a deliberately designed and tested FSM/saga contract.
