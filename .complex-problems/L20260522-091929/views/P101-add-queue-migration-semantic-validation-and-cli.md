# P101: Add Queue Migration Semantic Validation And CLI

Status: done
Parent: P075
Root: P000
Source Ticket: T096 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P075/children/P101
Body: problems/P000/children/P024/children/P028/children/P075/children/P101/README.md
Ticket(s): T099

## Problem
The migration is only production-useful if it validates semantic invariants after copy and exposes a clear operator command. We need a CLI that runs planning, optional dry-run, execution, validation, and redacted report writing, plus tests that catch semantic drift before production restart.

## Success Criteria
- Provides a documented CLI entrypoint for SQLite path, Postgres DSN/DSN file, report path, dry-run mode, and non-empty target handling.
- Validates row counts for every active table after migration.
- Validates semantic aggregates: task/saga/session states, pending/dead-letter outbox counts, idempotency statuses, worker lease states, max event/outbox IDs, and config schema version.
- Writes a redacted JSON report suitable for ledger artifacts.
- Dry-run performs planning and validation preflight without writing target rows.
- Tests cover CLI argument handling, dry-run/report writing, semantic validation success, and semantic validation failure.

## Subproblems
- P102: Add Queue Migration Semantic Aggregate Validation
- P103: Add Queue Migration CLI And Report Writing

## Results
- R098

## Latest Check
C106

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P075/children/P101/README.md
- Ticket T099: problems/P000/children/P024/children/P028/children/P075/children/P101/tickets/T099.md
- Result R098: problems/P000/children/P024/children/P028/children/P075/children/P101/results/R098.md
- Check C106: problems/P000/children/P024/children/P028/children/P075/children/P101/checks/C106.md

## Follow-ups
- none
