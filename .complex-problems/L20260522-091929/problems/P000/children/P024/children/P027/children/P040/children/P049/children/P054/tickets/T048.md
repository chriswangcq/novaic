# Implement Entangled Migration Copy Executor And Identity Reset

## Problem Definition

The migration planner can inspect SQLite and produce copy/sequence plans, but Entangled still needs the execution layer that reads planned SQLite rows, writes them to the Postgres target through explicit column lists, migrates support tables, resets generated identities, and returns target counts/checks to the report model.

## Proposed Solution

1. Extend `entangled/sql/migration.py` with copy-executor helpers that accept a `MigrationPlan`, SQLite source path, and target DB adapter.
2. Add SQL builders for explicit target inserts and target count queries, keeping identifier quoting centralized.
3. Read source rows using planned `source_columns`; for dynamic tables with `rowid` copy, select SQLite `rowid` and insert it as `entangled_rowid`.
4. Copy `entangled_sync_versions` and `subagent_state_transitions` as ordinary planned tables while preserving their semantic counts/max IDs.
5. Add sequence reset SQL generation/execution for planned identity-backed columns.
6. Return or update a `MigrationReport` with target counts, sync-version equality status, transition count/max-ID status, rowid-copy status, and sequence reset evidence.
7. Add focused tests using temporary SQLite fixtures and fake target adapters that capture SQL/params.

## Acceptance Criteria

- Copy executor can copy planned tables using explicit source/target columns.
- Dynamic table copy includes SQLite `rowid` as `entangled_rowid` when planned.
- Support tables copy through the same explicit planning path and expose checks for sync-version and transition preservation.
- Sequence reset SQL is generated/executed for dynamic `entangled_rowid`, integer IDs, and transition IDs.
- Target counts and semantic check statuses are reflected in the report model.
- Tests cover insert SQL generation, rowid copy values, support-table copies, sequence reset calls, and target count reporting.

## Verification Plan

Run focused migration executor tests, `python -m py_compile entangled/sql/migration.py`, and the full Entangled server-python pytest suite.

## Risks

- Fake target tests can prove SQL shape but not all Postgres type behavior; staging execution remains assigned to `P050`.
- Identifier quoting must be shared between source and target paths to avoid table/column-name edge cases.
- Sequence reset SQL must be safe to emit without leaking target connection data.

## Assumptions

- `P053` planner/report structures are available.
- The executor can operate against the current `PostgresDatabase` adapter surface (`execute`, `executemany`, `fetchone`, `transaction`) or a fake with the same methods.
- Real target cleanup and CLI wiring are handled by the sibling CLI child.
