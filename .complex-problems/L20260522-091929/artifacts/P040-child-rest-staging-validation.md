# Validate Entangled Postgres Mode With REST Smokes

## Problem

The migrated/staging Postgres target must be exercised by an Entangled process running in Postgres mode, not only by offline SQL checks. This belongs under `P040` because production cutover needs proof that the runtime starts, registers schemas, serves REST reads/writes, and does not open the SQLite database file in Postgres mode.

## Success Criteria

- A staging or local test Entangled process starts with `--db-backend postgres` against a safe test target.
- Health/readiness endpoints return success in Postgres mode.
- Process arguments and file-handle checks show Entangled is not opening the active SQLite database file.
- Schema registration completes without Postgres DDL errors.
- REST smoke checks pass for representative list/read, singleton upsert/read, stream append/query, update, delete, and CAS or equivalent rowcount-sensitive behavior.
- Smoke-test output is captured in a redacted report without secrets.
- Any unavailable auth/client dependency is explicitly documented with the smallest equivalent direct API proof and a follow-up gap if the REST behavior cannot be proven.
