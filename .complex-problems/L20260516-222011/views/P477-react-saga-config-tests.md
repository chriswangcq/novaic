# P477: React saga config tests

Status: done
Parent: P472
Root: P000
Source Ticket: T463 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P477
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P477/README.md
Ticket(s): T466

## Problem
Add and run focused tests proving react saga decisions are controlled by explicit config, not global `ServiceConfig` monkeypatching.

## Success Criteria
- Tests cover non-default round cap for `react_actions`.
- Tests cover non-default round cap or stack-hold retry limit for `react_think`.
- A guard proves decision adapter functions no longer directly reference `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE`.
- Test logs are saved under `.complex-problems/L20260516-222011/tmp/p477/`.

## Subproblems
- none

## Results
- R459

## Latest Check
C486

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P477/README.md
- Ticket T466: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P477/tickets/T466.md
- Result R459: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P477/results/R459.md
- Check C486: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P477/checks/C486.md

## Follow-ups
- none
