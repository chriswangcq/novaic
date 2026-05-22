# Define Entangled Postgres Implementation and Cutover Requirements

## Problem Definition

Entangled has a live SQLite inventory and a semantic Postgres mapping, but it still needs a concrete implementation and cutover requirements plan. The plan must target the existing `novaic_entangled` Postgres database, avoid production cutover during P020, and make later implementation safe to execute without rediscovering the same risks.

## Proposed Solution

Create one no-cutover implementation and cutover requirements artifact.

1. Use P018 and P019 as inputs.
2. Define implementation phases:
   - config and dependency changes;
   - Postgres adapter boundary;
   - Postgres DDL/type generator;
   - entity-store SQL conversion;
   - sync-version and transition-log conversion;
   - migration/export/import tooling;
   - local unit tests and test-environment integration tests;
   - deployment and production cutover window;
   - stabilization and SQLite residue cleanup.
3. Define target database and environment policy:
   - `novaic_entangled` on the existing `novaic-postgres` container;
   - production and integration use Postgres;
   - no maintained production SQLite fallback;
   - SQLite allowed only as narrow unit-test doubles/fakes if they do not require duplicate production logic.
4. Define pre/post validation:
   - row counts, schema/index parity, sync-version equality and monotonicity, transition history, rowid replacement, JSON decode, timestamp wire format, health/readiness, process holders, and no SQLite open files after cutover.
5. Define WebSocket/client smoke tests.
6. Define rollback boundaries and old SQLite cleanup criteria.
7. Write `.complex-problems/L20260522-091929/artifacts/entangled-postgres-implementation-cutover-plan.md`.

## Acceptance Criteria

- A phased implementation plan exists for config, adapter, DDL, store SQL, migration tooling, tests, deployment, stabilization, and cleanup.
- The plan targets `novaic_entangled` and states the no-production-SQLite-fallback policy.
- Pre-cutover and post-cutover checks cover table counts, schema/index parity, sync-version equality/monotonicity, JSON decode, timestamp compatibility, transition history, rowid replacement, and health/readiness.
- WebSocket/client smoke tests cover schema push, list/form/stream full sync, create/update/delete or append delta, and reconnect after restart.
- Rollback boundaries are documented for before PG writes, after PG writes with no client-visible deltas, and after client-visible deltas.
- Old SQLite cleanup criteria are documented for the stabilization window.
- No production Entangled cutover is attempted.

## Verification Plan

- Verify the artifact has explicit phases, validation matrix, smoke tests, rollback boundaries, and cleanup rules.
- Verify every P020 success criterion maps to a concrete section.
- Verify the artifact references P018/P019 artifacts and marks production cutover as out of scope.
- Record the result and run a skeptical P020 success check.

## Risks

- The plan may look safe but still hide a dual-write or fallback path; explicitly ban production SQLite fallback.
- A migration without rowid preservation can subtly break stream pagination.
- A migration without version equality checks can break reconnect/delta semantics.
- Postgres FK enforcement can fail on historical data if enabled too early.
- Rollback after client-visible PG deltas is not symmetric unless writes are replayed or accepted as lost.

## Assumptions

- The existing Postgres infrastructure from P001 is available and contains `novaic_entangled`.
- P020 does not edit Entangled code or production runtime.
- Later implementation tickets will refresh live row counts immediately before cutover.
