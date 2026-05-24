# Complex Problem Ledger

Ledger: L20260524-225445
Schema: v6
Root: P000 - Fix WebRTC black screen across different networks
Status: done
Updated: 2026-05-24T15:52:33+00:00

## Problem Tree
- [done] P000: Fix WebRTC black screen across different networks
  - [done] P001: Audit and fix cross-network ICE/TURN discovery
    - [done] P004: Deploy and verify TURN credential endpoint
  - [done] P002: Fix connected-but-black WebRTC media behavior
  - [done] P003: Deploy and verify cross-network WebRTC release
    - [done] P005: Make image release recover from corrupt staging Compose state

## Active

## Blocked

## Done
- [x] P000: Fix WebRTC black screen across different networks
- [x] P001: Audit and fix cross-network ICE/TURN discovery
- [x] P002: Fix connected-but-black WebRTC media behavior
- [x] P003: Deploy and verify cross-network WebRTC release
- [x] P004: Deploy and verify TURN credential endpoint
- [x] P005: Make image release recover from corrupt staging Compose state

## Tickets
- [done] T000: Diagnose and repair cross-network WebRTC media path -> P000 (split)
- [done] T001: Repair namespace-safe ICE/TURN configuration -> P001 (one_go)
- [done] T002: Release fixed TURN discovery to prod and staging -> P004 (one_go)
- [done] T003: Make WebRTC media readiness explicit -> P002 (one_go)
- [done] T004: Verify released WebRTC fixes across backend and OTA frontend -> P003 (one_go)
- [done] T005: Add namespace-scoped Compose release recovery -> P005 (one_go)

## Latest Checks
- [not_success] C000: P001 The implementation closes the discovered code/config bug, and the API host secret has been repaired, but the problem asked for deployed prod/staging ICE/TURN discovery to be working. The new Gateway route and fail-fast behavior are not yet running in prod/staging, so the deployed credential endpoint still has not been proven to return relay-capable ICE servers.
- [success] C001: P004 `R001` satisfies the follow-up problem: the fixed image was deployed through Release Controller, prod/staging now serve relay-capable TURN credentials, and namespace-specific runtime secrets are present.
- [success] C002: P001 The original ICE/TURN discovery problem is now solved. `R000` fixed the code path and guard behavior, and `R001` deployed and verified the repaired path in prod and staging.
- [success] C003: P002 `R002` solves the connected-but-black media behavior at the frontend state boundary: a WebRTC track is no longer treated as visible video, first-frame readiness is explicit, keyframes are requested immediately, and no-video becomes a clear error.
- [not_success] C004: P003 P003 is not solved by result R003. The final release image was built and pushed, but staging deployment failed in Docker Compose before smoke verification, so the final commit cannot be promoted to prod yet.
- [success] C005: P005 P005 is successful. The deployment path now has namespace-scoped recovery and health-based convergence, and the final commit was released to staging and promoted to prod through Release Controller.
- [success] C006: P003 P003 is successful after follow-up R004. The initial release attempt R003 exposed a deployment recovery gap; R004 closed that gap, released the final commit to staging, promoted the same image set to prod, and verified TURN credentials plus frontend OTA markers.
- [success] C007: P000 P000 is successful. The likely root causes of off-LAN black screen were removed: relay-capable TURN is now required and served, STUN-only fallback is gone, the app waits for actual video frames, and the complete fix is deployed to both staging and prod through Release Controller.
