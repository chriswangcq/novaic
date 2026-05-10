# Phase 1 Cortex Operational SQLite Store Substrate

## Problem Definition

Cortex still needs a durable operational state substrate before scope transition events, active stack/status projections, and payload manifests can stop depending on local projection files, process memory, or scattered helper logic. The substrate must be a reusable Cortex-owned SQLite state port with explicit clock/id dependencies and no in-memory fallback.

## Proposed Solution

Implement Phase 1 as the minimal durable substrate only:

- Add a `novaic_cortex.operational_store` SQLite module with explicit filesystem database path, injected clock, and injected ID provider.
- Initialize a schema for `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
- Provide small methods for append/read/upsert/get operations that later phases can migrate onto without duplicating SQL.
- Wire the store through Cortex registry/startup so runtime construction has one explicit operational SQLite path.
- Add focused unit tests for schema creation, event append/idempotency behavior, projections, active stack, and payload manifests.
- Update startup/docs tests enough that the new required dependency is visible at the service boundary.

This ticket intentionally does not migrate old active-stack or scope-transition callers yet; those are Phase 2 and Phase 3 tickets.

## Acceptance Criteria

- `OperationalSqliteStore` exists and rejects memory-only fallback.
- Store construction requires explicit SQLite path and explicit clock/id boundaries.
- Tables exist for scope events, scope projections, active stack projections, and payload manifests.
- Idempotent scope event append returns the existing event for matching retry keys and raises on semantic conflicts.
- Registry/startup wiring passes a concrete operational SQLite path into Cortex.
- Tests cover schema initialization, append/read, idempotency, projection read/write, active stack read/write, and payload manifest read/write.

## Verification Plan

- Run the new operational store tests directly.
- Run existing Cortex registry dependency tests to ensure explicit boundary expectations still hold.
- Run static searches for forbidden `:memory:` fallback and unregistered operational store construction paths.
- Inspect startup scripts and Cortex CLI args to confirm the SQLite path is mandatory at the service boundary.

## Risks

- Adding the store without wiring would repeat the previous “new code not on live path” failure mode.
- Wiring the store too deeply in Phase 1 could accidentally migrate behavior before Phase 2/3 tests exist.
- Hidden time/id generation inside repository methods would make event behavior non-reproducible in tests.

## Assumptions

- SQLite is acceptable for Cortex operational/control state.
- Raw payload bytes remain outside SQLite; SQLite only stores manifests and semantic metadata.
- Phase 1 may introduce the substrate and explicit construction boundary before cutting existing behavior over.
