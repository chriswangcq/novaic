# Generic task publish route boundary decision ticket

## Problem Definition

P485 must decide whether `queue_service/routes.py` `/tasks/publish` is an acceptable generic queue adapter boundary or a bypass that should be removed/tightened. It directly calls `queue.publish`, so it needs an explicit contract and guard evidence rather than implicit acceptance.

## Proposed Solution

Inspect the route schema, authentication/internal boundary, tests, and current usage assumptions. Decide one of: retain as generic adapter boundary with explicit guard/documentation, tighten the route contract, or remove/replace it. Prefer minimal source changes only if the route lacks an explicit guard proving it is generic infrastructure and not a session-owned FSM/outbox bypass.

## Acceptance Criteria

- Decision is recorded with file references and rationale.
- If retained, a regression guard/test proves the route remains generic queue infrastructure and does not contain session-owned special handling.
- If changed, focused route/queue tests pass.
- No ambiguous decision is left for P481.

## Verification Plan

Inspect `queue_service/routes.py` and relevant route/queue tests. Add or update a focused guard if current coverage does not make the boundary explicit. Run the focused test file(s) touched by the decision.

## Risks

- Removing the route may break internal tooling or tests that rely on generic task publish.
- Retaining without a guard could let future session-owned bypass logic creep into the route.

## Assumptions

- The route is internal infrastructure, but this ticket must verify and codify that assumption.
