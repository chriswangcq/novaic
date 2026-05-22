# Add Entangled Migration CLI Entry Point And Command Tests

## Problem Definition

The Entangled migration planner and executor exist as importable helpers, but operators still need a safe command-line entry point with clear arguments, DSN-file support, dry-run/report output, explicit destructive-target confirmation, and command-level tests proving secrets are not printed or persisted.

## Proposed Solution

1. Add a CLI module such as `entangled/app/migrate_postgres.py` or `entangled/sql/migration_cli.py` and expose it through `[project.scripts]`.
2. Support arguments for SQLite source path, Postgres DSN or DSN file, report output path, `--clean-target`, target confirmation, and `--dry-run`.
3. In dry-run mode, run planner/report generation without connecting to Postgres.
4. In execution mode, build `PostgresDatabase` from DSN/DSN file and run `execute_migration_plan`.
5. Write the report as JSON to the requested output path and ensure it contains only redacted connection labels.
6. Keep failure messages secret-safe by avoiding raw DSN or DSN-file contents in exceptions and stdout/stderr.
7. Add command-level tests using temporary SQLite fixtures, dry-run mode, and monkeypatched/fake execution for non-dry-run paths.

## Acceptance Criteria

- A CLI entry point exists in the package and is listed in `[project.scripts]` or is otherwise directly runnable by `python -m`.
- CLI validates mutually exclusive DSN/DSN-file inputs and requires some target label for report context.
- CLI supports `--dry-run` that produces a redacted planning report without creating a Postgres connection.
- CLI supports non-dry-run execution through the migration executor and Postgres adapter boundary.
- Missing clean-target confirmation fails safely without printing DSN contents.
- DSN file contents are not written into the report or failure output.
- Command tests cover dry-run report writing, unsafe cleanup failure, DSN-file redaction, and execution path wiring with a fake target.
- `python -m py_compile` passes for new modules/scripts and full Entangled pytest passes.

## Verification Plan

Run focused CLI tests, py_compile for the migration module/CLI, and the full Entangled server-python pytest suite. Inspect generated test reports/assertions for absence of raw DSN passwords or tokens.

## Risks

- Instantiating `PostgresDatabase` in unit tests could accidentally require psycopg; tests should monkeypatch execution path or use dry-run for no-network coverage.
- CLI exception handling can accidentally echo raw DSN values if errors include argument values.
- A script entry point can drift from direct module invocation unless tests call the same `main(argv)` function.

## Assumptions

- Real staging execution remains under `P050`; this ticket proves command wiring and safety behavior locally.
- JSON report output is sufficient for command-level artifacts.
