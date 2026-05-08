# Result summary

## Summary

The user message was accepted by Entangled, but it was not handed off into the queue/session runtime. The immediate failure was Business subscriber dispatch timing out when calling Queue Service `/api/queue/dispatch`. The deeper runtime condition was Queue Service SQLite/global FIFO lock congestion plus broken saga claiming: saga workers repeatedly received 500 from `/api/queue/sagas/claim` with `sqlite3.OperationalError: database is locked`.

## Done

- Checked production process health on `root@api.gradievo.com`: gateway, business, device, queue-service, blob, cortex, task workers, saga workers, outbox workers, health, scheduler, and subscriber were running. This rules out a simple "service is completely down" cause.
- Queried `/opt/novaic/data/entangled.db`.
  - Latest user message `d0fd5569974f` (`hello`) exists in `environment_im_messages`.
  - Its matching `environment_notifications` row is `state=failed`, `dispatch_attempts=5`.
  - A previous user message `24d90512564a` also ended as `failed`, while an older 2026-05-06 message had processed.
- Queried `/opt/novaic/data/queue.db`.
  - No `tq_session_events` rows exist for `d0fd5569974f`.
  - Recent session events only reference the older `24d90512564a`.
  - `tq_session_state` is still `active`, generation `1`, pointing at stale saga `saga-459abe82fdbf` and scope `067fcefa-3a09-495b-b049-8e1e34b17ed9`.
  - `tq_session_outbox` has stale pending `create_wake_saga` effect `seff-6d770f4b4793`, generation `1`, attempts `0`.
  - `tq_sagas` contains `saga-459abe82fdbf` for message `24d90512564a`; `tq_saga_state` says it is still `pending`; `tq_saga_events` only has `saga_created`.
- Read subscriber logs around the exact latest message time.
  - At `2026-05-08 18:28:10`, subscriber claimed notification `d0fd5569974f` and loaded the IM message.
  - At `18:28:15`, `common.wake.assembler` logged `result=network target=http://127.0.0.1:19997 exc_type=ReadTimeout`.
  - `business.subscribers.dispatch_subscriber` then logged transient failure for the same notification, `attempts=1`, `retry_in=2000ms`, `error=timed out`.
  - Retried attempts at `18:28:45` and `18:29:16` also hit `ReadTimeout`; DB shows this reached 5 attempts and then failed.
- Read Queue Service logs around the same period and current period.
  - Queue Service showed repeated `[FIFO Lock] Long wait` entries with callers `runtime-task`, `runtime-saga`, and `business`.
  - Around the message failure window, `business` waited around 5.5-5.9 seconds for the FIFO DB lock, which aligns with the subscriber client's 5 second read timeout.
  - Saga workers repeatedly got `POST /api/queue/sagas/claim` -> `500 Internal Server Error`.
  - Queue Service tracebacks show `sqlite3.OperationalError: database is locked` inside `queue_service/fsm/sqlite_store.py` while recording FSM events.

## Verification

The evidence chain is consistent:

1. Message is present in Entangled: the user input was not lost at the API/business persistence boundary.
2. Notification is failed after 5 dispatch attempts: the subscriber did try to dispatch it and gave up.
3. Subscriber log says the exact failure was `httpx.ReadTimeout` while posting `/api/queue/dispatch`.
4. Queue DB has no session event for the new message: dispatch did not commit the user input into the queue/session ledger.
5. Queue Service logs at the same time show FIFO lock waits and DB lock pressure: queue-service was alive but starved/blocked internally.
6. Saga workers are separately failing on `/api/queue/sagas/claim` with SQLite database locks: even the existing stale wake saga cannot progress.

## Known gaps

- This diagnosis did not patch production. It identifies the failure precisely enough for a follow-up fix ticket.
- I did not manually replay the message because the user asked for cause analysis, not mutation/recovery.
- The exact code path likely combines short dispatch client timeout, global DB/FIFO locking, worker polling pressure, and saga FSM event-store writes. Fixing only one symptom, such as increasing timeout, would not be a complete cure.

## Artifacts

- Ledger: `.complex-problems/L20260508-183023`
- Ticket: `T000-diagnose-message-no-reply`
- Production DBs inspected: `/opt/novaic/data/entangled.db`, `/opt/novaic/data/queue.db`
- Production logs inspected: `/opt/novaic/data/logs/subscriber-20260508.log`, `/opt/novaic/data/logs/queue-service.log`, saga worker logs
