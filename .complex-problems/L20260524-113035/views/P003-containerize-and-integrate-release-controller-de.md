# P003: Containerize and integrate release-controller deployment

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T009

## Problem
The controller must run as a Docker service on the API host and be deployable through the repository's operational tooling.

## Success Criteria
- Dockerfile and Compose package exist for release-controller.
- Runtime directories, env examples, and safe defaults are documented.
- Deploy script has release-controller install/update/status/logs commands.
- Compose rendering passes locally.
- Controller container has only the volumes needed for git working copy, release state, deploy script, Docker socket, and SSH/deploy inputs.

## Subproblems
- P013: Package release-controller Docker image
- P014: Integrate release-controller into Compose runtime
- P015: Add release-controller deploy script path

## Results
- R011

## Latest Check
C012

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T009: problems/P000/children/P003/tickets/T009.md
- Result R011: problems/P000/children/P003/results/R011.md
- Check C012: problems/P000/children/P003/checks/C012.md

## Follow-ups
- none
