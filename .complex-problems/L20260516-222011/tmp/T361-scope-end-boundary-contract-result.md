# Scope End Boundary Contract Result

## Summary

Implemented scope-end archive diagnostics propagation across the runtime/Cortex boundary.

## Changes Made

Changed runtime saga and recovery archive payloads so structural Cortex archive receives explicit `session_generation`, `finalize_reason`, `remaining_stack`, and `round_num` instead of relying on implicit archive behavior. Runtime `cortex.scope_end` handler now requires `remaining_stack`, validates positive generation, and passes the diagnostics through `CortexBridge.scope_end`. Recovery archive outbox now rejects payloads missing `remaining_stack`.

Changed Cortex `/v1/scope/end` request validation so archive diagnostics are all-or-nothing: if any diagnostic field is present, `session_generation`, `finalize_reason`, and `remaining_stack` are required, and bool `session_generation` is rejected before Pydantic can coerce it to `1`. Hardened the runtime bridge adapter to reject bool generation before posting to Cortex as well.

## Evidence

- `novaic-agent-runtime`: `python3 -m py_compile task_queue/sagas/wake_finalize.py task_queue/handlers/cortex_handlers.py task_queue/utils/cortex_bridge.py queue_service/session_recovery.py queue_service/session_outbox.py`
- `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q tests/test_scope_end_environment_notifications.py tests/test_pr70_explicit_skill_summary_only.py tests/test_pr65_agent_root_scope.py tests/test_pr67_wake_child_scope.py tests/test_pr186_runtime_main_path_acceptance.py tests/test_finalize_summary_boundary.py tests/test_pr254_finalize_ownership.py tests/test_pr266_session_recovery_boundary.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr233_active_inbox_dispatch.py` -> 61 passed.
- `novaic-cortex`: `python3 -m py_compile novaic_cortex/api.py`
- `novaic-cortex`: `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_pr74_scope_summary_contract.py tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_write_authority.py` -> 25 passed.

## Residual Note

- Cortex still allows structural `ScopeEndRequest` without diagnostics for direct structural API tests. Runtime active/recovery paths now provide diagnostics; the remaining no-diagnostic cases are local Cortex structural lifecycle tests, not runtime finalize traffic.
