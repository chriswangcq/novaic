# P001: Audit and fix cross-network ICE/TURN discovery

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
WebRTC works on the same LAN but shows a black screen across different networks, which strongly suggests that signaling may complete while ICE candidates, relay candidates, TURN credentials, or advertised ICE server configuration are incomplete or incorrect for NAT traversal.

## Success Criteria
- Identify the exact path that provides ICE servers from deployed backend/config to the app and Rust peer.
- Confirm whether a reachable TURN relay is deployed, configured, and advertised to both sides.
- Fix missing or incorrect ICE/TURN config so cross-network peers can negotiate relay candidates without relying on LAN host candidates.
- Add a guard or test that fails when production/staging WebRTC config does not include namespace-appropriate relay-capable ICE servers.
- Document the operational knobs needed for TURN host, ports, credentials, and namespace-specific rollout.

## Subproblems
- P004: Deploy and verify TURN credential endpoint

## Results
- R000

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md
- Check C002: problems/P000/children/P001/checks/C002.md

## Follow-ups
- P004: Deploy and verify TURN credential endpoint
