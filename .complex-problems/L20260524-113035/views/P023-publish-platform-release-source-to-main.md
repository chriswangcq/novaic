# P023: Publish platform release source to main

Status: doing
Parent: P021
Root: P000
Source Ticket: T021 (spawn)
Source Check: none
Package: problems/P000/children/P019/children/P021/children/P023
Body: problems/P000/children/P019/children/P021/children/P023/README.md
Ticket(s): T022

## Problem
The API-host release-controller worktree is now a git checkout, but `origin/main` does not contain the current platform release paths such as `docker/`, `services-image`, `factory-image`, and `release-controller-image`. Without publishing the current source, the managed worktree cannot execute real non-dry-run release commands after checkout.

## Success Criteria
- Current release-controller and Docker/deploy platform source is committed on `main`.
- The commit is pushed to `origin/main`.
- The API-host worktree can fast-forward to that commit.
- After updating, the API-host worktree contains `docker/api-backend/Dockerfile`, `docker/llm-factory/Dockerfile`, `docker/release-controller/Dockerfile`, and `deploy` commands for `services-image`, `factory-image`, and `release-controller-image`.
- Existing unrelated dirty submodule working trees are not silently reverted.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P019/children/P021/children/P023/README.md
- Ticket T022: problems/P000/children/P019/children/P021/children/P023/tickets/T022.md

## Follow-ups
- none
