# Port Entangled basic write queries to Postgres

## Problem Definition

Entangled basic write paths still embed SQLite timestamp expressions and SQLite auto-ID handling. P046 must add dialect-aware write helpers for create, append, update, upsert, delete, batch update/delete, update_where, and CAS without touching stream pagination or production runtime.

## Proposed Solution

1. Add `SqlEntityStore` helper methods for backend dialect, timestamp update expression, auto-ID returning, and insert SQL construction.
2. Use these helpers in `_sql_create` and `append` so Postgres auto-integer IDs use `RETURNING`.
3. Replace raw `updated_at = datetime('now')` write expressions with a dialect helper.
4. Keep rowcount-driven behavior unchanged for update/delete/CAS/batch paths.
5. Add fake-Postgres tests that capture generated SQL for create/update/upsert/delete/CAS paths.
6. Run full Entangled tests to prove SQLite compatibility.

## Acceptance Criteria

- SQLite write SQL remains compatible and existing tests pass.
- Postgres write SQL does not emit `datetime('now')`.
- Postgres auto-integer create/append paths use `RETURNING`.
- Postgres upsert/update/CAS SQL keeps conflict targets and rowcount behavior.
- User/key-param/parent scoping remains unchanged.
- Focused SQL-capture tests and full Entangled tests pass.

## Verification Plan

Run targeted write-query tests, full Entangled pytest, and py_compile for touched modules. Do not modify production or run migration in this child.

## Risks

- Some callers may rely on cursor `lastrowid`; Postgres paths need a compatible alternative.
- Timestamp update expression must preserve first-cutover wire format.

## Assumptions

- Stream rowid/list pagination work remains in P047.
- Output-shape cross-checks remain in P048.
