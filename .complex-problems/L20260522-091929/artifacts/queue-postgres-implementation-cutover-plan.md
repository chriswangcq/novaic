# Queue Postgres Implementation and Cutover Plan

## Scope

Artifact for P014 / T014. This is the implementation and cutover plan for migrating Queue Service from `/opt/novaic/data/queue.db` to the existing Postgres database `novaic_queue` on `api.gradievo.com`.

This ticket does not cut over production.

## Inputs

- P012 inventory: `.complex-problems/L20260522-091929/artifacts/queue-sqlite-inventory.md`
- P015 concurrency map: `.complex-problems/L20260522-091929/artifacts/queue-pg-task-saga-lease-semantics.md`
- P016 replay map: `.complex-problems/L20260522-091929/artifacts/queue-pg-session-outbox-idempotency-semantics.md`
- P017 SQL compatibility map: `.complex-problems/L20260522-091929/artifacts/queue-pg-jsonb-time-index-sqlite-assumptions.md`

## Current Production Facts

- Live SQLite path: `/opt/novaic/data/queue.db`
- Queue service health: `/health` reports SQLite path.
- Live DB is non-empty and active.
- Live pending outbox rows from P012:
  - `tq_saga_outbox=6`
  - `tq_session_outbox=31`
- Runtime users include queue-service, task workers, saga workers, session/saga outbox workers, health, and scheduler.

## Phase 0: Preconditions

Goal: confirm the target and freeze the rules before code changes.

Tasks:

- Confirm `novaic_queue` DB and queue DB user/secret exist in the existing `novaic-postgres` Docker service.
- Confirm queue migration will be server-runtime Postgres-only.
- Confirm SQLite remains only a migration source/rollback archive, not a maintained server fallback.
- Confirm test environment can run Queue Service and workers against Postgres.

Exit checks:

- `novaic-postgres` healthy.
- `novaic_queue` reachable from the API host.
- Secret path for Queue PG DSN exists with `0600 root:root`.
- No production queue cutover attempted.

## Phase 1: Postgres Schema

Goal: create PG schema compatible with P015/P016/P017.

Touched areas:

- New Queue PG schema DDL/migration script.
- Target DB: `novaic_queue`.

Required schema choices:

- Use `jsonb` for payload/context/result/dependency/outbox JSON fields.
- Use `timestamptz` for all time fields.
- Preserve primary keys and idempotency unique constraints.
- Preserve partial pending outbox indexes.
- Preserve in-progress idempotency lease index.
- Add JSON expression indexes:
  - `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`
  - `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`
- Add outbox claim metadata required by P016 before supporting multiple PG outbox workers:
  - `claimed_by`
  - `claim_until`
  - optional `claim_token`
- Do not add foreign keys in first cutover unless separately tested.

Verification:

- Apply schema to empty `novaic_queue`.
- Verify table list equals intended Queue tables.
- Verify all unique and partial indexes exist.
- Verify JSONB/timestamptz column types.
- Verify outbox claim metadata exists or document single-worker constraint.

## Phase 2: Postgres Adapter and Runtime Boundary

Goal: introduce PG runtime path without maintaining long-term SQLite fallback.

Touched areas:

