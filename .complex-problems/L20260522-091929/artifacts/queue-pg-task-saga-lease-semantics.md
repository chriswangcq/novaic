# Queue Postgres Task/Saga/Lease Concurrency Map

## Scope

Artifact for P015 / T011. This maps the current Queue Service task, saga, and worker lease concurrency behavior from SQLite to Postgres implementation rules.

This artifact is design-only. It does not change runtime code or production data.

## Source Evidence

- Task lifecycle code: `novaic-agent-runtime/queue_service/queue_db.py`
  - `publish`: lines 115-199
  - `claim`: lines 201-300
  - `complete`: lines 302-358
  - `fail`: lines 360-483
  - `heartbeat`: lines 485-530
  - `recover_stale`: lines 532-633
  - `release_task`: lines 635-686
  - `cancel_all`: lines 750-839
  - task projection/state/event writers: lines 1118-1344
- Saga lifecycle code: `novaic-agent-runtime/queue_service/saga_repo.py`
  - `create`: lines 101-156
  - `claim`: lines 158-237
  - `heartbeat`: lines 239-284
  - `recover_stale`: lines 286-354
  - `mark_launched`: lines 388-450
  - `append_step_result`: lines 452-510
  - `check_saga_complete`: lines 512-573
  - `mark_completed`: lines 575-607
  - `mark_failed`: lines 608-670
  - `cancel_all`: lines 686-772
  - `cancel_pending`: lines 774-813
  - saga projection/state/event writers: lines 843-1026
- Worker lease code:
  - `lease_ledger.py`: table mapping and upsert paths, lines 16-172
  - `lease_fsm.py`: acquire/heartbeat/release/timeout transitions, lines 18-216
  - task lease writer: `queue_db.py` lines 1346-1418
  - saga lease writer: `saga_repo.py` lines 1028-1113
- Generic FSM runner:
  - `fsm/runner.py` writes event first, then state, then outbox, and suppresses duplicate idempotency-key events without replaying state/outbox, lines 56-99.
- SQLite transaction wrapper:
  - `novaic-common/common/db/database.py` uses process-local FIFO/sharded locks around one SQLite connection transaction, lines 184-227.

## Design Principles

- Use Postgres `READ COMMITTED` by default.
- Make `tq_*_state` rows the lock targets because they are the lifecycle authority.
- Keep `tq_tasks` and `tq_sagas` as content/context projections, not lifecycle authority.
- Keep event insert, state upsert/update, projection update, and lease event/state write in one database transaction per lifecycle transition.
- Use `FOR UPDATE SKIP LOCKED` for queue-style candidate selection.
- Use `SELECT ... FOR UPDATE` for single machine operations by ID.
- Use unique constraints for idempotency and worker lease identity. Do not rely on Python locks for correctness.
- Treat the current Python FIFO/sharded locks as SQLite-era fairness/performance helpers only. After PG cutover, correctness must come from row locks, uniqueness, and transaction predicates.

## Required Constraints and Indexes

The PG schema for this slice must preserve:

- `tq_task_state(task_id primary key)`.
- `tq_saga_state(saga_id primary key)`.
- `tq_worker_lease_state(lease_id primary key)`.
- Unique `tq_worker_lease_state(machine_type, machine_id)`.
- Unique event idempotency indexes for task, saga, and worker lease events.
- Task candidate index: `(topic, state)` plus retry/created ordering support, likely on `tq_task_state(topic, state, next_retry_at, updated_at)` and `tq_tasks(created_at)`.
- Saga candidate index: `tq_saga_state(saga_type, state)` plus `tq_sagas(created_at)`.
- Recovery indexes: `tq_worker_lease_state(machine_type, state, heartbeat_at)` and joins on `machine_id`.

## Generic FSM Write Rule

For task and saga ledger adapters, preserve the current runner order:

1. Insert event row with deterministic `id` and `idempotency_key`.
2. If event idempotency already exists, return the existing event id and do not update state/outbox again.
3. Upsert/update the materialized state row.
4. Append outbox rows, if the decision emits effects.

Postgres rule:

```sql
-- Inside the caller's transaction.
INSERT INTO <events_table> (...)
VALUES (...)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id;
```

- If an event row is returned, continue with state/outbox writes.
- If no row is returned, select the existing event id and treat the transition as already recorded.
- Do not advance generation twice on duplicate event idempotency keys.

## Task Lifecycle Mapping

### `publish`

Current behavior:

