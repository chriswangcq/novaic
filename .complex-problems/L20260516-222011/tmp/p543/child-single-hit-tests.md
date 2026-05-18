# Classify single-hit boundary tests

## Problem

Classify the low-density remainder test files that have exactly one P531 static-residue hit each. This bucket contains 21 hits across 21 files after subtracting P541 and P542 ownership.

Initial file group:
- `tests/test_health_dispatch.py`
- `tests/test_pr112_business_client_boundary.py`
- `tests/test_pr119_no_retired_step_result_service_arg.py`
- `tests/test_pr186_runtime_main_path_acceptance.py`
- `tests/test_pr234_repeated_scope_mismatch.py`
- `tests/test_pr240_input_consumption.py`
- `tests/test_pr241_pending_inbox_projection.py`
- `tests/test_pr242_strict_input_ledger.py`
- `tests/test_pr249_observed_wake_outbox_cleanup.py`
- `tests/test_pr253_dispatch_pure_fsm_cutover.py`
- `tests/test_pr265_session_restart_context_boundary.py`
- `tests/test_pr276_session_repository_required_ledger.py`
- `tests/test_pr279_session_rebuild_projector_boundary.py`
- `tests/test_pr312_saga_old_sql_residue_cleanup.py`
- `tests/test_pr314_queue_control_plane_audit_replay.py`
- `tests/test_pr317_sagarepository_state_candidate_cutover.py`
- `tests/test_pr43_previous_scope_transport.py`
- `tests/test_pr70_explicit_skill_summary_only.py`
- `tests/test_pr83_no_legacy_summary_paths.py`
- `tests/test_queue_explicit_dependencies.py`
- `tests/test_saga_creation_policy_boundary.py`

## Success Criteria

- The single-hit bucket is counted and reconciled.
- Every listed file has a classification rationale.
- Stale or misleading one-off tests become follow-up-worthy.
- The bucket records artifacts for P543/P544 reconciliation.
