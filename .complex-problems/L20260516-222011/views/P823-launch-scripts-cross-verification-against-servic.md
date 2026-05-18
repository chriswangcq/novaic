# P823: Launch scripts cross-verification against service topology

Status: done
Parent: P698
Root: P000
Source Ticket: T814 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P823
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P823/README.md
Ticket(s): T818

## Problem
Three launch scripts (start.sh, start-backends.sh, launch_split_only.sh) must match current service topology. After auditing individual service entrypoints, verify these scripts reference correct ports, correct service names, and no stale services.

## Success Criteria
- Each launch script's service list is mapped against the actual service topology.
- Stale port/service references are identified and fixed.
- Scripts launch only services that exist with correct entrypoints.

## Subproblems
- none

## Results
- R812

## Latest Check
C861

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P823/README.md
- Ticket T818: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P823/tickets/T818.md
- Result R812: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P823/results/R812.md
- Check C861: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P823/checks/C861.md

## Follow-ups
- none
