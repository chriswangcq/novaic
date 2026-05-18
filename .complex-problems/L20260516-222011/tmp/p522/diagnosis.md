# P522 Attach Outbox Status Diagnosis

## Finding

`SessionRepository.dispatch` records attach delivery as `outbox_pending`; publication is owned by `SessionOutboxDispatcher.drain_pending` or a worker.

## Source Evidence

- `queue_service/session_repo.py` returns `delivery: outbox_pending` and `outbox_id` for attach.
- `queue_service/session_outbox.py` owns `_publish_attach_input` and marks outbox rows published after drain.
- The failing test drained only `CREATE_WAKE_SAGA` before attach, then expected the later attach effect to already be published.

## Decision

Update the test to explicitly drain the attach outbox boundary after dispatching the attach message before asserting `published` and checking the emitted task.
