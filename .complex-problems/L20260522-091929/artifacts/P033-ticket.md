# Cortex Postgres Operational Store Implementation

## Problem Definition

Cortex needs a Postgres-backed operational store that preserves the current SQLite operational store API for `scope_events`, `scope_projection`, `active_stack_projection`, `payload_manifest`, and `cortex_operational_meta`.

## Proposed Solution

1. Inspect current Cortex operational store, main config, and tests.
2. Add an explicit Postgres operational store implementation or adapter.
3. Add runtime configuration for `sqlite` vs `postgres` operational backend.
4. Preserve API behavior, row shapes, JSON string handling, idempotency uniqueness, and projection semantics.
5. Add a migration helper script for P034.
6. Run focused Cortex tests.

## Acceptance Criteria

- Cortex can initialize a Postgres operational store.
- The Postgres schema covers all five operational tables with required constraints/indexes.
- Existing tests for operational store behavior pass or are extended for the Postgres contract.
- Production default remains unchanged until P034.
- No production data/config/runtime state is changed.

## Verification Plan

- Use `rg`/file inspection to map store call sites.
- Run existing Cortex tests and targeted compile checks.
- Record changed files and any production cutover prerequisites.

## Risks

- The store may rely on SQLite-specific transaction behavior.
- JSON text fields must not accidentally change API output shape.
- Postgres connection dependency may be absent in the Cortex venv until production preflight.

## Assumptions

- P034 handles production backup, data migration, dependency install, runtime switch, and restart.
