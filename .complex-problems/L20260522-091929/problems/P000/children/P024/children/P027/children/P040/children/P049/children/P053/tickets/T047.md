# Implement Entangled Migration Planner And Report Model

## Problem Definition

The offline Entangled migration command needs a deterministic planning layer before data copy is implemented. The planner must inspect a SQLite source in read-only mode, classify tables, compute copy/sequence plans, enforce destructive-target safety, and build a structured redacted report model.

## Proposed Solution

1. Add a new testable module such as `entangled/sql/migration.py`.
2. Define small data classes for table inventory, table copy plan, sequence reset plan, skipped table reason, migration checks, and migration report.
3. Implement SQLite read-only inspection using a URI connection mode that cannot create or mutate the source file.
4. Inspect SQLite tables and columns via `sqlite_master`/`PRAGMA table_info`, collect counts, and classify:
   - dynamic entity table candidates,
   - `entangled_sync_versions`,
   - `subagent_state_transitions`,
   - SQLite internal/shadow/ignored tables.
5. Mark dynamic tables for `rowid` copy when their Postgres target is expected to have `entangled_rowid`.
6. Implement target cleanup safety logic that requires both an explicit clean flag and a target confirmation string.
7. Implement report rendering to JSON-compatible dictionaries, with DSN/password/token redaction and placeholders for later target counts and semantic checks.
8. Add focused tests in `tests/test_migration_planner.py` using temporary SQLite fixtures and pure functions.

## Acceptance Criteria

- `entangled/sql/migration.py` or equivalent exists and is importable.
- Planner opens SQLite read-only and returns table inventory with columns and counts.
- Planner identifies support tables and dynamic table candidates, and records skipped table reasons.
- Planner marks `copy_rowid_to_entangled_rowid` for dynamic copy plans that need stream ordering preservation.
- Target cleanup guard refuses unsafe destructive cleanup and accepts explicit confirmation.
- Report model includes source counts, target count placeholders, sequence reset plan, semantic check placeholders, skipped tables, and redacted connection labels.
- Tests cover read-only inspection, classification, rowid-copy planning, cleanup refusal/acceptance, and redaction.

## Verification Plan

Run `python -m pytest tests/test_migration_planner.py`, `python -m py_compile entangled/sql/migration.py`, and the full Entangled server-python test suite after the module is added.

## Risks

- Planner may classify non-Entangled SQLite tables as active dynamic tables; tests should include internal/skipped tables.
- SQLite URI read-only handling is easy to accidentally bypass; tests should fail on missing files instead of creating them.
- Report redaction must avoid storing secret-bearing input fields, not merely mask them at display time.

## Assumptions

- Copy execution and CLI integration are separate child problems.
- The planner can use table/column heuristics now and be tightened by staging validation if live inventory exposes an edge case.
