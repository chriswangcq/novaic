# P001: Production Runtime Topology Verification

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Verify that the just-deployed production backend is running the expected Queue Service and runtime worker topology, including the role-level worker roster and fresh logs.

## Success Criteria
- `./deploy status` or equivalent remote status confirms expected service and worker processes.
- Fresh-smoke evidence confirms logs are current after the deployment.
- The deployed runtime worker roster matches the code-defined roster.
- Any mismatch is recorded with concrete process/log evidence.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
