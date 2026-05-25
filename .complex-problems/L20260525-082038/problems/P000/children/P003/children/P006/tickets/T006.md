# Verify production message recovery

## Problem Definition

The fixed prod deployment must be proven to recover the previously stuck Environment notification dispatch path and leave the message pipeline healthy.

## Proposed Solution

Inspect post-deploy Entangled logs, subscriber logs/metrics, queue diagnostics, and health endpoints. Verify the old duplicate `updated_at` error stops and the subscriber can claim or deliver notifications.

## Acceptance Criteria

- No post-deploy Entangled `multiple assignments to same column "updated_at"` errors.
- Subscriber no longer loops on PATCH 500 for `environment-notifications/81acac494a82`.
- Subscriber metrics or logs show successful claim/delivery or empty healthy polling after recovery.
- Queue diagnostics are healthy with no unexpected stuck sessions or pending inputs.
- Health endpoints remain green.

## Verification Plan

Use `docker logs`, `/metrics`, Queue `/sessions` and `/pending`, and public/internal health endpoints after prod promotion.

## Risks

- If no new user message is sent after deploy, verification may rely on the formerly stuck notification and service metrics rather than a fresh manual chat send.

## Assumptions

- The previously stuck notification is sufficient evidence for recovery if it is no longer producing Entangled PATCH 500 loops.
