# P475: React saga decision config model

Status: done
Parent: P472
Root: P000
Source Ticket: T463 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P475
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P475/README.md
Ticket(s): T464

## Problem
Define the smallest explicit config model/provider needed for react saga decisions, covering `max_rounds_before_force_finalize` and `max_stack_hold_retries`.

## Success Criteria
- A clear typed config object or provider exists in an appropriate module.
- Defaults can still come from `ServiceConfig` at a narrow boundary.
- Tests or source structure allow callers to pass explicit values without monkeypatching globals.

## Subproblems
- none

## Results
- R457

## Latest Check
C484

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P475/README.md
- Ticket T464: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P475/tickets/T464.md
- Result R457: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P475/results/R457.md
- Check C484: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P472/children/P475/checks/C484.md

## Follow-ups
- none
