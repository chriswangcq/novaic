# Add Queue Migration Semantic Validation And CLI

## Problem

The migration is only production-useful if it validates semantic invariants after copy and exposes a clear operator command. We need a CLI that runs planning, optional dry-run, execution, validation, and redacted report writing, plus tests that catch semantic drift before production restart.

## Success Criteria

- Provides a documented CLI entrypoint for SQLite path, Postgres DSN/DSN file, report path, dry-run mode, and non-empty target handling.
- Validates row counts for every active table after migration.
- Validates semantic aggregates: task/saga/session states, pending/dead-letter outbox counts, idempotency statuses, worker lease states, max event/outbox IDs, and config schema version.
- Writes a redacted JSON report suitable for ledger artifacts.
- Dry-run performs planning and validation preflight without writing target rows.
- Tests cover CLI argument handling, dry-run/report writing, semantic validation success, and semantic validation failure.
