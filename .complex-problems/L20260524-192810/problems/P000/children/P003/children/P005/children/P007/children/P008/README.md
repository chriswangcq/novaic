# Add httpx test dependency to Release Controller image

## Problem

The first real remote quality gate failed because `novaic-release-controller/tests/test_service.py` imports FastAPI/Starlette `TestClient`, which requires `httpx`. The Release Controller image now has pytest but still lacks httpx, so the default `release-controller-ci` gate cannot run the controller test suite inside the controller container.

## Success Criteria

- Release Controller Docker image installs `httpx` alongside pytest for the default controller CI gate.
- Dockerfile invariant tests cover the `httpx` dependency.
- The default gate command succeeds inside the running controller container before retrying the staging rollout.
- The fix is committed and pushed while polling remains disabled.
