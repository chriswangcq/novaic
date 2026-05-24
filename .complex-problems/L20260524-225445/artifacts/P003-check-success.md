# P003 cross-network WebRTC release success check

## Summary

P003 is successful after follow-up R004. The initial release attempt R003 exposed a deployment recovery gap; R004 closed that gap, released the final commit to staging, promoted the same image set to prod, and verified TURN credentials plus frontend OTA markers.

## Evidence

- R003 proved the final images could build and push but identified the staging Compose corruption gap.
- R004 added recovery logic and health-based release convergence.
- Release Controller staging run `20260524-154416-main-b6ba02e4165b` succeeded.
- Release Controller prod promotion run `20260524-154727-promote-prod-staging-b6ba02e4165b` succeeded.
- Prod and staging Release Controller pointers both reference `b6ba02e4165b9ad3d7754d2b9227740aaf13b380`.
- Prod and staging `/api/turn/credentials` return TTL `86400` and STUN/TURN/TURNS URLs for `relay.gradievo.com`.
- Frontend OTA `v0.3.0` serves bundle `assets/index-D2ZcBCbV.js` containing the new WebRTC markers.

## Criteria Map

- Deploy final WebRTC backend to staging: satisfied by `20260524-154416-main-b6ba02e4165b`.
- Promote the same release to prod: satisfied by `20260524-154727-promote-prod-staging-b6ba02e4165b`.
- Verify TURN credential endpoint on prod and staging: satisfied by direct Gateway checks returning `stun:`, `turn:`, and `turns:` relay URLs.
- Verify frontend OTA contains no-fallback and media-readiness changes: satisfied by deployed bundle marker checks.
- Avoid manual backend release path: satisfied because staging and prod backend/factory changes were executed by Release Controller internal deploy steps.

## Execution Map

- R003: first final-release attempt and precise deployment gap capture.
- R004: recovery implementation, successful Release Controller staging/prod deployment, and verification evidence.

## Stress Test

- The deployment path was tested against the actual corrupt staging Compose state created by failed releases. The final successful run handled the transient Compose return-code failure by waiting for service health and completed staging smoke.
- Prod promotion used the same code path and health gate, then passed `https://api.gradievo.com/health`.

## Residual Risk

- A live off-LAN WebRTC video session still needs user-side experiential confirmation because I cannot initiate a real client screen session from a separate network here.
- The deploy and runtime evidence directly covers the known failure class: missing relay-capable ICE credentials plus connected/no-frame ambiguity.

## Result IDs

- R003
- R004
