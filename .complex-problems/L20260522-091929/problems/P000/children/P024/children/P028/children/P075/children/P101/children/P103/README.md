# Add Queue Migration CLI And Report Writing

## Problem

Operators need a safe command to run Queue migration planning, dry-run preflight, copy execution, semantic validation, and redacted report writing. The CLI must expose source/target/report options and return non-zero for blocked/error results without leaking DSNs or secret file paths.

## Success Criteria

- Provides a module entrypoint for Queue migration CLI.
- Supports `--sqlite-path`, `--postgres-dsn`, `--postgres-dsn-file`, `--report-path`, `--dry-run`, and `--allow-non-empty-target`.
- Dry-run runs planning/report writing without copy execution.
- Execution path initializes Postgres schema, copies data, validates semantics, writes the final report, and returns non-zero on blocked/error status.
- Report JSON is redacted and suitable for ledger artifacts.
- Tests cover argument handling, dry-run report writing, execution report writing, and error exit behavior without a live Postgres server.
