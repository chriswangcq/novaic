# P679: Local dev backend launcher remediation

Status: done
Parent: P676
Root: P000
Source Ticket: T673 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P679
Body: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P679/README.md
Ticket(s): T674

## Problem
`novaic-app/scripts/start-backends.sh` is an active dev launcher but appears to start only a subset of current backend services while claiming to start all Python backends. Inspect and fix stale or misleading local dev launcher behavior/wording without live deployment.

## Success Criteria
- The script is inspected against current service topology evidence.
- Misleading comments/status output or stale worker/process assumptions are fixed.
- Shell syntax and relevant guard checks pass.
- Any intentional local-dev subset behavior is documented in the script or result.

## Subproblems
- none

## Results
- R669

## Latest Check
C711

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P679/README.md
- Ticket T674: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P679/tickets/T674.md
- Result R669: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P679/results/R669.md
- Check C711: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P679/checks/C711.md

## Follow-ups
- none
