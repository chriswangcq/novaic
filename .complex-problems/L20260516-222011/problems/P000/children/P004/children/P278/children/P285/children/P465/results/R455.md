# Session legacy residue inventory result

## Summary

Completed the read-only inventory for P465. The broad guards produced 135 lines of hits, saved as an artifact. The inventory did not edit production source; it only added ledger evidence files. Most hits are either active runtime concepts now backed by `session_state`, generic outbox boundaries, or test-only historical guards. One incidental production cleanup candidate was noticed: `session_outbox.py` has a duplicated `remaining_stack` error string.

## Done

- Saved source guard output covering legacy/compat/fallback terms, active-session terms, session side-effect names, and matching tests.
- Compared git status before and after the inventory command; no delta appeared between the two status snapshots.
- Inspected representative hits in `session_observed_events.py`, `session_rebuild.py`, `session_ledger.py`, `session_repo.py`, `session_outbox.py`, and existing residue guard tests.
- Classified `tq_active_sessions` hits as test guard / schema cleanup evidence rather than live production references.
- Classified `observe_create_wake_saga` hits as test-only old-effect fixtures after the production constant was removed earlier.

## Verification

- Artifact line count: `135 .complex-problems/L20260516-222011/tmp/p465/session-legacy-residue-inventory.txt`.
- `diff -u .complex-problems/L20260516-222011/tmp/p465/git-status-before.txt .complex-problems/L20260516-222011/tmp/p465/git-status-after.txt` produced no output.
- Representative production slices showed `record_active_session` now writes `SessionRuntimeStatus.ACTIVE` into session state, not the retired `tq_active_sessions` table.
- Existing guard tests explicitly assert removed legacy paths stay absent: `test_pr255_legacy_compat_cleanup.py`, `test_pr273_session_harness_final_residue_guard.py`, and `test_pr315_queue_fsm_final_residue_guard.py`.

## Known Gaps

- This was an inventory pass only; no cleanup was performed inside P465.
- Some retained names (`get_active_session`, `list_active_session_states`, `record_active_session`) still carry "active session" language even though the backing authority is `session_state`. That may be acceptable as runtime vocabulary, but P466/P467 should decide whether naming cleanup is needed.
- Incidental cleanup candidate: `novaic-agent-runtime/queue_service/session_outbox.py` has a duplicated `"recovery archive outbox payload requires remaining_stack"` string in one `ValueError`.
- Keyword guards cannot prove behavior alone; P466/P467 should use focused source checks/tests for final closure.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p465/session-legacy-residue-inventory.txt`
- `.complex-problems/L20260516-222011/tmp/p465/git-status-before.txt`
- `.complex-problems/L20260516-222011/tmp/p465/git-status-after.txt`
