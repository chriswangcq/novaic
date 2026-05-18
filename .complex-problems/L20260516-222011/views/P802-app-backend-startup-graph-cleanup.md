# P802: App backend startup graph cleanup

Status: done
Parent: P785
Root: P000
Source Ticket: T791 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/README.md
Ticket(s): T794

## Problem
App backend startup scripts and packaged/generated backend scripts may contain stale service topology, port conflicts, or binary/resource expectations that do not match current services.

## Success Criteria
- `novaic-app/scripts/start-backends.sh`, packaged backend scripts, and generated backend scripts agree on the current service list and ports.
- The `PORT_CORTEX=19996` versus `vmcontrol` port conflict is resolved or renamed clearly.
- Backend binary/resource expectations match committed resources or are marked dev-only.
- Focused script/config checks run.

## Subproblems
- P804: App backend startup graph audit
- P805: App backend startup graph remediation

## Results
- R792

## Latest Check
C840

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/README.md
- Ticket T794: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/tickets/T794.md
- Result R792: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/results/R792.md
- Check C840: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/checks/C840.md

## Follow-ups
- none
