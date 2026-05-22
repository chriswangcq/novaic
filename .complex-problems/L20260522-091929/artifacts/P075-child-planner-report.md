# Build Queue Migration Planner And Redacted Report Model

## Problem

Queue SQLite to Postgres migration needs a deterministic plan before any copy execution: the active table inventory, source/target row count inspection, clean-target preflight, redacted connection metadata, and a report shape suitable for production ledger artifacts. Without this boundary, later copy code will mix operational safety checks with data movement and become hard to verify.

## Success Criteria

- Defines the active migration table plan from `QUEUE_POSTGRES_TABLES` plus `config` in dependency-safe order.
- Can inspect a SQLite source and Postgres target abstraction for per-table row counts without copying data.
- Refuses or reports non-empty target tables by default.
- Produces a structured migration report model with status, table counts, semantic aggregate placeholders, errors, and timings.
- Redacts inline Postgres DSNs and DSN file paths in report output.
- Tests cover planning, empty/non-empty target detection, and report redaction without requiring a live Postgres instance.
