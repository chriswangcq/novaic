# P501: Recovery and session-ended contract inventory

Status: done
Parent: P491
Root: P000
Source Ticket: T493 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P501
Body: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P501/README.md
Ticket(s): T494

## Problem
Before changing recovery code, inspect suspected-dead, recovery archive, session-ended, and finalize-adapter production paths. Classify whether they preserve explicit generation and stack diagnostics, and identify silent fallback behavior.

## Success Criteria
- Production paths in `saga_repo.py`, `session_recovery.py`, `session_repo.py`, `session_fsm.py`, and `session_handlers.py` are inspected.
- Raw guard and classified artifacts are saved.
- Any silent stack/generation fallback is routed to an implementation child instead of being accepted without evidence.

## Subproblems
- none

## Results
- R489

## Latest Check
C518

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P501/README.md
- Ticket T494: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P501/tickets/T494.md
- Result R489: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P501/results/R489.md
- Check C518: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P501/checks/C518.md

## Follow-ups
- none
