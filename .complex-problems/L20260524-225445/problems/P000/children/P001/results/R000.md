# ICE/TURN configuration repaired

## Summary

The cross-network WebRTC path was missing a relay-capable TURN configuration. The browser tried `/api/turn/credentials`, but the deployed Gateway returned 404, then the app silently fell back to STUN-only. The Gateway also did not have `turn_secret` in `/opt/novaic/etc/secrets.json`, so App WS offer relay could not inject TURN servers for VmControl either. Coturn itself was running on the API host and `relay.gradievo.com` resolved to that host.

## Done

- Added authenticated `GET /api/turn/credentials` in Gateway.
- Centralized Gateway TURN ICE server construction for both browser credentials and App WS offer relay.
- Included UDP TURN, TCP TURN, and TLS TURN URLs.
- Added `services.turn.tls_port` to the strict service config and tests.
- Changed the frontend WebRTC hook to require relay-capable TURN credentials instead of silently using STUN-only.
- Added deployed-environment fail-fast validation: `prod`, `staging`, and `preview-pr-*` Gateway runtimes require `turn_secret`.
- Updated the API host `/opt/novaic/etc/secrets.json` with the coturn `static-auth-secret` as `turn_secret`.

## Verification

- `pytest -q tests/test_turn_credentials.py tests/test_pr152_gateway_boundary.py` in `novaic-gateway`: passed, 16 tests.
- `python3 -m pytest -q tests/test_strict_config.py` in `novaic-common`: passed, 10 tests.
- `npx eslint src/hooks/useWebRtc.ts --max-warnings 0` in `novaic-app`: passed.
- `npx tsc --noEmit --pretty false` in `novaic-app`: still fails on pre-existing `src/types/messageContract.test.ts` missing `MESSAGE_LIFECYCLE_STATES`; no new `useWebRtc.ts` error was reported.
- API host checks showed `novaic-coturn` running, `turnserver.conf` using `external-ip=43.106.113.95/172.17.220.140`, and `api.gradievo.com`/`relay.gradievo.com` resolving to `43.106.113.95` from the API host.
- Direct Gateway checks before this code deploy confirmed `http://127.0.0.1:19999/api/turn/credentials` and staging `:29999` were 404, matching the missing route diagnosis.

## Known Gaps

- The new Gateway/app/common code is not deployed yet; deployment belongs to the release/deploy child problem.
- Cross-network media still needs end-to-end verification after deployment, because ICE repair removes the main relay gap but black screen can also come from media/keyframe readiness.

## Artifacts

- `novaic-gateway/gateway/api/turn.py`
- `novaic-gateway/gateway/api/app_client.py`
- `novaic-gateway/main_gateway.py`
- `novaic-gateway/tests/test_turn_credentials.py`
- `novaic-common/common/config.py`
- `novaic-common/config/services.json`
- `novaic-common/tests/test_strict_config.py`
- `novaic-app/src/hooks/useWebRtc.ts`