- Inserts `tq_tasks` content projection.
- Records `TASK_PUBLISHED` into `tq_task_events` and `tq_task_state`.
- If `tq_tasks.idempotency_key` conflicts, returns the existing task id.

Postgres transaction:

1. Generate `task_id` and `now` outside SQL, as today.
2. `INSERT INTO tq_tasks (...) VALUES (...) ON CONFLICT (idempotency_key) DO NOTHING RETURNING id`.
3. If conflict and idempotency key was supplied, `SELECT id FROM tq_tasks WHERE idempotency_key = $key` and return it. Do not create a second event/state row.
4. For a new row, insert task event and state in the same transaction.

Implementation note: if `idempotency_key` is nullable, PG allows many nulls. That matches SQLite behavior.

### `claim`

Current behavior:

- Global SQLite transaction with short busy timeout.
- Selects one pending task from `tq_task_state`, joining `tq_tasks` and optional `tq_saga_state` for dependency readiness.
- Applies task claim projection and writes task event plus lease acquired event/state in the same transaction.

Postgres transaction:

```sql
WITH candidate AS (
  SELECT ts.task_id
  FROM tq_task_state ts
  JOIN tq_tasks t ON t.id = ts.task_id
  LEFT JOIN tq_saga_state ss ON ss.saga_id = ts.saga_id
  WHERE ts.state = 'pending'
    AND (ts.next_retry_at IS NULL OR ts.next_retry_at <= $now)
    AND ts.topic = ANY($topics)
    AND <dependency_ready_predicate>
  ORDER BY t.created_at
  FOR UPDATE OF ts SKIP LOCKED
  LIMIT 1
)
SELECT <read model columns>
FROM candidate c
JOIN tq_task_state ts ON ts.task_id = c.task_id
JOIN tq_tasks t ON t.id = c.task_id
LEFT JOIN tq_saga_state ss ON ss.saga_id = ts.saga_id;
```

Then, still inside the transaction:

1. Decide task transition from the locked `tq_task_state` row.
2. Decide lease transition using `tq_worker_lease_state` for `lease_id='queue_task:' || task_id`.
3. Lock the lease row if it exists: `SELECT ... FOR UPDATE`.
4. If no lease row exists, insert it as part of lease state write. If the insert races, the unique key fails; retry the whole claim transaction or return no candidate.
5. Insert task event, update task state, insert lease event, upsert lease state.
6. Return the claimed read model.

`FOR UPDATE SKIP LOCKED` is required. A plain `SELECT` followed by update is not safe under multi-process PG workers.

### `complete`

Current behavior:

- Locks by task id in Python, reads task/state, requires state `claimed`.
- Decides task completed, updates `tq_tasks.result`, records task transition, releases lease.

Postgres transaction:

1. `SELECT ts.*, t.* FROM tq_task_state ts JOIN tq_tasks t ON ... WHERE ts.task_id=$1 FOR UPDATE OF ts`.
2. `SELECT * FROM tq_worker_lease_state WHERE lease_id=$lease_id FOR UPDATE`.
3. Revalidate `ts.state='claimed'` and lease state `acquired`.
4. Update `tq_tasks.result`.
5. Insert task completed event, update task state to `done`, insert lease released event, update lease state to `released`.
6. Return false if any revalidation fails.

Completion must win over stale recovery by holding the task state and lease state rows. If completion commits first, recovery no longer matches `state='claimed' AND lease='acquired'`.

### `fail` and `release_task`

Postgres transaction is the same lock shape as `complete`:

- Lock `tq_task_state` first.
- Lock `tq_worker_lease_state` second.
- Revalidate current state is `claimed`.
- Compute retry/final projection.
- Write task event/state and lease released event/state atomically.

For retrying failure, state returns to `pending` and lease becomes `released`. For terminal failure, task state becomes `failed` and lease becomes `released`.

### `heartbeat`

Postgres transaction:

1. Lock task state row.
2. Lock lease state row.
3. Revalidate task state is `claimed` and lease state is `acquired`.
4. Insert task heartbeat event, update task heartbeat projection, insert lease heartbeat event, update lease heartbeat.

Heartbeat must not update a lease after stale recovery has changed it to `expired`.

### `recover_stale`

Current behavior:

- Global SQLite transaction with short busy timeout.
- Selects claimed tasks whose lease heartbeat is older than the cutoff.
- For each row, applies timeout/retry or timeout/terminal task transition and lease timeout transition.

Postgres transaction:

