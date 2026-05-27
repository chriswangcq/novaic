# P001: Discover Release Controller deployment contract and current status

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Before deploying, the exact Release Controller API/config, branch policy, namespaces, health URLs, and current service status must be known so the release is triggered correctly and verified against the right endpoints.

## Success Criteria
- Identify the controller config file, HTTP endpoint/base URL, branch trigger policy, namespace target, and health/smoke URLs.
- Confirm the controller is reachable and report current status/runs.
- Confirm direct deploy scripts are controller internals rather than the deployment path.
- Produce exact commands/URLs to use for the release trigger.

## Subproblems
- P005: Inspect local Release Controller contract
- P006: Probe live Release Controller status and runs

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R002: problems/P000/children/P001/results/R002.md
- Check C002: problems/P000/children/P001/checks/C002.md

## Follow-ups
- none
