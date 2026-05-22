# Queue Postgres JSONB/Time/Index/SQLite Assumption Map

## Scope

Artifact for P017 / T013. This maps Queue SQLite-specific JSON, timestamp, index, busy/lock, and PRAGMA assumptions to explicit Postgres implementation choices.

This artifact is design-only. It does not change runtime code or production data.

## Source Evidence

- JSON correctness use:
  - Task dependency readiness: `queue_db.py` lines 220-245 uses `json_each(t.depends_on)` and `json_extract(ss.step_results, '$.' || j.value)`.
  - Task cancel by agent: `queue_db.py` lines 762-773 uses `json_extract(t.payload, '$.agent_id')`.
  - Saga cancel by agent: `saga_repo.py` lines 698-706 uses `json_extract(ss.context, '$.agent_id')`.
- Timestamp correctness use:
  - Task retry eligibility: `queue_db.py` line 228 uses `datetime(ts.next_retry_at) <= datetime(?)`.
  - Task stale recovery: `queue_db.py` lines 541-556 uses `datetime(ls.heartbeat_at) < datetime(?)`.
  - Saga stale recovery: `saga_repo.py` lines 295-307 uses `datetime(ls.heartbeat_at) < datetime(?)`.
  - Idempotency lease comparison: `queue_db.py` lines 917-924 parses ISO timestamps in Python.
  - Outbox and event ordering use `created_at` throughout `fsm/sqlite_store.py`.
- Index/schema evidence:
  - Task/task-state indexes: `schema.py` lines 59-121.
  - Saga/session/lease/outbox/idempotency indexes: `schema.py` lines 223-333 and 342-411.
- SQLite-specific behavior:
  - `routes.py` imports `sqlite3`, string-matches busy/locked errors, and defers claim/recovery, lines 9 and 27-58.
  - `fsm/sqlite_store.py` retries `sqlite3.OperationalError` busy strings, lines 491-548.
  - `common/db/database.py` configures SQLite WAL/synchronous/busy_timeout and process-local transaction locks.

## JSONB Decisions

Use `jsonb` for all durable JSON payload columns in the PG queue schema:

- `tq_tasks.payload`
- `tq_tasks.result`
- `tq_tasks.depends_on`
- `tq_task_events.payload`
- `tq_task_outbox.payload`
- `tq_sagas.context`
- `tq_saga_events.payload`
- `tq_saga_state.context`
- `tq_saga_state.step_results`
- `tq_saga_outbox.payload`
- `tq_worker_lease_events.payload`
- `tq_worker_lease_outbox.payload`
- `tq_idempotency_ledger.result`
- `tq_session_events.payload`
- `tq_session_outbox.payload`

Use Python adapters to pass dictionaries/lists as JSONB values instead of pre-serializing them to strings in the PG path. The API read model can still return decoded dictionaries/lists as today.

## JSONB Predicate Mapping

Task dependency readiness:

SQLite:

```sql
NOT EXISTS (
  SELECT 1 FROM json_each(t.depends_on) j
  WHERE json_extract(ss.step_results, '$.' || j.value) IS NULL
)
```

Postgres:

```sql
(
  t.depends_on IS NULL
  OR t.depends_on = '[]'::jsonb
  OR t.depends_on = 'null'::jsonb
  OR (
    ts.saga_id IS NOT NULL
    AND ss.saga_id IS NOT NULL
    AND NOT EXISTS (
      SELECT 1
      FROM jsonb_array_elements_text(t.depends_on) AS dep(step_name)
      WHERE NOT (COALESCE(ss.step_results, '{}'::jsonb) ? dep.step_name)
    )
  )
)
```

Task cancel by agent:

```sql
t.payload ->> 'agent_id' = $agent_id
```

Saga cancel by agent:

```sql
ss.context ->> 'agent_id' = $agent_id
```

State/context reads:

- Use `->>` for scalar strings such as `agent_id`, `subagent_id`, `scope_id`, and `session_generation` when filtering or deriving runtime state in SQL.
- Use Python-side JSON decoding only at the repository boundary for read models.

## JSONB Index Strategy

Required expression indexes:

