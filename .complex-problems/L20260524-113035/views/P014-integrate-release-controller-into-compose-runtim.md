# P014: Integrate release-controller into Compose runtime

Status: done
Parent: P003
Root: P000
Source Ticket: T009 (split)
Source Check: none
Package: problems/P000/children/P003/children/P014
Body: problems/P000/children/P003/children/P014/README.md
Ticket(s): T011

## Problem
Add a Compose runtime shape for the release-controller that mounts explicit config/state/worktree paths and binds the control plane internally without public ingress.

## Success Criteria
- Compose config contains a `release_controller` service.
- The service uses a parameterized image ref.
- Runtime config, state directory, releases directory, repo/worktree, and Docker socket mounts are explicit.
- The controller binds to loopback or an internal-only port.
- Rendered `docker compose config` succeeds with sample environment values.
- The Compose integration does not add Nginx/public domain routing.

## Subproblems
- none

## Results
- R009

## Latest Check
C010

## Bodies
- Problem: problems/P000/children/P003/children/P014/README.md
- Ticket T011: problems/P000/children/P003/children/P014/tickets/T011.md
- Result R009: problems/P000/children/P003/children/P014/results/R009.md
- Check C010: problems/P000/children/P003/children/P014/checks/C010.md

## Follow-ups
- none
