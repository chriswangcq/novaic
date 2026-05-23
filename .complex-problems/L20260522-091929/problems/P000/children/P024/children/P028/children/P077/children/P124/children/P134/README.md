# Verify Production Queue Postgres Migration Semantics

## Problem

After the data copy, production Postgres must be checked against the frozen SQLite backup for row counts and semantic invariants before Queue services restart. This belongs under P124 because raw migration completion is insufficient without proof that task state, saga state, FSM projections, outbox/session state, leases, and idempotency semantics survived correctly.

## Success Criteria

- Source SQLite and target Postgres row counts are compared for all migrated Queue tables.
- Semantic checks cover task state, saga state, FSM projections, session/outbox rows, worker lease rows, and idempotency completed/in-progress rows.
- Schema/version metadata is verified on the Postgres target.
- Any count mismatch or semantic warning is resolved or recorded as a blocker.
- A redacted verification report is saved under ledger artifacts.
