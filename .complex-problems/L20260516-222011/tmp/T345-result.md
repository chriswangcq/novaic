# Subagent finalize status identity aggregate verification result

## Summary

Completed aggregate verification for P354's terminal subagent status identity guard. The payload builders, handlers, wake-finalize ordering, session-ended rejection gate, and saga DAG dependency support now line up as one path.

## Done

- Ran the focused aggregate test suite across payload, handler, finalize ownership, scope-end, and DAG contracts.
- Ran source guards for live `last_scope_id`/`last_scope_archived_at` residue and session-generation defaulting in touched runtime files.
- Inspected terminal Business subagent status mutation paths.
- Confirmed terminal status mutations flow through `handle_subagent_set_sleeping()` / `handle_subagent_set_completed()`, both of which validate identity before `entity_update()`.
- Confirmed `wake_finalize` emits:
  - `cortex_scope_end -> []`
  - `session_ended -> ['cortex_scope_end']`
  - `set_subagent_sleeping -> ['session_ended']`
  - `set_subagent_completed -> ['session_ended']`

## Verification

- `python3 -m py_compile task_queue/saga.py task_queue/sagas/wake_finalize.py task_queue/handlers/subagent_handlers.py task_queue/handlers/session_handlers.py task_queue/dag_builder.py task_queue/workers/task_sources.py` passed.
- Aggregate pytest passed: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py tests/test_finalize_summary_boundary.py tests/test_scope_end_environment_notifications.py tests/test_pr65_agent_root_scope.py tests/test_pr67_wake_child_scope.py tests/test_pr70_explicit_skill_summary_only.py tests/test_pr165c_notification_lifecycle_guardrails.py tests/test_pr186_runtime_main_path_acceptance.py tests/test_runtime_explicit_contracts.py tests/test_pr234_tool_logical_failure.py tests/test_pr234_repeated_scope_mismatch.py tests/test_pr48_turn_finalizer.py` -> 109 tests.
- Source guards over `task_queue/sagas/wake_finalize.py`, `task_queue/handlers/subagent_handlers.py`, `task_queue/handlers/session_handlers.py`, and `task_queue/saga.py` found no live `last_scope_id`, `last_scope_archived_at`, `ctx.get("session_generation") or 0`, or `session_generation.*or 0` residue.
- Mutation scan found terminal subagent Business writes only in `subagent_handlers.py`, guarded at lines 85 and 130 before `entity_update()`.

## Known Gaps

- Recovery/compensation finalize identity remains owned by P351 and is outside P354's terminal subagent status path.
- `set_awake` still updates Business without this finalize identity contract by design; it is not a terminal finalize status mutation.

## Artifacts

- Test evidence: 109-test aggregate pytest run.
- Source evidence: `task_queue/sagas/wake_finalize.py`, `task_queue/handlers/subagent_handlers.py`, `task_queue/handlers/session_handlers.py`, `task_queue/saga.py`.
