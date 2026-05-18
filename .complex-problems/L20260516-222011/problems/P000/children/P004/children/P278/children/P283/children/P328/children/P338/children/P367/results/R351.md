# Session Finalize Diagnostics Binding Result

## Summary

Audited the queue session finalize diagnostics binding path. The current implementation already builds explicit finalize metadata before the active-session mutation and records that metadata into finalized/rejected ledger events, but the focused tests are not strict enough to prove all acceptance criteria against future drift.

## Done

- Inspected `novaic-agent-runtime/queue_service/session_repo.py`, `session_fsm.py`, and `session_ledger.py` around `session_ended`, `decide_session_finalize`, finalized event recording, rejected finalize recording, and session-closed metadata.
- Inspected `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`.
- Confirmed valid finalize currently records `finalize_reason`, `finalize_generation`, `ended_scope_id`, and `remaining_stack`.
- Confirmed stale generation finalize currently rejects without clearing the active session, and the rejection payload contains the stale finalize metadata.
- Confirmed `session_closed` currently carries the same finalize metadata in its payload metadata.

## Verification

- Source inspection covered the explicit finalize metadata path and related ledger writers.
- Existing tests already cover valid finalize, generation mismatch rejection, and scope mismatch rejection.
- A local inspection script confirmed valid and rejected ledger event payload shapes during `SessionRepository.session_ended`.

## Known Gaps

- Tests should be hardened so they assert `session_closed` metadata exactly equals the pre-mutation finalize metadata.
- Tests should assert stale generation and stale scope rejection payloads contain the rejected finalize's own `finalize_reason`, `finalize_generation`, `ended_scope_id`, and `remaining_stack`, while no `session_finalized` event is emitted.
- Focused tests and residue search still need to be rerun after those stricter assertions are added.

## Artifacts

- Ticket: `.complex-problems/L20260516-222011/tmp/P367-session-finalize-diagnostics-binding-ticket.md`
- Test file inspected: `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- Runtime files inspected: `novaic-agent-runtime/queue_service/session_repo.py`, `novaic-agent-runtime/queue_service/session_fsm.py`, `novaic-agent-runtime/queue_service/session_ledger.py`
