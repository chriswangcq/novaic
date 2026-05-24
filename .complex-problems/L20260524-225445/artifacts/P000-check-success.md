# WebRTC cross-network black screen success check

## Summary

P000 is successful. The likely root causes of off-LAN black screen were removed: relay-capable TURN is now required and served, STUN-only fallback is gone, the app waits for actual video frames, and the complete fix is deployed to both staging and prod through Release Controller.

## Evidence

- P001 success check C002 covers backend TURN credential generation and deployment.
- P002 success check C003 covers frontend media readiness and no-fallback behavior.
- P003 success check C006 covers final staging/prod deployment and verification.
- Prod and staging Release Controller current pointers both reference `b6ba02e4165b9ad3d7754d2b9227740aaf13b380`.
- Prod and staging TURN endpoints return `stun:`, `turn:`, and `turns:` URLs for `relay.gradievo.com`.
- The deployed frontend OTA bundle contains the new WebRTC request-keyframe, no-video-frame timeout, and relay-capable TURN enforcement markers.

## Criteria Map

- WebRTC off-LAN must not silently use STUN-only ICE: satisfied by hard failure when relay-capable TURN credentials are absent.
- Backend must provide usable relay credentials in prod/staging: satisfied by deployed `/api/turn/credentials` responses and `TURN_SECRET` startup guard.
- Connected-but-black must be observable and actively remediated: satisfied by video-frame readiness gating, `request_keyframe`, and no-frame timeout.
- Fix must be deployed through the intended release path: satisfied by Release Controller staging run and prod promotion run.
- Old/manual deployment residue must not be the path used for this release: satisfied because backend/factory deploy steps ran as Release Controller internal executors.

## Execution Map

- R005 summarizes child problem results C002, C003, and C006.

## Stress Test

- The release was tested against a real corrupt Docker Compose staging state during deployment; recovery and health-gated release succeeded.
- Both namespaces were checked after deployment, so prod/staging isolation did not hide a staging-only success.

## Residual Risk

- A physical off-LAN viewing session is still the final experiential test. If the screen still appears black after this release, the app should now surface a precise no-frame timeout instead of silently showing a connected black screen, which gives the next diagnosis a concrete signal.

## Result IDs

- R005
