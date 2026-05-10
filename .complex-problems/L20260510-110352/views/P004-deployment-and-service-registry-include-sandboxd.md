# P004: Deployment and service registry include sandboxd

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
The new independent server must be first-class infrastructure in local/deploy scripts and service registry; otherwise the code can exist but production still runs the old path.

## Success Criteria
- `services.json` declares sandboxd on a stable port.
- Local startup starts/stops sandboxd and passes its URL into Cortex.
- Deployment rsync/install/start/status/log verification includes `novaic-sandbox-service`.
- No deployment script keeps a hidden fallback to in-process sandbox execution.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R003: problems/P000/children/P004/results/R003.md
- Check C003: problems/P000/children/P004/checks/C003.md

## Follow-ups
- none
