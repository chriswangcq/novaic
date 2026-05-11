# Deploy and verify repaired agent loop

## Problem Definition

The code repair prevents the identified failure chain locally, but production currently has a stale active session and must be deployed and verified end to end.

## Proposed Solution

Split deployment verification into:

1. Deploy repaired runtime/Cortex code to the backend and restart services cleanly.
2. Verify backend health, inspect stale session recovery state, and smoke-test that a new agent-loop message can progress without the previous auth/step-ref/finalize failures.

## Acceptance Criteria

- Backend deployment completes and all services/workers are running.
- Fresh logs confirm restarted services are active.
- Queue/session state is no longer wedged by the old failed wake, or an explicit recovery path is triggered and verified.
- A smoke path confirms shell capability `agentctl` can read IM/meta without 401 and does not reproduce missing `step_ref` or wake-finalize root-scope errors.

## Verification Plan

- Run `./deploy services` or the minimal safe backend deployment path that syncs both `novaic-agent-runtime` and `novaic-cortex`.
- Run `./deploy status` and fresh-smoke checks.
- Inspect queue DB and recent logs for recurrence signatures.
- Run a targeted smoke command/API path if available.

## Risks

- Existing stale active session may need recovery after deployment; code fix alone may not clear historical failed saga state.
- Production smoke may depend on external model/provider availability.

## Assumptions

- Deployment via repository `./deploy` is the supported backend deployment path.
