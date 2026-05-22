# Queue SQLite Inventory

## Scope

Inventory for P012 / T009. This is read-only evidence for planning the Queue Service migration from `/opt/novaic/data/queue.db` to the shared Postgres service on `api.gradievo.com`.

No production database rows, schema, processes, or service configs were changed while collecting this inventory.

## Runtime File Evidence

- Host: `api.gradievo.com`
- SQLite path: `/opt/novaic/data/queue.db`
- File metadata at collection time: `size=378683392`, `mode=644`, `owner=root:root`, `mtime=2026-05-20 22:13:52.513230033 +0800`
- Health endpoint: `http://127.0.0.1:19997/health` returned `{"status":"healthy","service":"queue-service","version":"1.0.0","database":"/opt/novaic/data/queue.db"}`
- `lsof` showed the DB held by:
  - `main_novaic.py queue-service`
  - `main_novaic.py session-outbox-worker`
  - `main_novaic.py saga-outbox-worker`
- Process set using the queue data dir:
  - `queue-service --host 127.0.0.1 --port 19997 --data-dir /opt/novaic/data`
  - two `task-worker --pool control`
  - two `task-worker --pool execution`
  - two `saga-worker`
  - `session-outbox-worker`
  - `saga-outbox-worker`
  - `health`
  - `scheduler`

## Row Counts

Collected from the live SQLite file:

| Table | Rows | Role |
| --- | ---: | --- |
| `config` | 1 | Schema/config marker |
| `tq_tasks` | 2247 | Task content/result projection |
| `tq_task_events` | 6996 | Append-only task lifecycle events |
| `tq_task_state` | 2247 | Current task lifecycle authority |
| `tq_task_outbox` | 0 | Durable task side-effect outbox |
| `tq_sagas` | 315 | Saga context projection |
| `tq_saga_events` | 3226 | Append-only saga lifecycle events |
| `tq_saga_state` | 315 | Current saga lifecycle authority |
| `tq_saga_outbox` | 6 | Durable saga side-effect outbox |
| `tq_worker_lease_events` | 5379 | Append-only worker lease events |
| `tq_worker_lease_state` | 2539 | Current worker lease authority |
| `tq_worker_lease_outbox` | 0 | Durable worker lease side-effect outbox |
| `tq_idempotency_ledger` | 2215 | Cross-process idempotent execution guard |
| `tq_session_events` | 202 | Append-only session input/lifecycle events |
| `tq_session_state` | 2 | Current session coordinator authority |
| `tq_session_outbox` | 31 | Durable session side-effect outbox |

No SQLite triggers exist.

## Schema Groups

Schema version is `18`, stored through `queue_service/db/schema.py`.

Task tables:

- `tq_tasks(id, idempotency_key, topic, payload, result, saga_id, step_name, depends_on, created_at)`
- `tq_task_events(id, task_id, generation, event_type, payload, causation_id, correlation_id, idempotency_key, consumed_at, created_at)`
- `tq_task_state(task_id, state, generation, topic, saga_id, step_name, claimed_by, claimed_at, retry_count, max_retries, heartbeat_at, next_retry_at, error, started_at, finished_at, updated_at)`
- `tq_task_outbox(id, task_id, generation, effect_type, payload, idempotency_key, status, attempts, last_error, published_at, acked_at, created_at, updated_at)`

Saga tables:

- `tq_sagas(id, idempotency_key, saga_type, context, created_at)`
- `tq_saga_events(id, saga_id, generation, event_type, payload, causation_id, correlation_id, idempotency_key, consumed_at, created_at)`
- `tq_saga_state(saga_id, state, generation, saga_type, context, dag_task_count, step_results, claimed_by, claimed_at, heartbeat_at, error, completed_at, updated_at)`
- `tq_saga_outbox(id, saga_id, generation, effect_type, payload, idempotency_key, status, attempts, last_error, published_at, acked_at, created_at, updated_at)`

Worker lease tables:

- `tq_worker_lease_events(id, lease_id, machine_type, machine_id, generation, event_type, payload, causation_id, correlation_id, idempotency_key, consumed_at, created_at)`
- `tq_worker_lease_state(lease_id, state, generation, machine_type, machine_id, claimed_by, heartbeat_at, updated_at)`
- `tq_worker_lease_outbox(id, lease_id, machine_type, machine_id, generation, effect_type, payload, idempotency_key, status, attempts, last_error, published_at, acked_at, created_at, updated_at)`

Session coordinator tables:

- `tq_session_events(id, session_key, agent_id, subagent_id, user_id, generation, event_type, payload, causation_id, correlation_id, idempotency_key, consumed_at, created_at)`
- `tq_session_state(session_key, state, generation, agent_id, subagent_id, user_id, active_saga_id, active_scope_id, recovery_id, heartbeat_at, updated_at)`
- `tq_session_outbox(id, session_key, agent_id, subagent_id, user_id, generation, effect_type, payload, idempotency_key, status, attempts, last_error, published_at, acked_at, created_at, updated_at)`

Idempotency table:

- `tq_idempotency_ledger(idempotency_key, status, owner_token, task_id, result, contention_count, last_contended_at, lease_until, updated_at)`

Important index patterns to preserve in Postgres:

