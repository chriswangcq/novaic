# Define Queue Postgres Implementation and Cutover Plan

## Problem Definition

Queue migration now has inventory and semantic design inputs, but it still needs an implementation/cutover plan before any production cutover. The plan must convert P012/P013 evidence into phased coding, migration, verification, rollback, and cleanup work while keeping production Queue running on SQLite until a deliberate cutover window.

## Proposed Solution

Produce a phased plan covering:

- PG schema and adapter implementation using the P015/P016/P017 semantic maps.
- Explicit Postgres-only repository/runtime path with no long-term SQLite fallback.
- Migration scripts from live `queue.db` into `novaic_queue`.
- Dry-run validation for row counts, event/state projection consistency, outbox rows, leases, idempotency rows, JSONB/timestamp conversion, and health endpoints.
- Runtime cutover order for stopping producers/workers, copying final state, starting PG-backed services, smoke testing, and retaining SQLite rollback archives.
- Rollback boundaries and "do not cut over" blockers.
- Old SQLite residue cleanup policy after successful stabilization.

This ticket should produce a plan artifact only; it must not cut over production.

## Acceptance Criteria

- The plan breaks implementation into safe phases with clear order and dependencies.
- Each phase lists the code modules/scripts it touches and what it must verify.
- Pre-cutover and post-cutover checks include row counts, projection/event consistency, outbox pending/published/dead-letter state, leases, idempotency, queue health, worker smoke tests, and API behavior.
- Rollback boundaries distinguish pre-cutover, mid-cutover before PG writers, and post-cutover after PG writers.
- The plan explicitly says production queue cutover is not attempted by this ticket.
- The plan identifies cleanup targets for old SQLite residue after stabilization.

## Verification Plan

Review the plan against:

- P012 inventory artifact.
- P015 task/saga/lease semantics.
- P016 session/outbox/idempotency semantics.
- P017 JSONB/time/index/SQLite-assumption map.
- Current production process ownership and live pending outbox counts.

The success check should reject the plan if it lacks rollback boundaries, outbox handling, or no-cutover guarantees.

## Risks

- A plan that jumps straight to code can miss operational cutover hazards.
- A plan without explicit outbox handling can lose or duplicate effects.
- A plan without rollback boundaries can trap production in a half-migrated state.
- A plan that leaves SQLite fallback in server runtime violates the user's desired single-DB direction.

## Assumptions

- The target PG database for Queue is `novaic_queue` on the existing `novaic-postgres` Docker service.
- Production Queue remains SQLite-backed until a later explicit implementation/cutover ticket.
- Local unit tests may use fakes/fixtures, but server runtime should be Postgres-only after migration.

