# Diagnose and repair deployed agent loop stall

## Problem Definition

The production agent runtime appears to stop making progress after one loop. The failure may be in dispatch, queue session FSM, saga/outbox workers, Cortex context/stack behavior, shell/Cortex bridge calls, or stale deployed process state. We need prove the exact failure mode before changing code.

## Proposed Solution

Follow a live-first diagnostic path: inspect deployed process status, fresh logs, queue database state, active sessions, inbox/outbox/saga rows, and recent Cortex/runtime calls; map the stuck state back to code; patch the smallest deterministic bug; add regression tests around the state transition; deploy and run end-to-end smoke.

## Acceptance Criteria

- Live backend evidence shows where the stuck loop is waiting or failing.
- Code-level root cause is identified and linked to the evidence.
- Fix is implemented in the responsible module with no hidden fallback that masks the issue.
- Regression coverage exercises the failing transition.
- Deployment and smoke/e2e prove the agent loop progresses beyond the former stall.

## Verification Plan

- Query remote process state and fresh logs for runtime workers and Cortex.
- Inspect `/opt/novaic/data/queue.db` for active sessions, pending inputs, outbox/saga rows, wake/session state, and failed attempts.
- Run local targeted tests for the touched runtime/Cortex modules.
- Deploy backend services and run remote smoke/e2e against real services.

## Risks

- Production contains old stuck rows unrelated to the current bug; diagnostics must distinguish stale history from current failure.
- A loop stall can be caused by multiple coupled issues; if the first fix is insufficient, create follow-up problems instead of declaring success.
- Smoke tests can prove infrastructure health but not every LLM behavior; verification must focus on harness state transitions.

## Assumptions

- SSH access to `api.gradievo.com` and local repository tests are available.
- It is acceptable to inspect production logs/database read-only during diagnosis.
- The desired fix should prioritize deterministic harness progress over backward compatibility.
