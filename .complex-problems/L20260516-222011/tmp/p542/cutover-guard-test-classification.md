# P542 Cutover / Guardrail Test Classification

## Source

- Input: `.complex-problems/L20260516-222011/tmp/p531/static-residue-tests.txt`
- Filtered hits: `.complex-problems/L20260516-222011/tmp/p542/cutover-guard-test-hits.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p542/cutover-guard-test-counts.txt`
- Context slices: `.complex-problems/L20260516-222011/tmp/p542/cutover-guard-test-context.txt`

## Totals

- Hits: 73
- Files: 11

## Classification Table

| File | Hits | Purpose | Classification | Rationale | Follow-up |
| --- | ---: | --- | --- | --- | --- |
| `tests/test_pr153_pending_inbox_metadata.py` | 8 | Pending inbox metadata / active session behavior | Expected regression coverage | Hits exercise active-session state and `remaining_stack` while verifying concurrent dispatch attaches/buffers correctly. | No |
| `tests/test_pr315_queue_fsm_final_residue_guard.py` | 8 | Final residue source guard | Expected guardrail coverage | Hits are intentional negative assertions against `tq_active_sessions`, `legacy`, `compat`, and `fallback` in active queue coordinators. | No |
| `tests/test_pr251_wake_creation_outbox_cutover.py` | 7 | Wake creation outbox cutover | Expected regression coverage | Hits verify active session lifecycle and `remaining_stack` while asserting wake creation is driven through outbox-backed state. | No |
| `tests/test_pr252_session_state_ssot.py` | 7 | Session state SSOT routing | Expected regression coverage | Hits verify no-active/active routing and active session projection through `session_state` ownership. | No |
| `tests/test_pr255_legacy_compat_cleanup.py` | 7 | Retired compatibility cleanup | Expected guardrail coverage | Hits intentionally assert legacy dispatch routes, `legacy_pending`, and `tq_active_sessions` references stay removed. | No |
| `tests/test_pr257_remove_active_sessions_table.py` | 7 | Active sessions table removal | Expected guardrail/regression coverage | Hits verify fresh schema omits `tq_active_sessions` and dispatch/rebuild work through session state. | No |
| `tests/test_pr273_session_harness_final_residue_guard.py` | 7 | Final harness residue guard | Expected guardrail coverage | Hits intentionally assert no stale dual-path language remains and restrict `record_active_session` to expected projector/rebuild modules. | No |
| `tests/test_pr248_attach_outbox_cutover.py` | 6 | Attach outbox cutover | Expected regression coverage | Hits verify publish boundary and active-session generation/race behavior during attach buffering. | No |
| `tests/test_pr272_session_active_state_ledger_boundary.py` | 6 | Ledger-owned active-state shape | Expected boundary coverage | Hits assert active session shape ownership and prevent repository/outbox from recording active sessions directly. | No |
| `tests/test_pr316_taskqueue_state_candidate_cutover.py` | 5 | TaskQueue state candidate cutover | Expected regression coverage | Hits exercise `queue.publish()` in state-candidate lifecycle paths; this is current queue substrate API use. | No |
| `tests/integration/test_saga_dag_refactor.py` | 5 | Saga DAG refactor integration | Expected integration coverage | Hits exercise task publish with saga IDs and DAG dependencies; this is live TaskQueue/Saga substrate behavior. | No |

## Conclusion

All P542 hits are expected cutover/guardrail coverage. Several files intentionally contain retired vocabulary, but in negative assertions or source guardrails that protect the cleaned architecture. No stale or misleading test residue was found in this group.
