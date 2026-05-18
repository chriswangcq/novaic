# P456: Runtime focused compatibility behavior tests

Status: done
Parent: P454
Root: P000
Source Ticket: T446 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/children/P456
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/children/P456/README.md
Ticket(s): T447

## Problem
Run the focused runtime behavior tests that prove the Queue/session harness uses the intended FSM/generation/finalize/outbox contracts rather than old imperative or compatibility paths.

## Success Criteria
- Run focused `novaic-agent-runtime` tests for attach, finalize, session-ended, recovery, session-state/generation, legacy cleanup, explicit contracts, historical image guard, and shell output contract.
- Save the exact command, exit status, and log under `.complex-problems/L20260516-222011/tmp/p456/`.
- If tests fail, create a repair follow-up with failing test names and first actionable traceback.

## Subproblems
- none

## Results
- R440

## Latest Check
C466

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/children/P456/README.md
- Ticket T447: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/children/P456/tickets/T447.md
- Result R440: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/children/P456/results/R440.md
- Check C466: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P406/children/P454/children/P456/checks/C466.md

## Follow-ups
- none
