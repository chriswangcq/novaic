# Implement Remaining Service Postgres Cutovers

## Problem

The first safe phase is complete: Postgres is provisioned, LLM Factory is on Postgres, SQLite owners are classified, high-risk semantics are mapped, and stale residue is cleaned. The remaining user goal is to migrate all remaining service-side persistent state off SQLite and onto the existing per-service Postgres databases without maintaining production SQLite fallback logic.

Remaining active SQLite owners:

- `/opt/novaic/data/queue.db`
- `/opt/novaic/data/entangled.db`
- `/opt/novaic/data/gateway.db`
- `/opt/novaic/data/cortex/operational.sqlite3`

## Proposed Solution

Implement the remaining cutovers as separate service-owned migrations under one execution package:

1. Queue: implement Postgres schema/adapter/migration/cutover for `novaic_queue`, preserving FSM, saga, lease, outbox, idempotency, JSON/time, and locking semantics.
2. Entangled: implement Postgres schema/adapter/migration/cutover for `novaic_entangled`, preserving schema registration, sync versions, transition atomicity, row shapes, and API behavior.
3. Gateway: implement Postgres auth/config adapter/migration/cutover for `novaic_gateway`, migrating only `users`, `refresh_tokens`, and `config`.
4. Cortex: implement Postgres operational store/migration/cutover for `novaic_cortex`, migrating all five operational tables.
5. Remove production SQLite fallback paths after each service is stabilized; use unit-test fakes or mocks for local development and run integration tests in the test environment.

## Success Criteria

- Each remaining service has a production Postgres-backed code path and deployed runtime configuration.
- No production service keeps SQLite fallback logic for the migrated state path.
- Existing SQLite state is backed up before mutation and migrated with row-count/referential checks.
- Service-specific behavior is preserved according to the artifacts produced in P008, P009, P010, and P011.
- Live health/readiness checks pass after each cutover.
- Rollback instructions and retained snapshots are recorded for each service.
- Final SQLite classification note identifies remaining SQLite files as rollback-only snapshots or separately justified non-service data.

## Verification Plan

- Run service-specific unit tests for adapter behavior locally where available.
- Run schema/migration dry-runs or staging integration tests before production cutover when feasible.
- Before each production cutover, capture SQLite backup, row counts, and relevant semantic invariants.
- After each production cutover, verify service health, API smoke tests, Postgres row counts, and absence of new active SQLite writes.
- Verify no production code path recreates the old SQLite owner file.

## Risks

- Queue has the highest concurrency/FSM risk; it may need the most granular implementation ticketing.
- Entangled sync version behavior can corrupt client state if monotonic ordering or transition atomicity changes.
- Gateway auth migration can invalidate sessions if refresh token handling changes unexpectedly.
- Cortex active-stack/projection migration can affect runtime control-plane behavior if projections are dropped or rebuilt incorrectly.

## Assumptions

- The existing `novaic-postgres` container and per-service databases/users remain the target infrastructure.
- Development machines do not need SQLite fallback for integration behavior; unit tests can use fakes/mocks or ephemeral Postgres where appropriate.
- Production cutovers should be one service at a time, with backups and rollback notes before every mutation.
