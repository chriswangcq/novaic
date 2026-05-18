# Remove repository eager attach publish

## Problem

`SessionRepository._publish_attach_request_after_transaction(...)` records a durable attach outbox row and then eagerly calls `SessionOutboxDispatcher.publish_attach_input_effect(...)`. This leaves delivery owned by both the repository path and session-outbox-worker.

## Success Criteria

- SessionRepository no longer calls `publish_attach_input_effect` or otherwise publishes attach tasks directly.
- Dispatch attach result returns `delivery=outbox_pending`, `outbox_id`, and no synchronous `task_id` requirement.
- SessionOutboxDispatcher no longer exposes attach-only eager publish API unless another production caller needs it.
- Tests are updated so attach delivery is performed by draining session outbox explicitly.
