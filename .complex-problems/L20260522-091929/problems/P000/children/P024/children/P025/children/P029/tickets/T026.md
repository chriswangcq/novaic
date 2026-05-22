# Gateway Postgres Storage Implementation

## Problem Definition

Gateway needs an implementation path that can store active `users`, `refresh_tokens`, and `config` in Postgres. This problem is implementation-only: it should not mutate production data or switch the production runtime.

## Proposed Solution

1. Inspect Gateway DB/schema/access/auth/config call sites.
2. Add explicit Gateway database backend configuration for Postgres.
3. Implement Postgres DDL and adapter behavior for `users`, `refresh_tokens`, and `config`.
4. Keep retired Gateway tables out of the Postgres schema.
5. Preserve current API row shapes and auth/config behavior.
6. Add or update focused tests for the storage contract.

## Acceptance Criteria

- Gateway source supports a Postgres-backed production storage path.
- SQLite-only SQL assumptions are isolated or removed from production Gateway runtime logic.
- No production SQLite fallback is required for migrated Gateway state.
- Focused tests pass locally.
- No production data/config/service is changed by this ticket.

## Verification Plan

- Run `rg` over Gateway source to find DB access points.
- Run the focused Gateway test subset after implementation.
- Run static compile/import checks if the repo lacks a runnable DB integration test.
- Record files changed and remaining production cutover steps.

## Risks

- Gateway auth code may depend on SQLite cursor behavior.
- Password hash and refresh-token handling must not change.
- If tests are SQLite-only today, an adapter contract may need test fakes rather than a live Postgres dependency.

## Assumptions

- Production cutover and data migration are handled by P030, not this ticket.
- Test-only fakes/mocks are allowed; production SQLite fallback is not.
