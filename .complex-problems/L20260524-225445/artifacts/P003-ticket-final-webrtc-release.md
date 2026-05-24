# Verify released WebRTC fixes across backend and OTA frontend

## Problem Definition

The TURN backend fix and frontend media-readiness fix have been implemented and deployed through their respective release paths, but the root release state must be verified and recorded as one coherent WebRTC release.

## Proposed Solution

Confirm Release Controller prod/staging pointers, verify TURN endpoints in both namespaces, verify OTA frontend bundle contains the media readiness changes, commit the final parent repo pointer and ledger updates, and record any remaining need for a real outside-LAN manual session test.

## Acceptance Criteria

- Prod and staging backend releases point to the fixed immutable image containing the TURN endpoint.
- Frontend OTA v0.3.0 is deployed from a build containing `useWebRtc` media readiness behavior.
- Parent repo records the latest `novaic-app` submodule pointer and ledger updates.
- Focused local checks and remote smoke checks are listed with outcomes.
- Any remaining cross-network manual validation gap is explicit.

## Verification Plan

Use Release Controller `/v1/status`, direct prod/staging `/api/turn/credentials`, remote OTA asset inspection, local `git status`, and build/test outputs already captured in P001/P002.

## Risks

- A true cross-network WebRTC screen session cannot be fully proven without a client on a different network initiating the stream.
- Frontend OTA is still deployed through the existing OTA deploy target, not Release Controller.

## Assumptions

- Backend Release Controller and frontend OTA are the two current authoritative deployment mechanisms for this combined WebRTC release.
