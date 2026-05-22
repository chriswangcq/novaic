# Port Task Mutations And State Locking To Postgres

## Problem

Task publish, complete, fail, heartbeat, release, and cancel paths currently rely on process-local transaction locks and SQLite update behavior. The Postgres path needs explicit task-state row locking or compare-and-update semantics so single-task lifecycle mutations do not race with claim/recovery or duplicate workers. This belongs under P080 because these operations own the task lifecycle correctness after a candidate has been selected.

## Success Criteria

- Postgres task publish writes content/state/event/outbox rows with JSONB-compatible values and preserves idempotency-key behavior.
- Postgres task complete/fail/heartbeat/release/cancel lock or compare/update the relevant `tq_task_state` rows before applying lifecycle decisions.
- Task `_get_task_for_update` or its Postgres equivalent uses `FOR UPDATE` or a reviewed compare-and-update pattern.
- Postgres task mutation paths do not depend on `sqlite_busy_timeout_ms` or local process locks for correctness.
- Focused tests cover mutation loser/no-op behavior, completion versus recovery race shape, JSONB result binding, and existing sqlite mutation fixture compatibility.
