# Build Entangled Migration Planner And Redacted Report Model

## Problem

The migration command needs a deterministic planning layer before any data is copied. It must inspect the SQLite source read-only, identify active tables and columns, decide which tables need `rowid AS entangled_rowid`, require explicit target-clean confirmation, and produce a report structure that never stores secrets. This belongs under `P049` because safe planning and secret-safe reporting are prerequisites for the offline migration command.

## Success Criteria

- A migration planner module exists with testable functions/classes for source inspection, target-clean safety checks, table copy planning, support-table classification, sequence-reset planning, and report construction.
- SQLite source inspection uses a read-only URI/path strategy and can be unit-tested against a temporary SQLite file.
- The planner identifies dynamic entity tables, `entangled_sync_versions`, `subagent_state_transitions`, and skipped tables with reasons.
- The planner marks tables requiring SQLite `rowid` copy into Postgres `entangled_rowid`.
- Target cleanup planning refuses destructive cleanup unless an explicit clean flag and target confirmation are present.
- Report construction redacts DSNs/passwords/tokens and records source counts, target counts placeholders, semantic checks placeholders, sequence reset plan, and skipped tables.
- Focused tests cover read-only inspection, rowid-copy planning, unsafe-clean refusal, skip reasons, and report redaction.
