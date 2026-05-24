# Compose release recovery result

## Summary

The image release path now survives the observed Docker Compose recreate race and the final WebRTC release was deployed through Release Controller. The deploy script starts `service-registry` first, waits for key services to become healthy, treats Docker Compose transient non-zero exits as recoverable only when service health proves convergence, and still keeps namespace-scoped reset as the retry path for genuinely corrupt project state.

## Done

- Added `reset_api_backend_compose_project()` to clean only the requested `novaic-<namespace>` Compose project.
- Added `start_api_backend_release()` to bootstrap `service-registry` before starting the full API backend stack.
- Added `wait_api_backend_release_healthy()` and `wait_api_backend_compose_service_healthy()` so release success is judged by key service health rather than a Docker Compose transient return code alone.
- Updated Release Controller CI guard and deployment runbook to document and lock the recovery behavior.
- Committed and pushed recovery fixes:
  - `9b2904354253` `Make image deploy recover Compose state`
  - `203119f4196a` `Start registry before backend release`
  - `b6ba02e4165b` `Judge backend release by service health`
- Released final commit `b6ba02e4165b9ad3d7754d2b9227740aaf13b380` to staging through Release Controller.
- Promoted the exact same API and Factory images from staging to prod through Release Controller.

## Verification

- Local checks passed:
  - `bash -n deploy`
  - `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`
  - `python3 scripts/ci/lint_immutable_image_workflows.py`
- Staging Release Controller run `20260524-154416-main-b6ba02e4165b` succeeded.
- Prod promotion run `20260524-154727-promote-prod-staging-b6ba02e4165b` succeeded.
- Release Controller current pointers:
  - `staging -> b6ba02e4165b`
  - `prod -> b6ba02e4165b`
- Prod and staging `/api/turn/credentials` both return TTL `86400` and these relay URLs:
  - `stun:relay.gradievo.com:3478`
  - `turn:relay.gradievo.com:3478?transport=udp`
  - `turn:relay.gradievo.com:3478?transport=tcp`
  - `turns:relay.gradievo.com:5349?transport=tcp`
- Frontend OTA `v0.3.0` references `assets/index-D2ZcBCbV.js`; the deployed bundle contains `request_keyframe`, `no video frame arrived`, and `relay-capable TURN credentials`.

## Known Gaps

- I could not personally perform a live off-LAN screen session from a separate network in this environment. The deployed changes remove the known cross-network ICE/TURN fallback failure and add an explicit no-frame error path, but a real user-device WebRTC session is still the final experiential confirmation.

## Artifacts

- Release Controller staging run: `20260524-154416-main-b6ba02e4165b`.
- Release Controller prod promotion run: `20260524-154727-promote-prod-staging-b6ba02e4165b`.
- Final parent commit: `b6ba02e4165b9ad3d7754d2b9227740aaf13b380`.
- Staging API image: `127.0.0.1:5000/novaic/api-backend:sha-b6ba02e4165b`.
- Staging Factory image: `127.0.0.1:5000/novaic/llm-factory:sha-b6ba02e4165b`.
