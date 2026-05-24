# P007: Complete API-host quality-gate rollout

Status: done
Parent: P005
Root: P000
Source Ticket: none (none)
Source Check: C004
Package: problems/P000/children/P003/children/P005/children/P007
Body: problems/P000/children/P003/children/P005/children/P007/README.md
Ticket(s): T007

## Problem
The Release Controller image/runtime dependency gap has been fixed in commit `6a74b2ac08b199a4c2c0db54c3fc31708bd59261`, but the API-host controller has not yet been upgraded and no staging run has proven quality gates execute before image build/deploy.

## Success Criteria
- API-host Release Controller image is built/pushed/deployed from commit `6a74b2ac08b199a4c2c0db54c3fc31708bd59261`.
- Remote config includes `quality_gates` with `release-controller-ci` and `release-path-lints` while preserving existing release settings.
- A staging Release Controller run succeeds for commit `6a74b2ac08b199a4c2c0db54c3fc31708bd59261`.
- The staging run command plan and execution results show `quality-release-controller-ci` and `quality-release-path-lints` before build/deploy, both successful.
- Staging health is clean, prod current pointer remains unchanged, polling is re-enabled with `last_error=null`, and direct manual backend/factory deploy guards still fail.

## Subproblems
- P008: Add httpx test dependency to Release Controller image
- P009: Retry final quality-gated staging release

## Results
- R006

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P003/children/P005/children/P007/README.md
- Ticket T007: problems/P000/children/P003/children/P005/children/P007/tickets/T007.md
- Result R006: problems/P000/children/P003/children/P005/children/P007/results/R006.md
- Check C006: problems/P000/children/P003/children/P005/children/P007/checks/C006.md
- Check C008: problems/P000/children/P003/children/P005/children/P007/checks/C008.md

## Follow-ups
- P009: Retry final quality-gated staging release