- Unique idempotency indexes on task/saga/session/lease event and outbox tables.
- Partial pending outbox indexes: `status = 'pending'`.
- Partial projection indexes on `tq_tasks.saga_id` and `tq_task_state.saga_id` where not null.
- Candidate indexes on `state, updated_at`, `topic, state`, `saga_type, state`, and lease `machine_type, state, heartbeat_at`.
- Unique lease state index on `(machine_type, machine_id)`.
- Idempotency lease partial index on `(status, lease_until)` where `status = 'in_progress'`.

## Code Owners and Write Surfaces

Queue runtime bootstrap:

- `novaic-agent-runtime/queue_service/main.py` hard-codes `DB_PATH = Path(NOVAIC_DATA_DIR) / "queue.db"`, creates `common.db.Database(DB_PATH)`, runs `init_schema`, and wires the same DB object into task, saga, session, and outbox services.
- `/health` and `/ready` expose SQLite path/status and table checks.

SQLite wrapper and locks:

- `novaic-common/common/db/database.py` is a synchronous SQLite wrapper with thread-local connections, WAL, scoped `PRAGMA busy_timeout`, and Python FIFO/sharded locks.
- Its transaction API currently provides `global`, `task`, `saga`, `agent`, and `message` lock types. This is process-local coordination and must not be assumed to protect cross-process Postgres writers.

Schema:

- `novaic-agent-runtime/queue_service/db/schema.py` owns fresh schema creation and rejects unsupported schema versions. Historical in-process migrations have already been removed.

Task queue:

- `novaic-agent-runtime/queue_service/queue_db.py` owns task publish, claim, complete, fail, heartbeat, recover, release, cancel, stats, topics, and idempotency ledger operations.
- Task claim and recovery currently rely on a single SQLite transaction around candidate selection, task state projection, task event append, and lease state/event writes.
- `json_each` and `json_extract` are used for dependency readiness and agent-specific cancellation.

Generic FSM store:

- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py` owns generic event append, state upsert, outbox append/list/mark, event consumption, and busy retry handling.
- It uses SQL identifier validation plus SQLite `ON CONFLICT(...) DO UPDATE`.

Ledger adapters:

- `task_ledger.py` maps the generic store to `tq_task_*`.
- `saga_ledger.py` maps the generic store to `tq_saga_*`.
- `lease_ledger.py` maps the generic store to `tq_worker_lease_*`.
- `session_ledger.py` maps the generic store to `tq_session_*`.

Saga orchestration:

- `novaic-agent-runtime/queue_service/saga_repo.py` owns saga create, claim, heartbeat, recover, get, launch, complete, fail, cancel, and saga-task completion logic.
- Saga claim/recovery also needs atomic state transition plus worker lease writes.
- Several reads join `tq_sagas`, `tq_saga_state`, `tq_task_state`, and `tq_worker_lease_state`.

Session coordination:

- `novaic-agent-runtime/queue_service/session_repo.py` owns dispatch/session-ended/rebuild behavior.
- It guarantees at-most-one active session per `agent_id:subagent_id`, no input loss, and atomic dispatch decisions over `tq_session_events`, `tq_session_state`, and `tq_session_outbox`.
- `session_outbox.py`, `session_outbox_worker.py`, `saga_outbox_worker.py`, and related outbox workers drain durable side effects.

HTTP route behavior:

- `novaic-agent-runtime/queue_service/routes.py` catches `sqlite3.OperationalError` busy/locked conditions in claim/recovery paths and defers rather than failing user-facing flows.
- This busy/locked behavior should be replaced with a Postgres-specific retry/defer policy rather than retained as SQLite strings.

## Postgres Migration Implications

- The queue DB is live and non-empty; it cannot be deleted like `device.db`.
- All task/saga/session/lease transitions need a single authoritative transaction boundary in Postgres.
- Candidate claim/recover flows should use Postgres row-level concurrency controls, likely `FOR UPDATE SKIP LOCKED` or an equivalent compare-and-update pattern, instead of the process-local FIFO locks used around SQLite.
- JSON dependency checks using SQLite `json_each` / `json_extract` must be translated to Postgres `jsonb` operators/functions and covered by tests.
- Timestamps are currently stored as text. The PG design must deliberately choose either `timestamptz` with conversion or text-compatible columns for low-risk cutover.
- Unique idempotency behavior must remain byte-for-byte compatible at API level: duplicate publish/create/append calls must return the existing object/effect, not fail.
- Pending outbox rows are live (`tq_saga_outbox=6`, `tq_session_outbox=31`). Cutover must either drain them before migration or migrate them and start PG-backed outbox workers without losing/replaying effects unexpectedly.
- Queue Service and worker processes are co-deployed and currently open the same SQLite file directly in some worker modes. PG cutover should centralize all DB access behind the queue service runtime or give every worker an explicit PG adapter, not leave mixed direct-SQL paths.

## Verification

- Remote health was green during inventory.
- Table counts were collected from the live file.
- Schema was collected with `sqlite3 /opt/novaic/data/queue.db ".schema"`.
- Code evidence was read from local checkout:
  - `queue_service/main.py`
  - `queue_service/db/schema.py`
  - `queue_service/queue_db.py`
  - `queue_service/saga_repo.py`
  - `queue_service/fsm/sqlite_store.py`
  - `queue_service/routes.py`
  - `queue_service/session_repo.py`
  - `queue_service/{task,saga,lease,session}_ledger.py`
  - `novaic-common/common/db/{database,locks}.py`

