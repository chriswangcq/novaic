# P825: Runbook topology alignment

Status: done
Parent: P685
Root: P000
Source Ticket: T819 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P825
Body: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P825/README.md
Ticket(s): T821

## Problem
Operational runbooks (cloud-production.md, local-backends.md, local-dev.md) describe how to start/stop/monitor services. These must match the current 8-service topology and entrypoint paths.

## Success Criteria
- Each runbook's service references are compared against start.sh and service classification.
- Stale operational instructions are patched.
- No runbook references a service, port, or entrypoint that doesn't exist.

## Subproblems
- none

## Results
- R816

## Latest Check
C865

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P825/README.md
- Ticket T821: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P825/tickets/T821.md
- Result R816: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P825/results/R816.md
- Check C865: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P825/checks/C865.md

## Follow-ups
- none
