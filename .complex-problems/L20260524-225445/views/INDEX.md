# Complex Problem Ledger

Ledger: L20260524-225445
Schema: v6
Root: P000 - Fix WebRTC black screen across different networks
Status: doing
Updated: 2026-05-24T15:28:19+00:00

## Problem Tree
- [todo] P000: Fix WebRTC black screen across different networks
  - [done] P001: Audit and fix cross-network ICE/TURN discovery
    - [done] P004: Deploy and verify TURN credential endpoint
  - [done] P002: Fix connected-but-black WebRTC media behavior
  - [doing] P003: Deploy and verify cross-network WebRTC release

## Active
- [ ] P000: Fix WebRTC black screen across different networks (todo)
- [ ] P003: Deploy and verify cross-network WebRTC release (doing)

## Blocked

## Done
- [x] P001: Audit and fix cross-network ICE/TURN discovery
- [x] P002: Fix connected-but-black WebRTC media behavior
- [x] P004: Deploy and verify TURN credential endpoint

## Tickets
- [splitting] T000: Diagnose and repair cross-network WebRTC media path -> P000 (split)
- [done] T001: Repair namespace-safe ICE/TURN configuration -> P001 (one_go)
- [done] T002: Release fixed TURN discovery to prod and staging -> P004 (one_go)
- [done] T003: Make WebRTC media readiness explicit -> P002 (one_go)
- [executing] T004: Verify released WebRTC fixes across backend and OTA frontend -> P003 (one_go)

## Latest Checks
- [not_success] C000: P001 The implementation closes the discovered code/config bug, and the API host secret has been repaired, but the problem asked for deployed prod/staging ICE/TURN discovery to be working. The new Gateway route and fail-fast behavior are not yet running in prod/staging, so the deployed credential endpoint still has not been proven to return relay-capable ICE servers.
- [success] C001: P004 `R001` satisfies the follow-up problem: the fixed image was deployed through Release Controller, prod/staging now serve relay-capable TURN credentials, and namespace-specific runtime secrets are present.
- [success] C002: P001 The original ICE/TURN discovery problem is now solved. `R000` fixed the code path and guard behavior, and `R001` deployed and verified the repaired path in prod and staging.
- [success] C003: P002 `R002` solves the connected-but-black media behavior at the frontend state boundary: a WebRTC track is no longer treated as visible video, first-frame readiness is explicit, keyframes are requested immediately, and no-video becomes a clear error.
