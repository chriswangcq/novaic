# Dispatcher direct call classification

## Problem

Classify direct `saga_orchestrator.create(...)` and `queue.publish(...)` calls inside `SessionOutboxDispatcher` and verify whether they are safe implementation details below durable outbox ownership.

## Success Criteria

- Save source guard output for dispatcher direct calls.
- Classify each direct call with file references.
- If any call can be reached without a durable outbox row, create/fix a concrete follow-up.
- Run focused tests if source changes are made.
