# Validate Entangled Migration Semantics Against Safe Staging Data

## Problem Definition

The offline migration command exists, but it must produce evidence that migrated target data semantically matches the SQLite source before production cutover. The validation must go beyond row counts: sync versions, transition IDs, `entangled_rowid`, representative value shapes, sequence state, and report redaction all need proof against a safe non-production or fixture-backed Postgres-compatible target.

## Proposed Solution

1. Add a validation artifact path that runs the migration command or module against a safe fixture-backed target first, using temporary SQLite data with representative JSON, BOOL, BLOB, INTEGER, REAL, TIMESTAMP, sync-version, transition, and stream-rowid values.
2. Capture the produced migration report as a ledger artifact after checking it contains no DSNs, passwords, tokens, or env-file contents.
3. Verify source/target row counts, exact sync-version key/value equality, transition count/max-ID equality, `entangled_rowid` equality to SQLite `rowid`, sequence restart values, and representative value shapes.
4. If a safe remote staging Postgres target is immediately available without touching production, optionally run the same validation there; otherwise leave real remote staging to the following REST/WS staging children.
5. Record a concise validation report with table counts, semantic checks, value-shape checks, sequence checks, and residual risks.

## Acceptance Criteria

- A validation path runs the migration against a safe non-production or fixture-backed Postgres-compatible target.
- Row counts match for every migrated active fixture table.
- Sync-version key/value pairs match exactly.
- Transition count and max ID match exactly.
- `entangled_rowid` is populated and equals SQLite `rowid` for dynamic stream/list fixture rows.
- Representative JSON, BOOL, BLOB, INTEGER, REAL, and TIMESTAMP values are checked.
- Sequence reset/restart evidence proves generated IDs will advance beyond migrated maxima.
- A redacted validation report is written under the ledger artifacts.
- Focused tests or validation commands and full Entangled pytest pass.

## Verification Plan

Run the validation command/path, inspect the generated validation report for semantic pass statuses and no secret content, run focused migration tests, and run full Entangled server-python pytest.

## Risks

- Fixture-backed validation may not expose all live schema edge cases; remote staging validation still matters before production cutover.
- BLOB/JSON/BOOL representation through a fake target can differ from psycopg behavior; this must be called out if no real Postgres target is used.
- Accidentally copying production SQLite into a non-clean target would make counts misleading; validation must use a clean target or fixture.

## Assumptions

- `P049` migration command and follow-up target preparation are complete.
- It is acceptable for this child to use fixture-backed Postgres-compatible validation if real remote staging is not yet safely prepared.
