# P546 Single-Hit Boundary Test Classification

## Source

- Filtered hits: `.complex-problems/L20260516-222011/tmp/p546/single-hit-test-hits.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p546/single-hit-test-counts.txt`
- Hit lines: `.complex-problems/L20260516-222011/tmp/p546/single-hit-test-lines.txt`

## Totals

- Hits: 21
- Files: 21

## Classification Table

| File | Hit Purpose | Classification | Follow-up |
| --- | --- | --- | --- |
| `tests/test_health_dispatch.py` | No fallback-dispatch invariant comment/test section | Expected guardrail coverage | No |
| `tests/test_pr112_business_client_boundary.py` | Backcompat parameter removal guard | Expected source/API boundary guard | No |
| `tests/test_pr119_no_retired_step_result_service_arg.py` | Deprecated ignored arg absence assertion | Expected retired-API guard | No |
| `tests/test_pr186_runtime_main_path_acceptance.py` | `remaining_stack` in runtime acceptance payload | Expected finalize contract coverage | No |
| `tests/test_pr234_repeated_scope_mismatch.py` | `remaining_stack` in mismatch recovery context | Expected recovery/finalize coverage | No |
| `tests/test_pr240_input_consumption.py` | `remaining_stack` in input consumption finalize path | Expected lifecycle coverage | No |
| `tests/test_pr241_pending_inbox_projection.py` | `remaining_stack` in pending inbox projection path | Expected inbox/finalize coverage | No |
| `tests/test_pr242_strict_input_ledger.py` | Empty active session projection assertion | Expected strict ledger boundary coverage | No |
| `tests/test_pr249_observed_wake_outbox_cleanup.py` | `remaining_stack` in observed wake cleanup | Expected outbox/finalize coverage | No |
| `tests/test_pr253_dispatch_pure_fsm_cutover.py` | Legacy dispatch route absence guard | Expected source guard | No |
| `tests/test_pr265_session_restart_context_boundary.py` | `remaining_stack` in restart context boundary | Expected session restart coverage | No |
| `tests/test_pr276_session_repository_required_ledger.py` | Optional ledger bypass absence guard | Expected explicit dependency guard | No |
| `tests/test_pr279_session_rebuild_projector_boundary.py` | Projector owns `record_active_session` | Expected projector boundary guard | No |
| `tests/test_pr312_saga_old_sql_residue_cleanup.py` | Direct suspected-dead event writer absence guard | Expected stale-SQL cleanup guard | No |
| `tests/test_pr314_queue_control_plane_audit_replay.py` | Queue publish in audit replay control-plane test | Expected queue substrate coverage | No |
| `tests/test_pr317_sagarepository_state_candidate_cutover.py` | Queue publish in SagaRepository state-candidate test | Expected queue substrate coverage | No |
| `tests/test_pr43_previous_scope_transport.py` | Legacy `previous_scope_id` docstring for retired path | Expected regression context/retirement marker | No |
| `tests/test_pr70_explicit_skill_summary_only.py` | `remaining_stack` in explicit summary-only finalize path | Expected finalize contract coverage | No |
| `tests/test_pr83_no_legacy_summary_paths.py` | Legacy summary producer absence guard | Expected retired-path guard | No |
| `tests/test_queue_explicit_dependencies.py` | Queue publish in explicit dependency test | Expected queue API coverage | No |
| `tests/test_saga_creation_policy_boundary.py` | Fake publish method in creation policy boundary test | Expected test double for current publish boundary | No |

## Conclusion

All single-hit tests are expected boundary, guardrail, or queue/finalize contract coverage. No stale or misleading one-off test residue was found.
