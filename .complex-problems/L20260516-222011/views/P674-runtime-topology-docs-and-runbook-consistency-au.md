# P674: Runtime topology docs and runbook consistency audit

Status: done
Parent: P668
Root: P000
Source Ticket: T668 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P674
Body: problems/P000/children/P007/children/P668/children/P674/README.md
Ticket(s): T823

## Problem
Inspect docs/runbooks that describe backend service layout, worker roles, deployment, and runtime topology. Align current-facing docs with code evidence from scripts and entrypoints; classify historical docs explicitly rather than allowing misleading active docs.

## Success Criteria
- Runtime/deployment topology docs and runbooks are located and inspected.
- Current-facing docs match code-evidence process roles.
- Stale or misleading active docs are updated; historical material is retained only if clearly historical.
- Docs lint or focused markdown checks are run after any docs changes.

## Subproblems
- P827: Runtime process role docs accuracy audit
- P828: Deploy and build docs topology audit
- P829: Doc CI guards pass after topology changes

## Results
- R823

## Latest Check
C872

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P674/README.md
- Ticket T823: problems/P000/children/P007/children/P668/children/P674/tickets/T823.md
- Result R823: problems/P000/children/P007/children/P668/children/P674/results/R823.md
- Check C872: problems/P000/children/P007/children/P668/children/P674/checks/C872.md

## Follow-ups
- none
