# Verify live agent loop recovery

## Problem

Production had an already-stale active session. After deployment, verify that the old stuck condition is gone or recovered and that the same agent-loop path does not fail with internal-key, missing-step-ref, or bad-finalize errors.

## Success Criteria

- Recent logs do not show the previous recurrence signatures after deploy.
- Queue DB/session state is not left in a stale active failed state for the tested path.
- A smoke action proves the repaired shell/context/finalize chain can progress.
