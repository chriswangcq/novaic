# Deploy repair and run production smoke

## Problem Definition

The code and tests are ready, but production still needs the repair deployed and verified against the real message dispatch/runtime path.

## Proposed Solution

Use the repo deployment entrypoint to deploy the affected services, then perform production smoke checks:

1. Deploy backend services with `./deploy services` or the smallest safe target that includes `novaic-common`, `novaic-business`, and `novaic-agent-runtime`.
2. Verify process/log freshness with existing deploy smoke.
3. Send or inject a controlled IM through the existing production APIs/data path.
4. Query Entangled and Queue DBs plus logs to prove the message reaches queue/session runtime state.

## Acceptance Criteria

- Deployment succeeds.
- Services and worker roster are healthy after restart.
- Production smoke input does not reproduce the previous notification `failed` / dispatch timeout behavior.
- Queue/session state records activity for the smoke input.
- Any residual blocker is recorded with exact evidence.

## Verification Plan

- Run targeted deploy status/fresh smoke.
- Query production DB and logs around smoke timestamp.
- Record exact IDs observed.

## Risks

- End-to-end LLM reply can still depend on provider availability; if provider fails after runtime activity, that is a different failure.
- Existing stale failed notification/saga rows may remain in DB; smoke must use a fresh message ID.

## Assumptions

- `./deploy services` is acceptable because common, business, and runtime all changed or need restart.
