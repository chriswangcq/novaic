# P016: Update release-controller CI/CD docs

Status: done
Parent: P006
Root: P000
Source Ticket: T015 (split)
Source Check: none
Package: problems/P000/children/P006/children/P016
Body: problems/P000/children/P006/children/P016/README.md
Ticket(s): T016

## Problem
The repository needs documentation that reflects the deployed center-driven release-controller path, including current capabilities, operator commands, and remaining bootstrap limitations.

## Success Criteria
- Release-controller architecture/runbook docs mention deployed API host status.
- Docs describe branch-driven staging, manual prod promotion, rollback, dry-run behavior, and image-based deploy paths.
- Docs clarify that GitHub Actions is no longer the desired long-term primary orchestrator.
- Docs explicitly list the current managed worktree gap before real non-dry-run branch execution.
- Docs do not claim public ingress for the controller.

## Subproblems
- none

## Results
- R014

## Latest Check
C015

## Bodies
- Problem: problems/P000/children/P006/children/P016/README.md
- Ticket T016: problems/P000/children/P006/children/P016/tickets/T016.md
- Result R014: problems/P000/children/P006/children/P016/results/R014.md
- Check C015: problems/P000/children/P006/children/P016/checks/C015.md

## Follow-ups
- none
