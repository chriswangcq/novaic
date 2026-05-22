# Implement Entangled Migration Target Preparation And Clean Execution

## Problem Definition

The current offline migration command can inspect, copy, reset identities, and report, but it assumes the Postgres target schema already exists. Add a target preparation phase that can clean confirmed planned tables and create/ensure dynamic/support table schemas before copy, all inside the migration transaction and without leaking secrets.

## Proposed Solution

1. Extend `entangled/sql/migration.py` with target preparation helpers:
   - dynamic table schema generation from `TableInventory` using `FieldDef` and `SqlEntityDef` Postgres DDL helpers,
   - support-table schema creation using `sync_versions_create_table_sql` and `subagent_transitions_create_table_sql`,
   - confirmed clean-target deletion/truncation for only planned tables.
2. Add preparation evidence to `MigrationReport` such as prepared tables, cleaned tables, and schema SQL count without storing connection details.
3. Call target preparation from `execute_migration_plan` before copying rows.
4. Ensure CLI non-dry-run uses the same execution path and dry-run remains plan/report-only.
5. Add focused tests with fake target adapters for dynamic/support schema SQL, cleanup refusal/execution, transaction ordering, report evidence, and no secret leakage.

## Acceptance Criteria

- Planned dynamic tables can be created or ensured using `SqlEntityDef.create_table_sql(dialect="postgres")` and index helpers derived from SQLite inventory.
- `entangled_sync_versions` and `subagent_state_transitions` schema preparation uses existing support-table DDL helpers.
- Clean-target execution only runs when `MigrationPlan.clean_target_allowed` is true and only touches planned target tables/support tables.
- Target preparation runs before copy inside `execute_migration_plan`.
- Migration report output includes prepared/cleaned table evidence.
- CLI non-dry-run path benefits from target preparation without extra operator steps.
- Tests cover dynamic/support DDL, clean-target refusal/execution, report evidence, and full migration ordering.
- py_compile and full Entangled tests pass.

## Verification Plan

Run focused migration planner/executor/CLI tests, py_compile for migration modules, and full Entangled pytest. Inspect test-generated reports for target preparation evidence and absence of DSN/password/token values.

## Risks

- Inferring Postgres DDL from SQLite inventory can be lossy; this is acceptable for staging migration tooling but should be validated by `P050` against a real target.
- Deleting/truncating target tables can be destructive if the plan is wrong; preparation must only run after the existing confirmation gate.
- Foreign keys remain intentionally unenforced for first cutover, matching the earlier FK-off policy.

## Assumptions

- Production cutover will still run a fresh preflight/staging validation before touching production data.
- The target tables are planned from the SQLite source inventory in this follow-up, not from live app schema registration requests.
