# P626: Runtime Shell Handler SDK Wiring

Status: done
Parent: P624
Root: P000
Source Ticket: T619 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/children/P626
Body: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/children/P626/README.md
Ticket(s): T620

## Problem
Verify active runtime shell/tool handlers instantiate and call the sandbox SDK/service boundary for shell execution.

## Success Criteria
- Records exact scans for sandbox SDK imports/usages in `novaic-agent-runtime`.
- Cites active shell/tool handler source slices.
- Confirms shell execution goes through SDK/service boundary.
- Creates a follow-up if active shell execution bypasses sandboxd.

## Subproblems
- none

## Results
- R614

## Latest Check
C655

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/children/P626/README.md
- Ticket T620: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/children/P626/tickets/T620.md
- Result R614: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/children/P626/results/R614.md
- Check C655: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P624/children/P626/checks/C655.md

## Follow-ups
- none
