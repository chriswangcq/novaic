# P325: Update PR-252 attach state test for worker-owned outbox

Status: done
Parent: P324
Root: P000
Source Ticket: none (none)
Source Check: C330
Package: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P324/children/P325
Body: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P324/children/P325/README.md
Ticket(s): T316

## Problem
`test_active_session_state_routes_attach` in `test_pr252_session_state_ssot.py` still asserts old synchronous attach task publication. It should assert the current worker-owned contract: dispatch writes the session outbox row with expected generation, and explicit session outbox drain publishes the task.

## Success Criteria
- The test no longer expects `tq_tasks` attach task before outbox drain.
- The test still verifies active session state routes attach and preserves expected session generation.
- The test explicitly drains pending session outbox and then verifies the published task payload.
- The focused PR-252 test and rebuild/projection coverage set pass.

## Subproblems
- none

## Results
- R311

## Latest Check
C331

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P324/children/P325/README.md
- Ticket T316: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P324/children/P325/tickets/T316.md
- Result R311: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P324/children/P325/results/R311.md
- Check C331: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P324/children/P325/checks/C331.md

## Follow-ups
- none
