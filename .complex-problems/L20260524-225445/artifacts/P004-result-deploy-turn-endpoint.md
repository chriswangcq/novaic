# TURN endpoint deployed and verified

## Summary

The fixed TURN discovery code was committed, pushed, built by Release Controller as immutable `sha-163a782cb385` images, deployed to staging, then promoted to prod using the same image refs. Prod and staging now return relay-capable ICE server credentials.

## Done

- Committed and pushed `novaic-gateway` commit `ece234f` (`Require TURN credentials for WebRTC`).
- Committed and pushed `novaic-common` commit `a56ad28` (`Add TURN TLS port config`).
- Committed and pushed `novaic-app` commit `610b407` (`Require TURN relay credentials for WebRTC`).
- Committed and pushed parent repo commit `163a782c` (`Fix WebRTC TURN discovery path`).
- Added `turn_secret` to `/opt/novaic/etc/staging/secrets.json` and `/opt/novaic/etc/prod/secrets.json`, matching coturn static auth secret.
- Release Controller staging run succeeded: `20260524-151622-main-163a782cb385`.
- Release Controller prod promote succeeded: `20260524-151846-promote-prod-staging-163a782cb385`.

## Verification

- Release Controller status now points both `staging` and `prod` to commit `163a782cb385` and API image `127.0.0.1:5000/novaic/api-backend:sha-163a782cb385`.
- Direct prod Gateway check `http://127.0.0.1:19999/api/turn/credentials` with `X-User-ID` returned TTL `86400` and TURN URLs:
  - `turn:relay.gradievo.com:3478?transport=udp`
  - `turn:relay.gradievo.com:3478?transport=tcp`
  - `turns:relay.gradievo.com:5349?transport=tcp`
- Direct staging Gateway check `http://127.0.0.1:29999/api/turn/credentials` returned the same relay-capable TURN URLs.
- Prod Release Controller smoke `https://api.gradievo.com/health` succeeded.
- Staging initially failed fast exactly as intended when namespace-specific `turn_secret` was absent, then succeeded after the correct namespace secret file was repaired.

## Known Gaps

- This verifies ICE/TURN discovery and deployment. It does not yet prove first video frame rendering across an actual different-network WebRTC session; that belongs to the media/black-screen child problem.

## Artifacts

- Release Controller staging run `20260524-151622-main-163a782cb385`
- Release Controller prod run `20260524-151846-promote-prod-staging-163a782cb385`
- Parent repo commit `163a782cb3859b6e8d2528a26ad59bcf50480f85`
