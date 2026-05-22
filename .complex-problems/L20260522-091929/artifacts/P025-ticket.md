# Gateway Postgres Auth Config Cutover

## Problem Definition

Gateway currently stores active auth/config state in `/opt/novaic/data/gateway.db`. The target is to move the active production Gateway state to `novaic_gateway` Postgres and stop using SQLite as the production runtime store.

Scope tables:

- migrate: `users`, `refresh_tokens`, `config`
- do not migrate: zero-row retired tables from P021/P023

## Proposed Solution

Split Gateway cutover into two bounded stages:

1. Implement the Gateway Postgres storage path.
   - Add Postgres schema/connection/config support in Gateway.
   - Preserve current auth/config APIs and row shapes.
   - Add or update focused tests for Gateway auth/config storage behavior.
   - Keep production SQLite fallback out of the final runtime path; test-only fakes are acceptable.
2. Migrate and cut over production Gateway.
   - Back up `/opt/novaic/data/gateway.db`.
   - Copy `users`, `refresh_tokens`, and `config` into `novaic_gateway`.
   - Switch Gateway runtime config to Postgres.
   - Verify health, login/auth smoke behavior, row counts, and absence of active SQLite writes.
   - Update the central SQLite classification note and rollback notes.

## Acceptance Criteria

- Gateway production runtime uses `novaic_gateway` for auth/config state.
- `users`, `refresh_tokens`, and `config` are migrated with row-count checks.
- Retired zero-row tables are not recreated in Postgres.
- Gateway health and auth/config smoke checks pass after cutover.
- `/opt/novaic/data/gateway.db` is no longer active state and is retained only as rollback evidence.
- The central classification note is updated.

## Verification Plan

- Inspect current Gateway storage code and tests before editing.
- Run focused local Gateway tests after implementation.
- Before production migration, capture SQLite backup, schema, and row counts.
- After production migration, verify Postgres row counts and representative auth/config behavior.
- Verify no Gateway process writes to SQLite after cutover.

## Risks

- Password/login behavior can regress if user row shape changes.
- Refresh-token migration can invalidate active sessions if token/expires semantics change.
- Runtime config mistakes can make Gateway start with an empty store.

## Assumptions

- `novaic_gateway` database/user already exists in `novaic-postgres`.
- Gateway should not keep production SQLite fallback after cutover.
- Integration smoke can be performed on the `api` host after deployment.
