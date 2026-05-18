# Cortex Archive Diagnostics Aggregate Verification Result

## Summary

Completed P368 aggregate verification for Cortex archive diagnostics. Focused runtime and Cortex suites pass, compile checks pass, and source residue scans confirm the new path is active without replacing semantic context projection fields.

## Evidence

- Runtime compile: `python3 -m py_compile task_queue/sagas/wake_finalize.py task_queue/handlers/cortex_handlers.py task_queue/utils/cortex_bridge.py queue_service/session_recovery.py queue_service/session_outbox.py`
- Runtime focused tests: `PYTHONPATH=.:../novaic-common pytest -q tests/test_scope_end_environment_notifications.py tests/test_pr70_explicit_skill_summary_only.py tests/test_pr65_agent_root_scope.py tests/test_pr67_wake_child_scope.py tests/test_pr186_runtime_main_path_acceptance.py tests/test_finalize_summary_boundary.py tests/test_pr254_finalize_ownership.py tests/test_pr266_session_recovery_boundary.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py` -> 61 passed.
- Cortex compile: `python3 -m py_compile novaic_cortex/api.py novaic_cortex/context_event_writer.py novaic_cortex/context_event_projection.py`
- Cortex focused tests: `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_write_authority.py tests/test_pr74_scope_summary_contract.py tests/test_context_event_projection.py tests/test_context_event_model.py` -> 80 passed.

## Residue Findings

- Cortex source scan found no `active_generation`/`current_session_generation` synthesis in the archive diagnostics path.
- Cortex source scan shows `archive_diagnostics` nested in `WakeArchived` and `context_event_projection.py` still consumes only top-level list-shaped `remaining_stack`.
- Runtime source scan shows active/recovery archive paths require and forward explicit `session_generation`, `finalize_reason`, and dict-shaped `remaining_stack`.

## Acceptance Mapping

- Source map: closed by P371/P375.
- Boundary propagation: closed by P372.
- Persistence: closed by P373/P376.
- Aggregate guard against half integration: closed by P374 verification in this result.

## Residual Note

No follow-up is needed for P374. Parent P368 is ready for final check.