```sql
WITH candidates AS (
  SELECT ts.task_id
  FROM tq_task_state ts
  JOIN tq_worker_lease_state ls
    ON ls.machine_type = 'queue_task'
   AND ls.machine_id = ts.task_id
  WHERE ts.state = 'claimed'
    AND ls.state = 'acquired'
    AND ls.heartbeat_at IS NOT NULL
    AND ls.heartbeat_at < $stale_cutoff
  ORDER BY ls.heartbeat_at
  FOR UPDATE OF ts, ls SKIP LOCKED
  LIMIT $max_recoveries
)
SELECT ...
```

For each locked candidate in the same transaction:

- Recompute retry/terminal decision from the locked task state.
- Insert task timeout event and update task state.
- Insert lease timed-out event and update lease state to `expired`.

This can be one transaction for the batch, matching current SQLite behavior. If batch lock time becomes too long, implementation may use smaller batches, but each candidate transition must remain atomic.

### `cancel_all`

Current behavior:

- Selects all pending/claimed tasks, optionally filtered by `json_extract(payload, '$.agent_id')`.
- For claimed tasks, releases lease.
- Records cancel event/state for each row.

Postgres transaction:

- Select candidate task state rows with `FOR UPDATE SKIP LOCKED`, in chunks.
- For claimed rows, also lock the corresponding lease rows.
- Revalidate state is still `pending` or `claimed`.
- Record task cancel transition.
- Release lease only for rows that were claimed at the moment they were locked.

`cancel_all` should be chunked to avoid holding locks for the entire queue.

## Saga Lifecycle Mapping

### `create`

Current behavior:

- Checks existing idempotency key before insert.
- Inserts `tq_sagas` and records saga created event/state in one transaction.

Postgres transaction:

1. `INSERT INTO tq_sagas (...) ON CONFLICT (idempotency_key) DO NOTHING RETURNING id`.
2. If conflict, select and return existing saga id.
3. For new row, insert saga created event and state.

### `claim`

Current behavior:

- Global SQLite transaction with short busy timeout.
- Selects one pending saga by type and created order.
- Applies running projection and records saga event plus lease acquired event/state.

Postgres transaction:

```sql
WITH candidate AS (
  SELECT ss.saga_id
  FROM tq_saga_state ss
  JOIN tq_sagas s ON s.id = ss.saga_id
  WHERE ss.state = 'pending'
    AND ss.saga_type = ANY($saga_types)
  ORDER BY s.created_at
  FOR UPDATE OF ss SKIP LOCKED
  LIMIT 1
)
SELECT ...
```

Then lock/upsert the corresponding `queue_saga:<saga_id>` lease row, record saga claim event/state, and record lease acquired event/state in the same transaction.

### `heartbeat`, `mark_launched`, `mark_failed` while running

Postgres transaction:

- Lock `tq_saga_state` by saga id.
- Lock matching `tq_worker_lease_state` when the transition requires heartbeat/release.
- Revalidate saga state is `running` for heartbeat/launched and lease state is `acquired`.
- Insert saga event/update saga state and insert lease event/update lease state atomically.

`mark_launched` releases the saga worker lease after DAG construction, matching current behavior.

### `recover_stale`

Current behavior:

- Selects running sagas whose `queue_saga` lease is acquired and stale.
- Transitions saga back toward pending/retry and marks lease timed out.

Postgres transaction:

```sql
WITH candidates AS (
  SELECT ss.saga_id
  FROM tq_saga_state ss
  JOIN tq_worker_lease_state ls
    ON ls.machine_type = 'queue_saga'
   AND ls.machine_id = ss.saga_id
  WHERE ss.state = 'running'
    AND ls.state = 'acquired'
    AND (ls.heartbeat_at IS NULL OR ls.heartbeat_at < $stale_cutoff)
  ORDER BY ls.heartbeat_at NULLS FIRST
  FOR UPDATE OF ss, ls SKIP LOCKED
  LIMIT $max_recoveries
)
SELECT ...
```

Then record saga timeout/retry event/state and lease timeout event/state atomically.

### `append_step_result` and `check_saga_complete`

Postgres transaction:

- Lock the saga state row with `FOR UPDATE`.
- For `append_step_result`, update `step_results` from the locked state and record one saga event/state transition.
- For `check_saga_complete`, lock saga state, count done tasks from `tq_task_state`, and if `done_count >= dag_task_count`, record completed transition.

Concurrent task completions can call these in separate transactions. The saga state row lock must serialize modifications to `step_results` and final completion.

### `mark_completed`, `mark_failed`, `cancel_pending`, `cancel_all`

Postgres transaction:

