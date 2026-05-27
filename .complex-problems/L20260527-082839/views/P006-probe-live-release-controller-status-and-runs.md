# P006: Probe live Release Controller status and runs

Status: done
Parent: P001
Root: P000
Source Ticket: T001 (split)
Source Check: none
Package: problems/P000/children/P001/children/P006
Body: problems/P000/children/P001/children/P006/README.md
Ticket(s): T003

## Problem
Local config is not enough; the controller must be reachable and its current status/runs must be known before triggering a deployment.

## Success Criteria
- Discover a reachable controller base URL from local config, process list, compose, nginx, or docs.
- Call status/runs/read endpoints successfully or record the exact blocker.
- Capture current latest run/pointers before triggering new release.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P001/children/P006/README.md
- Ticket T003: problems/P000/children/P001/children/P006/tickets/T003.md
- Result R001: problems/P000/children/P001/children/P006/results/R001.md
- Check C001: problems/P000/children/P001/children/P006/checks/C001.md

## Follow-ups
- none
