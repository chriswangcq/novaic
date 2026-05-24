# P024: Make release-controller execute real staging releases

Status: done
Parent: P000
Root: P000
Source Ticket: none (none)
Source Check: C026
Package: problems/P000/children/P024
Body: problems/P000/children/P024/README.md
Ticket(s): T024

## Problem
The deployed release-controller can poll and plan branch releases, but its container lacks a usable Docker CLI and Docker Compose plugin. Make the release-controller image capable of running its build/publish/deploy command plan, redeploy it, and prove a non-dry-run staging release path.

## Success Criteria
- Release-controller image contains working `docker` and `docker compose` commands.
- API-host controller container can access the host Docker socket.
- Updated image is built, pushed, and deployed by immutable digest.
- Non-dry-run `main -> staging` trigger can run verification/build/publish/deploy or produces a precise blocker after invoking the real command path.
- Prod remains promotion-only and cannot be branch-triggered.
- Docs mention the Docker CLI/Compose runtime dependency.

## Subproblems
- P025: Deploy SSH-capable release-controller digest and rerun staging release

## Results
- R024

## Latest Check
C029

## Bodies
- Problem: problems/P000/children/P024/README.md
- Ticket T024: problems/P000/children/P024/tickets/T024.md
- Result R024: problems/P000/children/P024/results/R024.md
- Check C027: problems/P000/children/P024/checks/C027.md
- Check C029: problems/P000/children/P024/checks/C029.md

## Follow-ups
- P025: Deploy SSH-capable release-controller digest and rerun staging release
