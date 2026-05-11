# Verify production recovery after HD screenshot stall fix

## Problem Definition

P003 needs to prove that production no longer reproduces the HD screenshot/tool-completion stall after the code fix and deploy. The verification must cover local tests, deployment state, and durable queue/session evidence from a live smoke message.

## Proposed Solution

Use the already executed post-fix verification evidence and, if needed, run a small additional read-only production audit. Confirm that the final smoke progressed to normal session closure, related sagas completed, and no queue tasks remained failed or pending after the smoke window.

## Acceptance Criteria

- Local tests relevant to context step refs, externalized payloads, projection, and runtime cleanup are recorded as passing.
- Deployment is recorded as successful with worker roster healthy.
- Production smoke shows a clean terminal session state after the fix.
- No post-fix non-done queue tasks remain for the smoke window.

## Verification Plan

- Inspect recorded test and deploy evidence from `R001`.
- Query durable queue/session state for the final smoke window if necessary.
- Record a result mapping verification evidence to the P003 success criteria.

## Risks

- UI may show stale monitor cards even after backend session closure; durable queue state is the authority for this check.
- Historical failed task rows from before the fix may remain; the check must filter by post-fix smoke time.

## Assumptions

- The final smoke message `08ae61f4e3db` is the relevant post-fix production verification event.
- Durable queue/session state is sufficient to prove the harness progressed past the previously failing point.
