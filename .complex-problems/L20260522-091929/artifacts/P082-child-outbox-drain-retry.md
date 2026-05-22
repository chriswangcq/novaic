# Port Durable Outbox Drain And Retry Semantics To Postgres

## Problem

Task, saga, session, and lease outbox drains currently list pending rows and then publish external effects. That shape is acceptable under a single SQLite process but unsafe under Postgres if multiple drainers can select the same pending row. The Postgres runtime needs either database-level row claiming before publish or a deliberately enforced single-drainer constraint, plus retry/dead-letter transitions that remain correct after publish success/failure.

## Success Criteria

- Pending outbox selection for Postgres either claims rows with `FOR UPDATE SKIP LOCKED` and owner/timeout metadata, or has an explicit runtime guard that enforces one drainer per outbox effect/table.
- Outbox ordering remains deterministic under Postgres for all affected ledgers: task, saga, session, and worker lease.
- Publish success marks rows published/acked in a transaction that is idempotent for replay after a crash between external publish and ack.
- Publish failure increments attempts, returns rows to retryable pending state when attempts remain, and moves them to dead-letter at the configured threshold.
- Focused tests cover publish-before-ack retry, dead-letter transition, duplicate-drainer protection or claim SQL, and deterministic ordering.
- Outbox ledger APIs keep dialect-specific SQL behind the FSM store or explicit adapter helpers.