- `novaic-agent-runtime/queue_service/main.py`
- `novaic-agent-runtime/queue_service/db/schema.py` or new PG schema module.
- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py` replacement/generalization.
- `novaic-common/common/db` or Queue-local PG adapter.
- Queue service config/secrets.

Implementation rules:

- Add explicit backend config: `postgres`.
- Fail fast if production Queue starts without PG DSN after cutover.
- Do not silently create or use `queue.db` in production PG mode.
- Keep SQLite code only as migration-source tooling or isolated unit-test fixture, not runtime fallback.
- PG adapter must support:
  - explicit transaction scopes
  - row locks
  - `FOR UPDATE SKIP LOCKED`
  - JSONB binding/decoding
  - `timestamptz` binding/decoding
  - `ON CONFLICT` idempotency handling
  - PG exception classification

Verification:

- Unit tests against fake/fixture ports for pure logic.
- Integration tests in test environment against real Postgres.
- Static grep confirms production runtime has no accidental `queue.db` open path in PG mode.

## Phase 3: Repository SQL Conversion

Goal: convert queue repositories to PG-safe SQL.

Touched areas:

- `queue_service/queue_db.py`
- `queue_service/saga_repo.py`
- `queue_service/session_repo.py`
- `queue_service/session_ledger.py`
- `queue_service/task_ledger.py`
- `queue_service/saga_ledger.py`
- `queue_service/lease_ledger.py`
- `queue_service/session_outbox.py`
- `queue_service/saga_outbox_worker.py`
- `queue_service/session_outbox_worker.py`
- `queue_service/routes.py`

Required conversions:

- Task/saga claim and recovery use `FOR UPDATE SKIP LOCKED`.
- Single task/saga operations use `SELECT ... FOR UPDATE` on state rows.
- Session dispatch/finalize ensures `tq_session_state` row exists, then locks it.
- Outbox drain claims rows before external publish.
- Idempotency ledger locks by `idempotency_key`.
- SQLite JSON functions become JSONB expressions.
- SQLite `datetime(...)` comparisons become native `timestamptz` comparisons.
- SQLite busy string matching is removed from PG path.
- `rowid` ordering becomes `(created_at, id)`.

Verification:

- Tests for duplicate claim losers.
- Tests for completion/recovery race.
- Tests for session first-dispatch race.
- Tests for publish-before-ack outbox retry.
- Tests for duplicate idempotency completed/in-progress.
- Tests for JSONB dependency readiness.
- Tests for route defer behavior under simulated PG transient exceptions.

## Phase 4: Migration Tooling

Goal: copy SQLite data into PG with deterministic validation.

Touched areas:

- New migration script, likely under `novaic-agent-runtime/scripts/` or ops tooling.
- Source: `/opt/novaic/data/queue.db`.
- Target: `novaic_queue`.

Migration steps:

- Read source SQLite in read-only mode.
- Create a timestamped SQLite backup before final copy.
- Convert JSON text to JSONB.
- Convert ISO text timestamps to UTC `timestamptz`.
- Preserve IDs, generations, states, statuses, attempts, idempotency keys, and created/updated ordering.
- Copy tables in dependency-safe order:
  1. projection/content tables
  2. event tables
  3. state tables
  4. idempotency ledger
  5. outbox tables
  6. config/schema marker
- Record migration manifest with source file stat, row counts, target row counts, checksum queries, and script version.

Dry-run verification:

- Row counts match per table.
- Required non-null columns have no null conversion failures.
- JSONB parse failures are zero.
- Timestamp parse failures are zero.
- Event/state projection checks pass:
  - `tq_tasks` count equals `tq_task_state` count.
  - `tq_sagas` count equals `tq_saga_state` count.
  - lease state rows have unique `(machine_type, machine_id)`.
  - idempotency primary key count equals row count.
  - outbox status counts match.
- Pending outbox rows are either drained before migration or copied with same statuses.

## Phase 5: Test Environment Cutover

Goal: prove PG Queue runtime before production.

Steps:

- Restore a copy of production `queue.db` into a test environment.
- Run migration into test Postgres.
- Start Queue Service and all workers in PG mode.
- Run smoke tests:
  - `/health`
  - `/ready`
  - publish test task
  - claim test task
  - complete test task
  - create/claim/launch saga
  - session dispatch start
  - session attach path
  - outbox drain retry
  - idempotency duplicate completed
  - stale recovery no-op on fresh heartbeat

Exit checks:

- No SQLite file is opened by PG-mode Queue runtime.
- Health/readiness report PG backend.
- All smoke tests pass.
- Logs contain no `sqlite_busy` in PG mode.

## Phase 6: Production Pre-Cutover

Goal: prepare a low-risk cutover window.

Pre-cutover checks:

- Confirm latest `queue.db` backup location and restore command.
- Capture live row counts and status counts:
  - all tables
  - task states
  - saga states
  - session states
  - lease states
  - outbox statuses
  - idempotency statuses
- Capture live process list.
- Decide outbox strategy:
  - drain pending outbox rows to zero before migration, or
  - stop writers/workers and migrate pending rows.
- Announce no production cutover if pending outbox policy is unresolved.

Stop order for final copy:

1. Stop scheduler/producers.
2. Stop task workers.
3. Stop saga workers.
4. Stop session/saga outbox workers.
5. Stop queue-service last.
6. Confirm no `lsof /opt/novaic/data/queue.db` holders.

## Phase 7: Production Cutover Window

Goal: final copy and start PG runtime.

Steps:

- Take final SQLite backup.
- Run final migration to `novaic_queue`.
- Run validation manifest.
- Update Queue Service config to PG DSN.
- Start queue-service in PG mode.
- Start outbox workers.
- Start saga workers.
- Start task workers.
- Start scheduler/producers.

Immediate post-cutover checks:

- `/health` reports PG backend.
- `/ready` passes.
- No process opens `/opt/novaic/data/queue.db`.
- Row counts in PG match final manifest.
- Pending outbox status counts match selected policy.
- Task/saga/session/lease state counts match final manifest.
- Idempotency row count and status counts match final manifest.
- Smoke task publish/claim/complete succeeds.
- Saga claim/launch smoke succeeds.
- Session dispatch smoke succeeds.
- Logs have no SQLite busy strings.

## Rollback Boundaries

Pre-cutover rollback:

- If code is deployed but config still points to SQLite, revert code/config and restart current services.
- No data reconciliation required.

Stopped-before-PG-writers rollback:

- If final migration or validation fails before PG-backed queue-service accepts writes, restart the old SQLite-backed services with the untouched `queue.db` or final backup.
- Discard partial PG load and rerun later.

After-PG-writers-start rollback:

- Stop all PG-backed Queue producers/workers immediately.
- Compare PG writes since cutover with final SQLite backup.
- If no new successful writes occurred, restart SQLite-backed services from final backup.
- If new writes occurred, do not blindly roll back. Either:
  - migrate the delta back to SQLite with a reviewed script, or
  - keep PG runtime and fix forward.

Rollback blocker:

- Once outbox effects have been published from PG, rolling back to SQLite can duplicate external effects unless idempotency keys are verified. Treat this as manual incident handling, not a simple restart.

## Stabilization and Cleanup

Stabilization window:

- Keep final SQLite backup read-only.
- Keep old `queue.db` out of runtime path.
- Monitor:
  - claim latency
  - outbox pending/dead-letter
  - idempotency contention
  - stale recovery counts
  - DB locks/deadlocks
  - Queue health/readiness

Cleanup after stabilization:

- Mark `/opt/novaic/data/queue.db` as non-current rollback archive.
- Remove or disable production code paths that auto-create SQLite `queue.db`.
- Remove SQLite busy logs from PG runtime.
- Archive migration manifests and validation reports.
- Only delete rollback SQLite archive after an explicit retention decision.

## Do Not Cut Over If

- PG schema is missing outbox claim metadata or single-worker constraint is not accepted.
- Migration dry-run has JSON/timestamp parse failures.
- Pending outbox policy is unresolved.
- Test environment cannot pass claim/complete/saga/session/idempotency smoke tests.
- PG health/readiness endpoint cannot distinguish PG backend from SQLite.
- Rollback command and final SQLite backup location are not documented.

