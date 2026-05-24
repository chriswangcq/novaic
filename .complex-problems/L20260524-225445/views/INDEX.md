# Complex Problem Ledger

Ledger: L20260524-225445
Schema: v6
Root: P000 - Fix WebRTC black screen across different networks
Status: doing
Updated: 2026-05-24T15:07:30+00:00

## Problem Tree
- [todo] P000: Fix WebRTC black screen across different networks
  - [followup] P001: Audit and fix cross-network ICE/TURN discovery
    - [doing] P004: Deploy and verify TURN credential endpoint
  - [todo] P002: Fix connected-but-black WebRTC media behavior
  - [todo] P003: Deploy and verify cross-network WebRTC release

## Active
- [ ] P000: Fix WebRTC black screen across different networks (todo)
- [ ] P001: Audit and fix cross-network ICE/TURN discovery (followup)
- [ ] P002: Fix connected-but-black WebRTC media behavior (todo)
- [ ] P003: Deploy and verify cross-network WebRTC release (todo)
- [ ] P004: Deploy and verify TURN credential endpoint (doing)

## Blocked

## Done

## Tickets
- [splitting] T000: Diagnose and repair cross-network WebRTC media path -> P000 (split)
- [done] T001: Repair namespace-safe ICE/TURN configuration -> P001 (one_go)
- [executing] T002: Release fixed TURN discovery to prod and staging -> P004 (one_go)

## Latest Checks
- [not_success] C000: P001 The implementation closes the discovered code/config bug, and the API host secret has been repaired, but the problem asked for deployed prod/staging ICE/TURN discovery to be working. The new Gateway route and fail-fast behavior are not yet running in prod/staging, so the deployed credential endpoint still has not been proven to return relay-capable ICE servers.
