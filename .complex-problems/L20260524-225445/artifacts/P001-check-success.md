# ICE/TURN discovery solved

## Summary

The original ICE/TURN discovery problem is now solved. `R000` fixed the code path and guard behavior, and `R001` deployed and verified the repaired path in prod and staging.

## Evidence

- Gateway now exposes authenticated `/api/turn/credentials`.
- Browser-side WebRTC no longer silently falls back to STUN-only when TURN credentials are missing.
- Gateway App WS offer relay now injects the same relay-capable ICE server set into VmControl offers.
- Prod and staging runtime secrets include `turn_secret` in namespace-specific secret files.
- Prod and staging direct Gateway checks return `turn:relay.gradievo.com:3478?transport=udp`, `turn:relay.gradievo.com:3478?transport=tcp`, and `turns:relay.gradievo.com:5349?transport=tcp`.

## Criteria Map

- Identify ICE server source of truth: satisfied by code trace and central `gateway.api.turn.build_turn_ice_servers`.
- Confirm reachable TURN relay deployed/configured/advertised: satisfied by coturn/DNS checks and prod/staging endpoint responses.
- Fix missing ICE/TURN config: satisfied by Gateway endpoint, App WS injection, app TURN requirement, and namespace secret repair.
- Add guard/test: satisfied by Gateway tests, common strict config tests, and deployed fail-fast validation.
- Document operational knobs: captured in `R000`/`R001` artifacts with `turn_secret`, `turn` URLs, `tls_port`, namespace secret paths, and coturn relationship.

## Execution Map

- `R000` contains local code changes and verification.
- `R001` contains Release Controller deployment and endpoint verification.

## Stress Test

- Staging failed when `turn_secret` was absent in `/opt/novaic/etc/staging/secrets.json`, then recovered after the namespace secret was repaired. This proves the new path fails loudly instead of running a hidden STUN-only degradation.

## Residual Risk

- ICE/TURN discovery is fixed; actual cross-network first video frame still needs media-path validation in the separate black-screen child problem.

## Result IDs

- R000
- R001
