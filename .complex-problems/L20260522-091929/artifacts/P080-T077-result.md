# Task Queue And Idempotency Paths Ported

## Summary

Completed the P080 task queue and idempotency repository slice through three child problems:

- P084 / R074: task claim/recovery/cancel query dialect.
- P085 / R075: task publish/mutation locking and JSONB binding.
- P086 / R079: task idempotency acquisition, completion/release, and diagnostics.

Together these changes move the task queue paths away from SQLite-only `datetime(...)`, `json_each`, `json_extract`, tuple-only row assumptions, and unsafe idempotency upserts on the Postgres path.

## Done

- Task claim candidates use Postgres-native timestamp comparison, JSONB dependency readiness, stable ordering, and `FOR UPDATE OF ts SKIP LOCKED`.
- Stale recovery uses Postgres-native heartbeat comparison and `FOR UPDATE OF ts, ls SKIP LOCKED`.
- Cancel-by-agent uses `payload ->> 'agent_id'` and locks task-state candidates in Postgres.
- Task publish/result/dependency values bind as native JSONB-compatible values in Postgres mode.
- Single-task lifecycle mutations use `_get_task_for_update` with `FOR UPDATE OF ts` in Postgres.
- Idempotency acquisition uses row locking, native timestamptz lease activity, completed-result reuse, contention updates, expired reacquire, and same-owner renewal behavior.
- Idempotency completion binds JSONB-compatible results and no longer overwrites conflicting rows after a guarded update miss.
- Idempotency release keeps owner/task scoped deletes.
- Idempotency diagnostics support tuple and dict-like rows with the same public field shape.

## Verification

- P084 selected verification: 61 Queue tests passed.
- P085 focused/selected verification: 24 task-focused tests passed; 72 selected Queue/FSM tests passed.
- P086 combined idempotency verification: 66 selected Queue/idempotency tests passed.
- Compileall and `git diff --check` succeeded for the touched Queue files during child verification.

## Known Gaps

- Real Postgres runtime and concurrency validation remains a later Queue staging validation problem.
- Saga repository, session/outbox, and Postgres transient error guard slices remain separate P074 children.

## Child Results

- R074
- R075
- R079
