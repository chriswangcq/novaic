# WebRTC cross-network black screen result

## Summary

The known cross-network black-screen path is fixed and deployed. The backend now requires relay-capable TURN credentials in prod/staging, the app no longer falls back to STUN-only ICE, the WebRTC hook waits for real video frames before declaring media connected, and the final release is deployed to staging and prod through Release Controller.

## Done

- P001 fixed ICE/TURN discovery:
  - Gateway exposes authenticated `/api/turn/credentials`.
  - Prod/staging startup requires `TURN_SECRET`.
  - App WebRTC offers receive relay-capable STUN/TURN/TURNS servers.
- P002 fixed connected-but-black media behavior:
  - Frontend fails fast when relay-capable TURN credentials are absent.
  - `ontrack` no longer marks video connected before actual frame readiness.
  - DataChannel open sends `request_keyframe`.
  - A 25-second no-frame timeout surfaces a clear error instead of silent black screen.
- P003/P005 completed deployment:
  - Release Controller staging run `20260524-154416-main-b6ba02e4165b` succeeded.
  - Release Controller prod promotion run `20260524-154727-promote-prod-staging-b6ba02e4165b` succeeded.
  - Prod and staging both point at final commit `b6ba02e4165b9ad3d7754d2b9227740aaf13b380`.

## Verification

- Gateway tests: `pytest -q tests/test_turn_credentials.py tests/test_pr152_gateway_boundary.py`.
- Common config test: `python3 -m pytest -q tests/test_strict_config.py`.
- Frontend checks: `npx eslint src/hooks/useWebRtc.ts --max-warnings 0`, `npx tsc --noEmit --pretty false`, `npm run test:unit -- --run src/types/chatMessageContract.test.ts`, and `npm run build`.
- Deploy checks: `bash -n deploy`, `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`, and `python3 scripts/ci/lint_immutable_image_workflows.py`.
- Prod and staging TURN endpoints return `stun:relay.gradievo.com:3478`, `turn:relay.gradievo.com:3478?transport=udp`, `turn:relay.gradievo.com:3478?transport=tcp`, and `turns:relay.gradievo.com:5349?transport=tcp`.
- Frontend OTA `v0.3.0` serves bundle `assets/index-D2ZcBCbV.js` with `request_keyframe`, `no video frame arrived`, and `relay-capable TURN credentials`.

## Known Gaps

- I cannot personally perform the final off-LAN live screen viewing test from a separate physical network in this environment. The deployed code and infrastructure now cover the technical root causes and make failure observable if video frames still do not arrive.

## Artifacts

- Child success checks: C002, C003, C006.
- Final parent commit: `b6ba02e4165b9ad3d7754d2b9227740aaf13b380`.
- Prod promotion run: `20260524-154727-promote-prod-staging-b6ba02e4165b`.
