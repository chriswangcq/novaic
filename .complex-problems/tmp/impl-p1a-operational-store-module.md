# Phase 1A Operational Store Module And Unit Tests

## Problem

Create the Cortex-owned SQLite operational store as a reusable substrate with explicit dependencies and deterministic behavior. This child problem owns the module API, schema creation, and direct unit tests. It must not migrate existing active-stack or scope-transition behavior yet.

## Success Criteria

- Add or finish `novaic_cortex.operational_store` with explicit SQLite path, clock, and ID provider.
- Reject memory-only fallback and avoid hidden env/time/id inputs inside tested behavior.
- Create schema tables for `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
- Add direct unit tests for initialization, append/read, idempotency conflict behavior, projection read/write, active stack read/write, and payload manifest read/write.
