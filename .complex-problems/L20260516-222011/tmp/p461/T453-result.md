# T453 Result: Dispatcher direct side-effect call classification

## Summary

Classified direct external calls inside `SessionOutboxDispatcher`. They are safe implementation details below durable outbox ownership: each publication path is reached only after reading a durable `tq_session_outbox` row and is acked/failed through the session ledger. No dispatcher direct-call bypass was found.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p461/dispatcher-direct-call-guard.txt` (`66` lines).

## Classification

| Direct Call | File Reference | Classification | Reason |
| --- | --- | --- | --- |
| `saga_orchestrator.create(...)` | `novaic-agent-runtime/queue_service/session_outbox.py:186` | Safe implementation detail below durable outbox | Reached only from `_publish_create_wake_saga`, which is selected by `_publish(...)` after `drain_pending(...)` / `publish_effect(...)` obtains a durable row. Row is acked by `_publish_and_ack(...)` or failed by `_mark_failed(...)`. |
| `queue.publish(TaskTopics.CORTEX_SCOPE_END, ...)` | `novaic-agent-runtime/queue_service/session_outbox.py:213` | Safe implementation detail below durable outbox | Reached only through `RECOVERY_ARCHIVE_SCOPE` outbox delivery. Payload requires `scope_id`, positive `session_generation`, and `remaining_stack`; publication uses row idempotency key. |
| `queue.publish(TaskTopics.SESSION_ATTACH_INPUT, ...)` | `novaic-agent-runtime/queue_service/session_outbox.py:256` | Safe implementation detail below durable outbox | Reached only through `PUBLISH_ATTACH_INPUT` outbox delivery. Payload requires message IDs, scope, positive `expected_session_generation`, agent/subagent identity; publication uses row idempotency key. |

## Ownership Chain

- Durable row listing: `session_outbox.py:59-70`.
- Durable single-row fetch: `session_outbox.py:92-111`.
- Ack path: `session_outbox.py:120-127`.
- Failure/dead-letter path: `session_outbox.py:129-136`.
- Unsupported effect fail-closed path: `session_outbox.py:138-147`.

## Test Coverage Pointers

- Wake creation outbox: `novaic-agent-runtime/tests/test_pr251_wake_creation_outbox_cutover.py`.
- Attach outbox: `novaic-agent-runtime/tests/test_pr248_attach_outbox_cutover.py`.
- Recovery archive outbox: `novaic-agent-runtime/tests/test_pr247_recovery_outbox_cutover.py`.
- Effect builder/dispatcher boundary: `novaic-agent-runtime/tests/test_pr267_session_outbox_effect_boundary.py`.

## Changes

No source changes were made. This ticket only classified dispatcher-internal direct calls.

## Residual Risk

P462 still needs to classify/remove the stale `OBSERVE_CREATE_WAKE_SAGA` residue. P463 still needs final broad side-effect bypass guards.
