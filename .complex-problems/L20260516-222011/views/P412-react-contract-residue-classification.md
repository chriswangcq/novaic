# P412: React contract residue classification

Status: done
Parent: P409
Root: P000
Source Ticket: T398 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P412
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P412/README.md
Ticket(s): T399

## Problem
`react_think.py` and `react_actions.py` contain round, stack-depth, retry, and session-generation related guard hits. They must be classified or patched so React contract defaults cannot weaken live session generation boundaries.

## Success Criteria
- Inspect React contract guard hits from P402.
- Confirm `session_generation` is explicit and validated, not defaulted.
- Classify round/retry/stack-depth defaults as non-session control counters or patch if unsafe.
- Run focused React contract tests.

## Subproblems
- none

## Results
- R392

## Latest Check
C418

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P412/README.md
- Ticket T399: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P412/tickets/T399.md
- Result R392: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P412/results/R392.md
- Check C418: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P412/checks/C418.md

## Follow-ups
- none
