# P347: Upstream react generation default classification

Status: done
Parent: P343
Root: P000
Source Ticket: T331 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P347
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P347/README.md
Ticket(s): T334

## Problem
`react_think` and `react_actions` still default `session_generation` to `0`. Determine whether those defaults must be fixed inside P336 for delivery correctness, or whether they are upstream contract work already covered by P337/P339.

## Success Criteria
- Inspect `task_queue/contracts/react_think.py`, `task_queue/contracts/react_actions.py`, and their tests.
- Decide whether changing these defaults is required for P336 parent success.
- If not changed here, record exact follow-on ownership and guard P336 so zero generation still fails before session-ended delivery.

## Subproblems
- none

## Results
- R327

## Latest Check
C348

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P347/README.md
- Ticket T334: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P347/tickets/T334.md
- Result R327: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P347/results/R327.md
- Check C348: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P347/checks/C348.md

## Follow-ups
- none
