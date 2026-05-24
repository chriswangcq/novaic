# P008: Add httpx test dependency to Release Controller image

Status: done
Parent: P007
Root: P000
Source Ticket: T007 (spawn)
Source Check: none
Package: problems/P000/children/P003/children/P005/children/P007/children/P008
Body: problems/P000/children/P003/children/P005/children/P007/children/P008/README.md
Ticket(s): T008

## Problem
The first real remote quality gate failed because `novaic-release-controller/tests/test_service.py` imports FastAPI/Starlette `TestClient`, which requires `httpx`. The Release Controller image now has pytest but still lacks httpx, so the default `release-controller-ci` gate cannot run the controller test suite inside the controller container.

## Success Criteria
- Release Controller Docker image installs `httpx` alongside pytest for the default controller CI gate.
- Dockerfile invariant tests cover the `httpx` dependency.
- The default gate command succeeds inside the running controller container before retrying the staging rollout.
- The fix is committed and pushed while polling remains disabled.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P003/children/P005/children/P007/children/P008/README.md
- Ticket T008: problems/P000/children/P003/children/P005/children/P007/children/P008/tickets/T008.md
- Result R005: problems/P000/children/P003/children/P005/children/P007/children/P008/results/R005.md
- Check C005: problems/P000/children/P003/children/P005/children/P007/children/P008/checks/C005.md

## Follow-ups
- none
