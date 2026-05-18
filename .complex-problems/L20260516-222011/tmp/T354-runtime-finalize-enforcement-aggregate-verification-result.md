# T354 Result: Runtime Finalize Enforcement Aggregate Verification

## Execution

Compiled runtime finalize/session identity modules:

```bash
python3 -m py_compile \
  task_queue/contracts/session_generation.py \
  task_queue/contracts/react_think.py \
  task_queue/contracts/react_actions.py \
  task_queue/sagas/wake_finalize.py \
  task_queue/handlers/cortex_handlers.py \
  task_queue/handlers/session_handlers.py \
  task_queue/handlers/runtime_handlers.py \
  queue_service/session_repo.py \
  queue_service/session_fsm.py \
  queue_service/session_recovery.py \
  queue_service/session_outbox.py \
  queue_service/saga_repo.py \
  queue_service/session_rebuild.py
```

Ran focused aggregate test suite:

```bash
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_runtime_explicit_contracts.py \
  tests/test_pr43_last_scope_wiring.py \
  tests/test_runtime_tool_path_contract.py \
  tests/test_pr254_finalize_ownership.py \
  tests/test_finalize_summary_boundary.py \
  tests/test_scope_end_environment_notifications.py \
  tests/test_pr65_agent_root_scope.py \
  tests/test_pr67_wake_child_scope.py \
  tests/test_pr70_explicit_skill_summary_only.py \
  tests/test_pr165c_notification_lifecycle_guardrails.py \
  tests/test_pr186_runtime_main_path_acceptance.py \
  tests/test_pr234_tool_logical_failure.py \
  tests/test_pr234_repeated_scope_mismatch.py \
  tests/test_pr48_turn_finalizer.py \
  tests/test_pr311_saga_compensation_outbox_cutover.py \
  tests/test_pr266_session_recovery_boundary.py \
  tests/test_pr247_recovery_outbox_cutover.py \
  tests/test_pr245_suspected_dead_recovery.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr243_inbox_restart_cutover.py \
  tests/test_pr248_attach_outbox_cutover.py \
  tests/test_pr251_wake_creation_outbox_cutover.py \
  tests/test_pr271_session_attach_flow_consolidation.py \
  tests/test_pr279_session_rebuild_projector_boundary.py \
  tests/test_pr318_projection_table_quarantine_guard.py \
  tests/test_pr272_session_active_state_ledger_boundary.py \
  tests/test_pr273_session_harness_final_residue_guard.py
```

Result: `170 passed in 0.95s`.

## Residue Search and Classification

Searched for generation defaulting and finalize/session-ended paths:

- `session_generation.*or 0`
- `finalize_generation.*or 0`
- `generation.*or 0`
- `session_generation: int = 0`
- `ctx.get("session_generation") or 0`
- direct `CORTEX_SCOPE_END` and `wake_finalize` paths
- stale `_publish_attach_request_after_transaction`

Suspicious hits were inspected:

- `queue_service/session_fsm.py`
  - `finalize_generation = int(event.payload.get("finalize_generation") or 0)` is immediately rejected when `< 1`; it does not synthesize a valid finalize identity.
  - `event_generation=int(decision.payload.get("event_generation") or 0)` is result metadata from the FSM decision, not a mutation identity producer.
- `queue_service/session_repo.py`
  - `generation=int(... or 0)` is used to build no-active/runtime state snapshots.
  - Attach path converts current active generation and raises when `< 1`.
- `queue_service/saga_repo.py`
  - Saga/lease generation reads are FSM runtime-state reads.
  - Suspected-dead recovery event records the current session generation if present, and downstream recovery archive now requires positive generation before scope-end publication.
- Tests retain negative assertions for removed compatibility/default patterns.

## Outcome

No new P352-scoped production gap was found after the P365 cleanup. Runtime finalize enforcement is aggregate-clean for the tested and searched paths.
