# P620: Sandbox Service Execution Boundary Residue

Status: done
Parent: P565
Root: P000
Source Ticket: T615 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P620
Body: problems/P000/children/P005/children/P553/children/P565/children/P620/README.md
Ticket(s): T616

## Problem
Audit `novaic-sandbox-service` for execution bypasses, local fallback paths, host path exposure, mount bypasses, or stale compatibility routes.

## Success Criteria
- Records exact scans for exec, fallback, local, host path, mount, base64, stdout/stderr, and compatibility terms.
- Cites service code/test slices.
- Runs focused sandbox service tests.
- Creates follow-up if sandboxd boundary can be bypassed in active code.

## Subproblems
- none

## Results
- R612

## Latest Check
C653

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P620/README.md
- Ticket T616: problems/P000/children/P005/children/P553/children/P565/children/P620/tickets/T616.md
- Result R612: problems/P000/children/P005/children/P553/children/P565/children/P620/results/R612.md
- Check C653: problems/P000/children/P005/children/P553/children/P565/children/P620/checks/C653.md

## Follow-ups
- none
