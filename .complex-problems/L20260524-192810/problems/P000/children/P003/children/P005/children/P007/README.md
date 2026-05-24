# Complete API-host quality-gate rollout

## Problem

The Release Controller image/runtime dependency gap has been fixed in commit `6a74b2ac08b199a4c2c0db54c3fc31708bd59261`, but the API-host controller has not yet been upgraded and no staging run has proven quality gates execute before image build/deploy.

## Success Criteria

- API-host Release Controller image is built/pushed/deployed from commit `6a74b2ac08b199a4c2c0db54c3fc31708bd59261`.
- Remote config includes `quality_gates` with `release-controller-ci` and `release-path-lints` while preserving existing release settings.
- A staging Release Controller run succeeds for commit `6a74b2ac08b199a4c2c0db54c3fc31708bd59261`.
- The staging run command plan and execution results show `quality-release-controller-ci` and `quality-release-path-lints` before build/deploy, both successful.
- Staging health is clean, prod current pointer remains unchanged, polling is re-enabled with `last_error=null`, and direct manual backend/factory deploy guards still fail.
