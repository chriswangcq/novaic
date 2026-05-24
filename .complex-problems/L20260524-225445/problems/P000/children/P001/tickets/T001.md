# Repair namespace-safe ICE/TURN configuration

## Problem Definition

Cross-network WebRTC can connect at the signaling layer while rendering black video if the deployed app and Rust peer do not receive relay-capable ICE servers or if TURN is not reachable from both peers. Same-LAN success can hide this because host candidates are enough on LAN.

## Proposed Solution

Trace the ICE server source of truth across app, backend, Rust WebRTC peer, deployment env, coturn container, and API host ingress. Make TURN relay mandatory for deployed non-local environments, normalize how ICE servers are passed into WebRTC peer creation, and add validation so prod/staging cannot silently run with LAN-only ICE config.

## Acceptance Criteria

- The code path serving and consuming ICE servers is identified with file/function evidence.
- Deployed prod/staging config advertises a reachable STUN/TURN set, including relay URLs usable outside the LAN.
- Missing TURN config fails loudly in deployed environments instead of falling back to LAN-only behavior.
- A focused test or guard covers the required ICE/TURN config shape.
- Any required host-infra/coturn deployment change is documented for the release-controller flow.

## Verification Plan

Run targeted repository tests/guards for ICE config, inspect the rendered compose/env config, query the deployed API endpoint that returns ICE servers if one exists, and verify coturn is running/listening on the API host.

## Risks

- Existing local development may rely on implicit host-candidate-only behavior and needs a clear local-mode exception.
- Coturn credential generation may live outside the app repo and require deploy-script updates.
- Browsers may hide host candidates behind mDNS, so validation must focus on relay candidates rather than host candidates.

## Assumptions

- Cross-network black screen is at least partly caused by ICE/TURN relay gaps until proven otherwise.
- Same-LAN should keep working after making deployed TURN config explicit.
