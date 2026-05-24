# Audit and fix cross-network ICE/TURN discovery

## Problem

WebRTC works on the same LAN but shows a black screen across different networks, which strongly suggests that signaling may complete while ICE candidates, relay candidates, TURN credentials, or advertised ICE server configuration are incomplete or incorrect for NAT traversal.

## Success Criteria

- Identify the exact path that provides ICE servers from deployed backend/config to the app and Rust peer.
- Confirm whether a reachable TURN relay is deployed, configured, and advertised to both sides.
- Fix missing or incorrect ICE/TURN config so cross-network peers can negotiate relay candidates without relying on LAN host candidates.
- Add a guard or test that fails when production/staging WebRTC config does not include namespace-appropriate relay-capable ICE servers.
- Document the operational knobs needed for TURN host, ports, credentials, and namespace-specific rollout.
