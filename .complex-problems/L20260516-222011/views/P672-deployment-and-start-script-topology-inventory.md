# P672: Deployment and start script topology inventory

Status: done
Parent: P668
Root: P000
Source Ticket: T668 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P672
Body: problems/P000/children/P007/children/P668/children/P672/README.md
Ticket(s): T669

## Problem
Inventory repository scripts and configs that start, deploy, supervise, or smoke backend services. Determine which scripts are active, which are guard/test-only, and whether any active script uses stale process names or unclear worker roles.

## Success Criteria
- Start/deploy/supervision/smoke script files are located and inspected with evidence.
- Active scripts are distinguished from historical/test-only scripts.
- Stale process names or unclear role labels in active scripts are patched when low-risk.
- Script syntax or relevant static checks are run for any changed script.

## Subproblems
- P675: Deployment script discovery and classification
- P676: Active deployment script stale-role remediation

## Results
- R673

## Latest Check
C715

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P672/README.md
- Ticket T669: problems/P000/children/P007/children/P668/children/P672/tickets/T669.md
- Result R673: problems/P000/children/P007/children/P668/children/P672/results/R673.md
- Check C715: problems/P000/children/P007/children/P668/children/P672/checks/C715.md

## Follow-ups
- none
