# P006: Migrate CI/CD docs and clean stale branches

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P006
Body: problems/P000/children/P006/README.md
Ticket(s): T015

## Problem
The repository and local git workspace should reflect the controller as the primary long-term CI/CD path, with GitHub Actions demoted to optional verification/fallback. Stale local branches should be cleaned without losing current work.

## Success Criteria
- Deployment/runbook docs explain release-controller as the primary path.
- GitHub Actions docs are updated as secondary or optional.
- Local stale branches are reviewed and safe stale branches are deleted.
- Current dirty work and active branch are preserved.
- Final git branch/status summary is recorded.

## Subproblems
- P016: Update release-controller CI/CD docs
- P017: Inspect and clean stale local branches

## Results
- R016

## Latest Check
C017

## Bodies
- Problem: problems/P000/children/P006/README.md
- Ticket T015: problems/P000/children/P006/tickets/T015.md
- Result R016: problems/P000/children/P006/results/R016.md
- Check C017: problems/P000/children/P006/checks/C017.md

## Follow-ups
- none
