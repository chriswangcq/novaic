# P018: Wire deployed release-controller branch polling

Status: done
Parent: P000
Root: P000
Source Ticket: none (none)
Source Check: C018
Package: problems/P000/children/P018
Body: problems/P000/children/P018/README.md
Ticket(s): T018

## Problem
The deployed release-controller must be able to trigger from branch heads through its own control plane, not only through manual `/v1/triggers`. Wire the existing poller into the service and prepare a managed API-host worktree so branch-driven dry-run polling is operational.

## Success Criteria
- HTTP API exposes a poll-once endpoint or a documented internal loop that invokes `BranchPoller`.
- Poll-once can run safely with `dry_run=true` and returns changed/skipped/failed outcomes.
- API host has a managed worktree path or explicit documented bootstrap command for it.
- Deployed controller can call the poll-once path successfully on the API host.
- Branch-driven polling remains non-prod only and cannot target prod.
- Docs mention how to run/verify branch polling.

## Subproblems
- none

## Results
- R018

## Latest Check
C019

## Bodies
- Problem: problems/P000/children/P018/README.md
- Ticket T018: problems/P000/children/P018/tickets/T018.md
- Result R018: problems/P000/children/P018/results/R018.md
- Check C019: problems/P000/children/P018/checks/C019.md

## Follow-ups
- none
