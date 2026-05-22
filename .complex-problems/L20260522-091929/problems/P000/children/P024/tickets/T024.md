# Remaining Service Postgres Cutovers

## Problem Definition

The safe preparation phase is complete, but four production services still own active SQLite state. The user wants the remaining service-side databases moved to Postgres without maintaining production SQLite fallback logic.

Remaining active SQLite owners:

- Queue: `/opt/novaic/data/queue.db`
- Entangled: `/opt/novaic/data/entangled.db`
- Gateway: `/opt/novaic/data/gateway.db`
- Cortex: `/opt/novaic/data/cortex/operational.sqlite3`

## Proposed Solution

Split the implementation by service ownership and cut over one service at a time:

1. Queue to `novaic_queue`
   - Implement schema, adapter, data migration, deployment config, smoke tests, and rollback notes.
   - Preserve FSM, saga, lease, outbox, idempotency, JSON/time, and locking semantics from P008.
2. Entangled to `novaic_entangled`
   - Implement schema, adapter, data migration, deployment config, smoke tests, and rollback notes.
   - Preserve schema registration, sync-version monotonicity, transition atomicity, and API row shape from P009.
3. Gateway to `novaic_gateway`
   - Implement Postgres auth/config storage and migrate only `users`, `refresh_tokens`, and `config`.
   - Do not migrate retired zero-row Gateway tables.
4. Cortex to `novaic_cortex`
   - Implement Postgres operational store and migrate `cortex_operational_meta`, `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
   - Preserve idempotency, active-stack, projection, and payload manifest behavior from P010.

## Acceptance Criteria

- Each remaining service has a production Postgres-backed runtime path.
- Production SQLite fallback is removed or disabled after each service cutover.
- Existing SQLite state is backed up before migration and retained as rollback-only evidence after cutover.
- Postgres row counts and service-specific semantic checks match the pre-cutover source state.
- Health/readiness/API smoke checks pass after each cutover.
- The central SQLite classification note is updated after each service cutover.
- Final state leaves no active service-owned SQLite database without an explicit non-current/rollback-only classification.

## Verification Plan

- Before each cutover: capture SQLite backup, schema, row counts, live process/config evidence, and rollback commands.
- During each implementation: run focused local unit tests for adapter behavior; use fakes/mocks for unit tests rather than maintaining production SQLite fallback.
- Before production mutation when feasible: run migration in staging/test environment or as a dry-run against copied data.
- After each cutover: verify service health/readiness, representative API behavior, Postgres row counts, absence of SQLite writes, and rollback snapshot presence.
- After all cutovers: verify no active `*.db`/`*.sqlite3` files remain for service-owned state except rollback-only archives.

## Risks

- Queue is concurrency-sensitive and should probably be implemented first only if enough time is available for careful tests; otherwise Gateway is the smallest remaining cutover.
- Entangled sync-version mistakes can corrupt client/device state.
- Gateway auth migration can affect logins and refresh-token validity.
- Cortex operational projection mistakes can affect runtime control-plane behavior.

## Assumptions

- The existing `novaic-postgres` container and per-service databases/users are the target infrastructure.
- The development machine can run unit tests with fakes/mocks; integration behavior should be validated in the test environment or against copied production data before production cutover.
- Production cutovers should be serialized by service, not done as one large switch.
