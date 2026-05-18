# Ticket: Classify dispatcher direct side-effect calls

## Problem Definition

Classify the direct `saga_orchestrator.create(...)` and `queue.publish(...)` calls inside `SessionOutboxDispatcher`. Determine whether each call is safely below durable outbox row ownership or a bypass risk.

## Proposed Solution

- Save focused source guard output for dispatcher direct calls.
- Inspect `SessionOutboxDispatcher.publish_effect`, `drain_pending`, `_publish_and_ack`, and `_publish`.
- Classify each direct call by reachability:
  - must read a durable outbox row first
  - must ack/fail the row through ledger
  - must preserve idempotency key
- Run focused tests if any code changes are needed.

## Acceptance Criteria

- Every dispatcher direct external side-effect call is classified.
- No dangerous dispatcher bypass remains unclassified.
- If no source change is needed, result explains why direct calls are safe implementation details.

## Verification Plan

- Cross-check source pointers and tests covering create wake, attach input, and recovery archive outbox delivery.
