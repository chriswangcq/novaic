# P005: Upgrade API-host controller and verify quality gates execute

Status: done
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P005
Body: problems/P000/children/P003/children/P005/README.md
Ticket(s): T005

## Problem
After the quality-gate commit is pushed, the running API-host controller must be upgraded to an image built from that commit and the remote runtime config must include `quality_gates`. A staging run must prove the gates execute before build/deploy and block semantics remain controller-owned.

## Success Criteria
- A new Release Controller image is built/pushed/deployed from the quality-gate commit.
- Remote `/opt/novaic/release-controller/config.json` contains the intended `quality_gates` and preserves existing registry, branch, health, and polling settings.
- A staging run through Release Controller succeeds with command plan order: git/submodule, `quality-*`, preflight, build, push, deploy, smoke.
- Staging public health is clean after the run.
- Prod current pointer remains unchanged unless deliberately promoted.
- Polling is re-enabled and Release Controller status has `last_error=null`.
- Manual direct backend/factory deploy commands still fail locally before remote side effects.

## Subproblems
- P006: Make Release Controller image capable of running quality gates
- P007: Complete API-host quality-gate rollout

## Results
- R004

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P003/children/P005/README.md
- Ticket T005: problems/P000/children/P003/children/P005/tickets/T005.md
- Result R004: problems/P000/children/P003/children/P005/results/R004.md
- Check C004: problems/P000/children/P003/children/P005/checks/C004.md
- Check C009: problems/P000/children/P003/children/P005/checks/C009.md

## Follow-ups
- P007: Complete API-host quality-gate rollout
