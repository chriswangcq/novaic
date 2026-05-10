# Implement Operational SQLite Store Module

## Problem Definition

The Phase 1A child problem needs a tested, deterministic SQLite state port for Cortex operational state. This port must be reusable by later migration phases and must not hide dependencies on process time, random IDs, environment variables, or in-memory fallback.

## Proposed Solution

Finish the `novaic_cortex.operational_store` module and add direct tests:

- Validate constructor inputs and reject `:memory:`.
- Initialize the operational SQLite schema.
- Implement scope event append/list with idempotency-key semantics.
- Implement scope projection, active stack projection, and payload manifest CRUD-style helpers.
- Add tests using injected deterministic clock and ID providers.

## Acceptance Criteria

- Store module supports all Phase 1 schema tables and basic operations.
- Unit tests prove deterministic clock/ID behavior.
- Idempotent append returns the same event for matching retries and raises on conflicting semantic retries.
- Payload manifests store only metadata/blob refs, not raw payload bytes.

## Verification Plan

- Run `pytest` for the new operational store tests.
- Run a syntax/import check for `novaic_cortex.operational_store`.
- Inspect the implementation for hidden `time.time`, `uuid.uuid4`, `os.environ`, and `:memory:` fallback usage.

## Risks

- Generating time/ID before an idempotency lookup can make retries consume hidden inputs unnecessarily.
- Overloading the module with migration behavior would blur the Phase 1 boundary.

## Assumptions

- SQLite stdlib is available in the Cortex runtime.
- Later phases will own converting existing projection/log behavior to this store.