```sql
CREATE INDEX idx_tq_tasks_payload_agent
  ON tq_tasks ((payload ->> 'agent_id'))
  WHERE payload ? 'agent_id';

CREATE INDEX idx_tq_saga_state_context_agent
  ON tq_saga_state ((context ->> 'agent_id'))
  WHERE context ? 'agent_id';
```

Optional GIN indexes:

- `tq_saga_state.step_results` can use `GIN (step_results)` if dependency readiness becomes hot across many saga rows. Current claim joins by `saga_id`, so this is not required for first cutover.
- `tq_tasks.payload` and `tq_saga_state.context` can use GIN later if diagnostics add broad JSON searches.

No JSONB index is required for `tq_tasks.depends_on` in the first cutover because it is evaluated only on candidate pending rows after topic/state filtering.

## Timestamp Decision

Use `timestamptz` for all queue time fields in Postgres:

- `created_at`
- `updated_at`
- `claimed_at`
- `heartbeat_at`
- `next_retry_at`
- `started_at`
- `finished_at`
- `completed_at`
- `consumed_at`
- `published_at`
- `acked_at`
- `last_contended_at`
- `lease_until`

Reasons:

- Retry, heartbeat, stale recovery, and idempotency lease comparisons are correctness paths, not display-only values.
- SQLite's text ISO timestamps currently work because comparisons are wrapped with `datetime(...)` or parsed in Python. Postgres should use native time comparison.
- Queue code already treats times as UTC ISO strings. PG adapter should normalize inbound values to UTC `timestamptz` and render outbound API values as ISO strings with `Z` for compatibility.

Migration rule:

- Parse existing SQLite text with `datetime.fromisoformat(value.replace("Z", "+00:00"))`.
- Store as `timestamptz`.
- Preserve nulls.
- For ordering ties, always use `(created_at, id)` or `(updated_at, id)` instead of relying on SQLite `rowid`.

## Timestamp Predicate Mapping

Task retry eligibility:

```sql
ts.next_retry_at IS NULL OR ts.next_retry_at <= $now
```

Task stale recovery:

```sql
ls.heartbeat_at IS NOT NULL AND ls.heartbeat_at < $stale_cutoff
```

Saga stale recovery:

```sql
ls.heartbeat_at IS NULL OR ls.heartbeat_at < $stale_cutoff
```

Idempotency lease active:

```sql
lease_until IS NOT NULL AND lease_until > $now
```

Outbox ordering:

```sql
ORDER BY created_at, id
```

## Required Postgres Constraints and Indexes

Preserve primary keys and unique constraints:

- Primary key on every `id`, `task_id`, `saga_id`, `session_key`, `lease_id`, and `idempotency_key` authority column as in SQLite.
- Unique idempotency keys on:
  - `tq_tasks(idempotency_key)`
  - `tq_task_events(idempotency_key)`
  - `tq_task_outbox(idempotency_key)`
  - `tq_sagas(idempotency_key)`
  - `tq_saga_events(idempotency_key)`
  - `tq_saga_outbox(idempotency_key)`
  - `tq_worker_lease_events(idempotency_key)`
  - `tq_worker_lease_outbox(idempotency_key)`
  - `tq_session_events(idempotency_key)`
  - `tq_session_outbox(idempotency_key)`
- Unique `tq_worker_lease_state(machine_type, machine_id)`.

Candidate and recovery indexes:

```sql
CREATE INDEX idx_tq_task_state_claim
  ON tq_task_state (topic, state, next_retry_at, updated_at);

CREATE INDEX idx_tq_task_state_saga
  ON tq_task_state (saga_id)
  WHERE saga_id IS NOT NULL;

CREATE INDEX idx_tq_saga_state_claim
  ON tq_saga_state (saga_type, state, updated_at);

CREATE INDEX idx_tq_worker_lease_state_heartbeat
  ON tq_worker_lease_state (machine_type, state, heartbeat_at);
```

Event read indexes:

```sql
CREATE INDEX idx_tq_task_events_task
  ON tq_task_events (task_id, generation, created_at, id);

CREATE INDEX idx_tq_saga_events_saga
  ON tq_saga_events (saga_id, generation, created_at, id);

CREATE INDEX idx_tq_worker_lease_events_lease
  ON tq_worker_lease_events (lease_id, generation, created_at, id);

CREATE INDEX idx_tq_session_events_session
  ON tq_session_events (session_key, generation, created_at, id);
```

