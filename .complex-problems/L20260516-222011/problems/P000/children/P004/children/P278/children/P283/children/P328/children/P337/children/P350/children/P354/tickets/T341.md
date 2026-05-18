# Subagent finalize status identity guard

## Problem Definition

`task_queue/handlers/subagent_handlers.py::handle_subagent_set_sleeping()` and `handle_subagent_set_completed()` mutate Business subagent status from finalize-related tasks using only `agent_id` and `subagent_id`. That is too coarse for a wake/session lifecycle mutation: a stale finalize DAG can still target the same subagent after a newer wake has already advanced, and the current handler shape has no required wake/session identity before writing `sleeping` or `completed`.

The current wake-finalize DAG also performs subagent status mutation before `session_ended`, so the authoritative session generation guard can run too late to protect Business status.

## Proposed Solution

1. Inspect the exact wake-finalize task order and the subagent status payload builders in `task_queue/sagas/wake_finalize.py`.
2. Make subagent terminal-status payloads carry explicit finalize identity:
   - `scope_id`
   - positive `session_generation`
   - existing `agent_id` and `subagent_id`
   - any existing finalize audit metadata already available without reviving `last_scope_id`.
3. Make `handle_subagent_set_sleeping()` and `handle_subagent_set_completed()` reject missing/non-positive finalize identity before calling `business_client.entity_update()`.
4. Reorder the wake-finalize DAG so the session-generation-owned `session_ended` transition gates subagent terminal status mutation. A stale generation must fail before Business status is changed.
5. Add regression tests for:
   - generated finalize status payloads include positive generation and current scope identity.
   - missing or zero generation rejects before Business mutation.
   - stale/failing `session_ended` prevents downstream subagent status mutation through task ordering.
   - no `last_scope_id` compatibility field is reintroduced.

## Acceptance Criteria

- `set_subagent_sleeping` and `set_subagent_completed` handlers do not mutate Business status without explicit positive `session_generation` and wake scope identity.
- The wake-finalize DAG places `session_ended` before Business subagent terminal-status tasks, or an equivalent proof-backed generation guard exists before the status mutation.
- Tests cover missing identity, non-positive generation, payload propagation, and finalize task ordering.
- No compatibility path treats missing generation as zero, optional, or otherwise valid.
- No legacy `last_scope_id` status payload path is reintroduced.

## Verification Plan

- `python3 -m py_compile task_queue/handlers/subagent_handlers.py task_queue/sagas/wake_finalize.py`
- Focused pytest:
  - `tests/test_pr43_last_scope_wiring.py`
  - `tests/test_runtime_tool_path_contract.py`
  - `tests/test_pr254_finalize_ownership.py`
  - `tests/test_pr311_saga_compensation_outbox_cutover.py`
  - `tests/integration/test_saga_dag_refactor.py`
- Source guard over `task_queue/handlers/subagent_handlers.py` and `task_queue/sagas/wake_finalize.py` for:
  - `last_scope_id`
  - `session_generation.*or 0`
  - `ctx.get("session_generation") or 0`

## Risks

- If the DAG engine does not preserve optional/gating semantics the way the saga builder implies, the implementation must inspect the executor and either fix the graph conversion or split a child ticket instead of assuming task order is enough.
- If Business `entity_update()` rejects extra audit fields, keep identity validation in runtime payload/handler and do not write unknown schema fields into Business.

## Assumptions

- P349 and P353 already make normal finalize contexts carry positive `session_generation`.
- Recovery/compensation finalize identity is covered by P351; this ticket should not add a loose fallback for those paths.
