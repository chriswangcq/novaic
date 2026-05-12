# Repair production IM delivery and session replay failure

## Problem Definition

The production no-response incident is not a single UI symptom. It has three coupled backend failure modes:

- Log storm filled disk, Redis entered MISCONF, and Cortex scope writes failed.
- The subscriber marked the IM notification as delivered even though session initialization failed before the wake could consume it normally.
- Replaying the same input idempotency key could update `tq_session_state` to a fresh active/starting scope without creating a corresponding event/outbox, because the generic FSM runner did not distinguish inserted events from idempotent duplicates.

## Proposed Solution

Repair production state, then patch the durable FSM substrate and logging layer:

- Confirm the message, notification, session, saga, and task state in production.
- Keep the operational recovery evidence in the result.
- Change the generic FSM SQLite store/runner so an idempotent duplicate event returns the existing event and skips materialized state and outbox writes.
- Suppress successful high-frequency internal polling access logs and noisy HTTP client dependency logs.
- Add regression tests for the FSM replay contract and logging suppression.
- Deploy and verify production disk, Redis, session state, notification state, and recent logs.

## Acceptance Criteria

- Duplicate FSM transition event idempotency does not mutate state to a new scope.
- Duplicate FSM transition event idempotency does not append or reuse a new outbox effect as if it were a fresh transition.
- Successful `/api/queue/tasks/claim` and `/api/queue/sagas/claim` internal access logs are suppressed, while failures remain visible.
- `httpx`, `httpcore`, and `uvicorn.access` are quieted to warning level by service logging bootstrap.
- Production is deployed and checked after the patch.

## Verification Plan

- Add a unit test around `FsmTransitionRunner` and `FsmSqliteStore` replay behavior.
- Add or extend common logging tests for hot claim path suppression and dependency logger levels.
- Run targeted runtime/common pytest.
- Deploy runtime/common services.
- Query production SQLite state and inspect logs after deployment.

## Risks

- Logging suppression must not hide error logs for failed claims.
- FSM idempotency change is generic infrastructure; tests must prove duplicate event replay is a no-op for state/outbox.
- Existing ledgers using `append_event()` directly should preserve the original return contract.

## Assumptions

- Production code is deployed from the current repository checkout through `./deploy runtime`.
- The correct user-facing agent ID for the incident is `340ea813-2398-4b50-b2b8-16a6975af1f9`.
