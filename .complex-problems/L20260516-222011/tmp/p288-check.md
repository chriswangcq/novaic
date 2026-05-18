# Check: Session rebuild projection and state read inventory

## Summary

Success. The parent problem was not closed by a shallow one-go result: it was split into active-read, rebuild/projection-writer, and coverage/guard audits. Those child results map the relevant methods, prove active reads derive from `tq_session_state` through `SessionLedgerRepository`, classify rebuild and pending projections as derived adapters, and fix the one stale attach test expectation found during verification.

## Evidence

- R308/C328 maps active reads: `SessionRepository.get_active_session`, `list_active_session_states`, `_active_session_state_in_current_transaction`, and `SessionLedgerRepository.list_active_states`. A source spot-check found no production `tq_active_sessions` hits under `novaic-agent-runtime/queue_service` or `novaic-agent-runtime/task_queue`.
- R309/C329 maps rebuild and pending projection writers: `rebuild_session_state_from_running_sagas`, `record_active_session`, `record_pending_projection`, and `PENDING_PROJECTION_OBSERVED`. The source classification is that rebuild projects saga rows into session state and pending projection is derived from unconsumed input events.
- R310 identified focused coverage and exposed a stale `test_pr252_session_state_ssot.py` eager attach expectation. R311 fixed it so dispatch records outbox first and explicit outbox drain publishes the task.
- C332 verifies the coverage set after the follow-up with `19 passed`.

## Criteria Map

- Map read/rebuild/projection methods and source tables: satisfied by R308 and R309, with additional spot-check source searches during this check.
- Explain whether active session reads derive from `tq_session_state` or another pointer: satisfied by R308/C328; active reads route through `SessionLedgerRepository` and the generic FSM store configured for `tq_session_state`.
- Identify test coverage for rebuild/projection/state ownership: satisfied by R310/R311/C332, including SSOT, active-session table removal, pending projection boundary, active state ledger boundary, rebuild projector boundary, and projection quarantine tests.

## Execution Map

- T312 split into P322, P323, and P324.
- P322 closed active-read inventory with R308/C328.
- P323 closed rebuild/projection writer inventory with R309/C329.
- P324 found a stale coverage expectation in R310, opened P325, and closed after R311 with final check C332.

## Stress Test

- Drift risk: production read paths silently use an old active pointer/cache. Checked by R308 plus source search; no production `tq_active_sessions` read path remained.
- Projection risk: pending projection becomes a second authority. Checked by R309; it records derived observed events from unconsumed input events and is non-critical.
- Test residue risk: tests still encode old synchronous attach semantics. Found by R310 and fixed by R311; the guard now requires explicit outbox drain.

## Residual Risk

- Non-blocking: the audit is source/test focused rather than a live deployment test. That is acceptable for P288 because the problem scope is inventory and ownership classification, not runtime smoke deployment.

## Result IDs

- R312
- R308
- R309
- R310
- R311
