# T451 Result: Session outbox effect inventory

## Summary

Mapped the current session outbox side-effect model. `tq_session_outbox` is the durable row store, `SessionOutboxDispatcher` owns supported effect delivery, and the active effect set is `create_wake_saga`, `recovery_archive_scope`, and `publish_attach_input`. Raw guard output is saved for downstream bypass classification.

## Artifacts

- Guard output: `.complex-problems/L20260516-222011/tmp/p458/session-outbox-inventory-guards.txt` (`2061` lines).

## Durable Store

- `novaic-agent-runtime/queue_service/db/schema.py:384` documents `tq_session_outbox` as the durable side-effect ledger.
- `novaic-agent-runtime/queue_service/db/schema.py:386` defines `tq_session_outbox`.
- Identity and dispatch fields:
  - `session_key`, `agent_id`, `subagent_id`, `user_id`: `schema.py:388-391`.
  - `generation`: `schema.py:392`.
  - `effect_type`, `payload`, `idempotency_key`, `status`, attempts/errors, timestamps: `schema.py:393-402`.
  - pending/session/idempotency indexes: `schema.py:405-410`.

## Effect Types

| Effect | Owner/Builder | Delivery Handler | Boundary |
| --- | --- | --- | --- |
| `create_wake_saga` | `session_wake_plan.py:76-89` and `session_wake_plan.py:113-126` build durable effects through `build_create_wake_saga_effect`. | `session_outbox.py:140-141` dispatches to `_publish_create_wake_saga`; `session_outbox.py:149+` validates payload and calls saga creation. | Creates a wake saga, then applies wake-created observation through `SessionObservedEventHandler`. |
| `recovery_archive_scope` | `session_repo.py:451-458` appends a recovery archive effect when a recovery marker is present. | `session_outbox.py:142-144` dispatches to `_publish_recovery_archive`; `session_outbox.py:190+` publishes `TaskTopics.CORTEX_SCOPE_END`. | Archives recovered/old scope with explicit `session_generation`, reason, and remaining stack. |
| `publish_attach_input` | `session_repo.py:929-943` builds attach input effects through `build_attach_input_effect`. | `session_outbox.py:145-146` dispatches to `_publish_attach_input`; `session_outbox.py:224+` publishes `TaskTopics.SESSION_ATTACH_INPUT`. | Attaches new input to active wake with `expected_session_generation`. |

## Dispatcher / Worker Flow

- `SessionOutboxDispatcher` states that the outbox row is durable authority and publish is idempotent through row idempotency key: `session_outbox.py:21-27`.
- Supported effect list is explicit: `session_outbox.py:29-37`.
- `drain_pending(...)` lists pending rows via ledger and marks publish/failure/dead-letter: `session_outbox.py:59-90`.
- `publish_effect(...)` can publish a single row but still reads the durable row first and acks through the ledger: `session_outbox.py:92-118`.
- `_publish_and_ack(...)` publishes then marks row published: `session_outbox.py:120-127`.
- `SessionOutboxHandler` exposes the generic worker job `session_outbox_drain` and delegates to dispatcher: `session_outbox_worker.py:13-58`.

## Observed Wake-Created Boundary

- `SessionObservedEventHandler.apply_wake_created(...)` applies the saga creation result back into session state.
- It validates `session_key`, `agent_id`, `subagent_id`, positive `generation`, and starting state before recording active session.
- It cancels race-loser/stale sagas instead of silently activating them.
- This is an observed-result handler below `create_wake_saga` delivery, not a separate supported outbox effect in the current active list.

## Initial Flags for P459

- `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA` constant still exists but is not included in `SUPPORTED_EFFECT_TYPES`; tests mention it as removed/unsupported behavior. P459 should classify whether this constant is harmless test guard residue or removable source residue.
- `_publish_create_wake_saga` contains a direct `saga_orchestrator.create(...)` call inside the outbox dispatcher. P459 should classify it as a safe implementation detail below the durable row or a bypass risk.
- `_publish_recovery_archive` and `_publish_attach_input` contain direct `queue.publish(...)` calls inside the outbox dispatcher. P459 should classify them as safe implementation details below the durable row or bypass risks.

## Changes

No source changes were made. This was a read-only inventory.
