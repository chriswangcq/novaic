# Deploy and verify message response recovery

## Problem

If the fix affects backend or frontend runtime behavior, release it through the correct deployment path and verify that the message pipeline no longer silently stalls.

## Success Criteria

- Backend changes, if any, are deployed through Release Controller.
- Frontend changes, if any, are built and deployed through the current OTA/frontend path.
- Prod/staging health checks pass.
- The diagnosed failure no longer reproduces, or the system now exposes a concrete actionable error instead of silent no-response.