- Lock saga state rows first.
- Lock lease rows only for running sagas that need lease release.
- Revalidate current state before transition.
- Record saga event/state; release lease where applicable.

`cancel_all` should use chunked `FOR UPDATE SKIP LOCKED` row selection, just like task cancellation.

## Worker Lease Mapping

Current lease FSM:

- `none/released/expired -> acquired`
- `acquired -> acquired` for heartbeat
- `acquired -> released`
- `acquired -> expired`
- All other transitions are rejected.

Postgres rule:

- Use `lease_id = machine_type || ':' || machine_id` as primary identity.
- Preserve unique `(machine_type, machine_id)` to prevent duplicate logical leases.
- Whenever a task/saga transition touches a lease, lock the machine state row first and then the lease row, in that order.
- If the lease row does not exist, insert it inside the same transaction. If insert conflicts, retry the transaction or return no candidate, depending on call path.
- Do not allow heartbeat/release/timeout to proceed unless the locked lease row is still `acquired`.

For claim paths, the authoritative task/saga state row lock is the main duplicate-execution guard. The lease unique constraint is a second guard and a diagnostic invariant.

## Lock Ordering

To avoid deadlocks:

- Task paths: lock `tq_task_state` before `tq_worker_lease_state`.
- Saga paths: lock `tq_saga_state` before `tq_worker_lease_state`.
- Saga completion checks that count task states should lock saga state first, then read task state counts without locking every task row unless implementation later proves it necessary.
- Cross-row batch operations should lock rows in deterministic order and use small batches.
- Do not take advisory locks in the normal task/saga claim path unless a later implementation ticket proves row locks are insufficient.

## Race-Case Outcomes

Two workers claim the same task:

- Both run candidate selection with `FOR UPDATE SKIP LOCKED`.
- One locks the pending `tq_task_state` row and claims it.
- The other skips it and either claims another row or returns none.

Task completion races stale recovery:

- Completion locks task state plus lease first: it sets task `done` and lease `released`; recovery no longer matches.
- Recovery locks first: it sets task `pending` or `failed` and lease `expired`; completion revalidates and returns false because the task is no longer claimed/acquired.

Heartbeat races stale recovery:

- Heartbeat locks first: updates lease heartbeat; recovery re-evaluates after lock and should no longer match the stale cutoff.
- Recovery locks first: expires lease and moves task/saga state; heartbeat revalidates and returns false.

Cancel races claim:

- Claim locks pending row first: cancel skips locked row or sees it claimed after commit and cancels/release in a later chunk.
- Cancel locks pending row first: it records cancel; claim no longer sees pending.

Lease uniqueness conflict:

- If a transition attempts to insert a lease row that another transaction inserted first, the unique constraint fires. The implementation should retry the whole transaction for claim/recovery paths or return false for single-ID operations after re-reading locked state.

Saga step-result races completion:

- `append_step_result` and `check_saga_complete` both lock the saga state row. Step results and final completion are serialized, avoiding lost JSON updates.

## Python Lock Classification

- `global` SQLite lock: replace with row-level candidate locks and transaction predicates. It is not a PG correctness primitive.
- `task` SQLite lock: replace with `SELECT ... FOR UPDATE` on `tq_task_state`.
- `saga` SQLite lock: replace with `SELECT ... FOR UPDATE` on `tq_saga_state`.
- Sharded/FIFO behavior may be kept as optional local fairness/backpressure, but tests must not rely on it for correctness.
- SQLite `sqlite_busy_timeout_ms=250` in claim/recovery becomes a PG retry/defer policy owned by P017; it must not remain as string matching on SQLite errors.

## Implementation Blockers

- A Postgres DB adapter must expose explicit transaction scopes and row-locking queries; the current `common.db.Database` is SQLite-specific.
- JSON dependency and agent filtering predicates are required for task claim/cancel and saga cancel; P017 must translate them to JSONB before implementation.
- Timestamp type choice is required for heartbeat/retry comparisons; P017 must decide `timestamptz` versus text-compatible storage before implementation.
- Route-level busy/defer behavior must be rewritten for PG exceptions before the queue service can run Postgres-only.

## P014 Inputs

P014 cutover design should consume these concrete requirements:

- Stop or drain queue workers before copying live rows, unless dual-write is introduced.
- Migrate state, events, outbox, lease, task, and saga projection rows together.
- Restart only PG-backed queue service and workers; do not leave mixed SQLite and PG writers.
- Run smoke tests that exercise claim, complete, stale recovery, saga claim/launch, and lease event/state verification.