Outbox indexes:

```sql
CREATE INDEX idx_tq_task_outbox_pending
  ON tq_task_outbox (status, created_at, id)
  WHERE status = 'pending';

CREATE INDEX idx_tq_saga_outbox_pending
  ON tq_saga_outbox (status, created_at, id)
  WHERE status = 'pending';

CREATE INDEX idx_tq_worker_lease_outbox_pending
  ON tq_worker_lease_outbox (status, created_at, id)
  WHERE status = 'pending';

CREATE INDEX idx_tq_session_outbox_pending
  ON tq_session_outbox (status, created_at, id)
  WHERE status = 'pending';
```

Idempotency lease index:

```sql
CREATE INDEX idx_tq_idempotency_lease
  ON tq_idempotency_ledger (status, lease_until)
  WHERE status = 'in_progress';
```

Foreign keys:

- Do not add foreign keys in the first PG cutover unless a later ticket explicitly tests them. SQLite currently sets queue schema foreign keys off for queue tables, so adding FK enforcement during migration is a behavior change.

## SQLite Busy/Error Mapping

Remove SQLite-specific imports and string matching from the PG runtime path.

Claim/recovery routes:

- With `FOR UPDATE SKIP LOCKED`, normal contention should return no candidate or zero recovered rows, not raise a busy error.
- Retry bounded transient PG errors:
  - `psycopg.errors.DeadlockDetected`
  - `psycopg.errors.SerializationFailure`
  - connection-level transient `OperationalError` only if the adapter classifies it as retryable.
- After retries, preserve user-facing defer behavior:
  - claim returns no task/saga
  - recovery returns zero recovered
  - log reason as `pg_transient_retry_exhausted` or `pg_lock_deferred`, not `sqlite_busy`.

Generic store:

- Remove `sqlite3.OperationalError` busy string matching.
- Use SQL `ON CONFLICT` instead of catching unique strings.
- Do not auto-commit standalone mutations in the PG store; require explicit transaction scopes for mutating queue writes.

## SQLite PRAGMA Mapping

Remove these from PG runtime:

- `PRAGMA journal_mode = WAL`
- `PRAGMA foreign_keys`
- `PRAGMA synchronous`
- `PRAGMA busy_timeout`
- `PRAGMA cache_size`
- `PRAGMA temp_store`

PG replacements:

- Connection pool settings and statement timeout belong in PG adapter/config.
- Lock wait behavior belongs to row-lock SQL (`SKIP LOCKED`) and bounded retry policy.
- FK behavior is a schema decision, not a per-connection PRAGMA.

## Python Lock Classification

- `global` SQLite lock: correctness residue for PG. Replace with row-level locks or session row ensure+lock. Do not rely on it.
- `task` SQLite lock: replace with `FOR UPDATE` on `tq_task_state`.
- `saga` SQLite lock: replace with `FOR UPDATE` on `tq_saga_state`.
- Session global lock: replace with ensure+lock on `tq_session_state(session_key)`.
- Sharded/FIFO locks may remain only as optional local backpressure/fairness. They must be outside correctness assumptions and not required for tests to pass.
- `TimeoutError` from local lock acquisition should disappear from normal PG claim/recovery paths. If the PG adapter adds its own timeout, expose a PG-specific exception and map it intentionally.

## Implementation Blockers

- A PG queue adapter must exist before runtime code can be switched; the current `common.db.Database` is SQLite-only.
- SQL-building helpers must separate SQLite and PG dialects; the generic FSM store currently emits SQLite-oriented SQL and catches SQLite exceptions.
- Outbox claim metadata from P016 must be reflected in schema/indexes before multi-worker PG outbox draining.
- All `rowid` order usage must become deterministic `(created_at, id)`.
- Tests must cover JSONB dependency readiness and agent filters before cutover.
- Route logs and exception handling must stop saying `sqlite_busy` in PG runtime.

## P014 Inputs

- Use `jsonb` and `timestamptz` in the PG schema.
- Include expression indexes for `payload->>'agent_id'` and `context->>'agent_id'`.
- Preserve partial pending outbox and in-progress idempotency indexes.
- Defer FK enforcement until after first successful cutover unless separately tested.
- Add PG exception/retry smoke tests for claim/recovery before deployment.

