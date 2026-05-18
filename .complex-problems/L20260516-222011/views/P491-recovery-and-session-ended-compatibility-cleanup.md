# P491: Recovery and session-ended compatibility cleanup

Status: done
Parent: P482
Root: P000
Source Ticket: T481 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P491
Body: problems/P000/children/P004/children/P279/children/P482/children/P491/README.md
Ticket(s): T493

## Problem
Recovery and session-ended paths must not mutate active-session state outside the FSM contract or preserve old fallback behavior for dead sessions. Watchdog and recovery should produce explicit recovery/session-ended semantics without silently treating a broken wake as normally resumable. This belongs under P482 because recovery is where stale compatibility tends to survive after dispatch migration.

## Success Criteria
- Recovery and session-ended production paths are inspected against the P482 inventory.
- Direct active-session mutation outside the accepted repository/FSM boundary is removed or justified with a guard test.
- Dead/suspected-dead recovery behavior is explicit and generation-aware.
- Focused recovery/session-ended tests pass.

## Subproblems
- P501: Recovery and session-ended contract inventory
- P502: Recovery stack diagnostics hardening
- P503: Recovery and session-ended final verification

## Results
- R492

## Latest Check
C521

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P491/README.md
- Ticket T493: problems/P000/children/P004/children/P279/children/P482/children/P491/tickets/T493.md
- Result R492: problems/P000/children/P004/children/P279/children/P482/children/P491/results/R492.md
- Check C521: problems/P000/children/P004/children/P279/children/P482/children/P491/checks/C521.md

## Follow-ups
- none
