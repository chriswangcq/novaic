# P473: Retained ServiceConfig boundary classification

Status: done
Parent: P469
Root: P000
Source Ticket: T462 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P473
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P473/README.md
Ticket(s): T467

## Problem
Classify remaining `ServiceConfig` reads in runtime queue/task code after the saga decision config fix. Adapter-boundary defaults may be retained, but decision-path hidden inputs must be remediated or split.

## Success Criteria
- Produce a saved classification artifact for retained `ServiceConfig` hits.
- Each retained hit is classified as process startup, client adapter, tool adapter, retry policy adapter, or risky decision-path hidden input.
- Any risky hit not handled by P472 is turned into a new child/follow-up rather than ignored.

## Subproblems
- none

## Results
- R461

## Latest Check
C488

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P473/README.md
- Ticket T467: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P473/tickets/T467.md
- Result R461: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P473/results/R461.md
- Check C488: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P473/checks/C488.md

## Follow-ups
- none
