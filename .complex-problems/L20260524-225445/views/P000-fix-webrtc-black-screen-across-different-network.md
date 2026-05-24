# P000: Fix WebRTC black screen across different networks

Status: todo
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
When the viewer and the controlled NovAIC desktop device are not on the same LAN, the WebRTC connection can report connected but render a black screen. This affects host desktop viewing/control and makes remote use unreliable across NAT/public network boundaries. Diagnose the signaling, ICE/TURN, media pipeline, and frontend receiver path, then implement the smallest correct fix that makes cross-network WebRTC use relay-capable and avoids connected-but-no-video failure modes.

## Success Criteria
- WebRTC session setup uses valid relay-capable ICE/TURN configuration for non-LAN clients, not just host/local/mDNS candidates.
- The app can detect or avoid the connected-but-no-video black-screen state with clear signaling or recovery behavior.
- The fix preserves same-LAN WebRTC behavior.
- The implementation is covered by focused tests or compile/type checks for the touched layers.
- Evidence is recorded for production/staging configuration needed by the fix, including coturn/release-controller deployment implications if any.

## Subproblems
- P001: Audit and fix cross-network ICE/TURN discovery
- P002: Fix connected-but-black WebRTC media behavior
- P003: Deploy and verify cross-network WebRTC release

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md

## Follow-ups
- none
