# Implement or Verify LLM Factory Postgres Backend

## Problem Definition

`llm-factory` must be able to run against the dedicated `novaic_llm_factory` Postgres database before production data can be migrated or Docker runtime can be cut over. The current deployed configuration points at `/data/llm_factory.db`, and the code appears SQLite-oriented until proven otherwise.

## Proposed Solution

Inspect the `novaic-llm-factory` config and database layer, identify the persistence API surface, and add the smallest explicit backend boundary needed for Postgres. Prefer preserving the existing method names and behavior so the API layer does not need broad rewrites. Implement idempotent Postgres schema creation for the existing tables and keep SQLite as the rollback/default backend unless config explicitly selects Postgres.

## Acceptance Criteria

- The existing persistence API surface is identified.
- Config can explicitly select Postgres using a DSN or equivalent root-readable config value.
- Postgres schema creation supports the existing `api_keys`, `models`, `user_keys`, and `llm_logs` tables.
- Existing SQLite behavior remains available for rollback.
- A smoke test or script verifies basic insert/read/update/delete behavior for the Postgres backend.

## Verification Plan

Inspect code with `rg` and focused file reads, implement the adapter/config path if missing, run available tests or a focused smoke script locally, then optionally run the same smoke against the `api` host's local Postgres if safe. Verify no credentials are committed into the repository.

## Risks

- The SQLite implementation may use SQL or row behavior that does not translate directly to Postgres.
- A wide abstraction rewrite could destabilize the service; the change should stay close to current persistence methods.
- Postgres credentials must not be stored in repo files.

## Assumptions

- The service code in this workspace is the source used to build the deployed `novaic/llm-factory:local` image.
- It is acceptable for SQLite to remain the default backend until Docker cutover.
