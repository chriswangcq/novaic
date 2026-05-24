# TURN endpoint deployment succeeded

## Summary

`R001` satisfies the follow-up problem: the fixed image was deployed through Release Controller, prod/staging now serve relay-capable TURN credentials, and namespace-specific runtime secrets are present.

## Evidence

- Staging Release Controller run `20260524-151622-main-163a782cb385` succeeded.
- Prod Release Controller promote run `20260524-151846-promote-prod-staging-163a782cb385` succeeded.
- Prod and staging current release pointers both reference commit `163a782cb385` and image `127.0.0.1:5000/novaic/api-backend:sha-163a782cb385`.
- Prod and staging loopback TURN credential checks returned `turn:` and `turns:` URLs.

## Criteria Map

- Deploy new image via Release Controller: satisfied by staging run and prod promote.
- Verify `/api/turn/credentials` returns relay-capable ICE servers: satisfied by direct prod/staging checks.
- Verify `turn_secret` is present: satisfied by the repaired namespace secret files and successful fail-fast startup.
- Confirm no STUN-only silent fallback in deployed cross-network mode: satisfied by app code requiring relay-capable credentials and Gateway failing deployed envs without `turn_secret`.

## Execution Map

- `R001` records commits, pushes, Release Controller run IDs, and remote endpoint verification.

## Stress Test

- Staging initially failed to start without namespace `turn_secret`, proving the new guard detects the dangerous misconfiguration instead of serving a degraded STUN-only path.

## Residual Risk

- Actual cross-network first-frame rendering still needs the separate media-path check; this follow-up only closes TURN discovery deployment.

## Result IDs

- R001
