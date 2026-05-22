# Implement Entangled Offline SQLite-To-Postgres Migration Command

## Problem Definition

Entangled needs a safe offline migration command before staging or production cutover can be trusted. The command must read the SQLite source without mutating it, prepare a clean Postgres target, copy dynamic entity data and support tables, preserve stream ordering by carrying SQLite `rowid` into `entangled_rowid`, reset identities, and emit a report that is useful but secret-safe.

## Proposed Solution

1. Add a migration module under `entangled/sql/` or `entangled/app/` with small testable functions for source inspection, target cleanup, schema creation, table copy planning, row conversion, sequence reset, and report generation.
2. Add a CLI entry point under `Entangled/packages/server-python/scripts/` or `[project.scripts]` that wraps the module with explicit flags:
   - SQLite source path.
   - Postgres DSN or DSN file.
   - `--clean-target` plus a target confirmation string before dropping/truncating target tables.
   - report output path.
   - optional dry-run/planning mode where useful.
3. Open SQLite via read-only URI mode and fail if the source file is missing, mutable-only, or still has unexpected write holders during final-use mode.
4. Use Entangled schema registration/DDL helpers for dynamic entities and support-table helpers for `entangled_sync_versions` and `subagent_state_transitions`.
5. Copy dynamic table rows with explicit column lists; when a Postgres table has `entangled_rowid`, include SQLite `rowid AS entangled_rowid`.
6. Migrate support tables exactly, then reset generated identities above observed maximum IDs.
7. Produce a structured JSON or Markdown report with redacted connection info, source/target counts, sequence reset evidence, semantic checks, and skipped tables with reasons.
8. Add unit tests around planner/report behavior using fake DB adapters and temporary SQLite fixtures; leave real staging execution to `P050`.

## Acceptance Criteria

- The migration command/module exists in the Entangled server-python package and is discoverable by tests or CLI.
- SQLite is opened read-only for source inspection/copy.
- Destructive target cleanup requires explicit `--clean-target`-style opt-in and target confirmation.
- Dynamic schema creation uses Entangled DDL/schema helpers rather than unrelated handwritten create-table SQL.
- Dynamic table copy preserves `entangled_rowid` from SQLite `rowid` when the Postgres table has that column.
- `entangled_sync_versions` and `subagent_state_transitions` copy paths are implemented.
- Identity reset SQL is generated for migrated identity-backed tables, including `subagent_state_transitions`.
- Report output redacts DSNs/passwords/tokens and records counts/checks/skips.
- Focused tests cover read-only source handling, unsafe-clean refusal, rowid copy planning, support-table copy planning, identity reset, and redaction.

## Verification Plan

Run focused migration unit tests, py_compile for the new migration module/CLI, and the full Entangled server-python pytest suite. Inspect the generated test report to ensure it has no secret-like DSN material and includes source/target count/check sections.

## Risks

- A too-large first migration command could become hard to test; keep planner/copy/report units small.
- Fully generic schema discovery may miss application-owned active tables; use the existing Entangled schema inventory and explicit support-table handling.
- Identity reset logic differs between dynamic entity IDs, `entangled_rowid`, and transition IDs; tests need to pin each case.
- DSN file support can accidentally leak content in exception messages or report fields.

## Assumptions

- Real Postgres execution is deferred to `P050`; this ticket can use fakes and fixtures for deterministic tests.
- `P039` has already added the needed Postgres DDL/entity-store/support-table helpers.
- The command may support both JSON and Markdown reports, but only one structured format is required.
