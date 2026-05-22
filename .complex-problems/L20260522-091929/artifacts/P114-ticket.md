# Clean Queue Startup Default Ticket

## Problem Definition

`novaic-agent-runtime/main_novaic.py` still defaults `--db-backend` to `sqlite`, even though the active Queue Service runtime default is Postgres. This is misleading residue: future local/staging smoke commands could accidentally validate SQLite while believing they are validating the current server path.

## Proposed Solution

1. Inspect the startup CLI code and focused tests.
2. Change the CLI default from implicit SQLite to Postgres.
3. Preserve SQLite only as an explicit `--db-backend sqlite` or env-selected adapter/test mode.
4. Add or update a focused test that guards `main_novaic.py` from regressing to an implicit SQLite default.
5. Run the focused tests around Queue runtime defaults.

## Acceptance Criteria

- `main_novaic.py` no longer defaults Queue DB backend to SQLite.
- Explicit SQLite selection remains possible where the CLI supports it.
- Tests prove both `queue_service/main.py` and `main_novaic.py` default to Postgres.
- No unrelated startup behavior is rewritten.

## Verification Plan

- Search for `NOVAIC_QUEUE_DB_BACKEND` startup defaults.
- Patch the smallest relevant code path.
- Run focused pytest tests for runtime default guards.

## Risks

- Local scripts that relied on implicit SQLite must now opt in explicitly.
- Static source tests can become brittle if over-specified; keep assertions narrow and behavior-focused.

## Assumptions

- The user's desired architecture is a single Postgres server path with SQLite only for explicit tests/adapters.
