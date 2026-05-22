# Isolate Session And Outbox SQLite Runtime Residue

## Problem Definition

Queue Service runtime wiring still defaults to a local `queue.db` SQLite path unless `NOVAIC_QUEUE_DB_BACKEND` is explicitly set. That is stale for the Postgres cutover and conflicts with the no-hidden-fallback direction. SQLite can remain available as an explicit adapter/test option, but production session/outbox runtime should not silently select or advertise local SQLite paths when Postgres configuration is expected.

## Proposed Solution

Make the runtime Postgres-first and make any SQLite use explicit:

1. Change Queue Service runtime default backend to `postgres`, with fail-fast DSN/DSN-file requirements coming from the Postgres database factory.
2. Keep `create_queue_database(backend="sqlite", ...)` for explicit tests/adapters, but do not let `main.py` silently default to it.
3. Update runtime-facing comments/logging/readiness output so `queue.db` is described only as explicit SQLite mode, not the normal production path.
4. Add static guard tests that assert Queue Service main does not default to SQLite, does not expose SQLite path in Postgres readiness, and confines local `.db` path handling to explicit SQLite branches.
5. Produce an audit artifact classifying remaining SQLite references as adapter/test/migration/runtime-removed.

## Acceptance Criteria

- `queue_service/main.py` defaults `NOVAIC_QUEUE_DB_BACKEND` to `postgres`.
- Runtime documentation/comments in `main.py` no longer state that `queue.db` is the normal database.
- SQLite path logging/readiness fields are only emitted under explicit SQLite backend branches.
- Static tests guard against reintroducing a SQLite runtime default or unguarded `queue.db` path in session/outbox runtime wiring.
- Audit artifact lists remaining SQLite references and explains why retained references are adapter/test/migration boundaries.

## Verification Plan

- Add or update focused tests for Queue Service database runtime configuration.
- Run the focused guard tests plus queue Postgres boundary tests and relevant session/outbox tests.
- Run compile checks for touched files.
- Run an `rg` audit and save the classified result under the ledger artifacts.

## Risks

- Defaulting to Postgres will fail startup in environments that have not provided `NOVAIC_QUEUE_POSTGRES_DSN` or `NOVAIC_QUEUE_POSTGRES_DSN_FILE`; this is intentional for production cutover clarity.
- Some developer scripts may still set SQLite explicitly for local fixtures. Those should remain explicit rather than hidden fallback.

## Assumptions

- The current deployment now has Postgres DSN configuration available.
- SQLite support remains acceptable only as an explicit adapter/test path during the transition.
