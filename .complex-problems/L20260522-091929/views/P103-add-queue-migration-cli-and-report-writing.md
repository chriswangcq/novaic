# P103: Add Queue Migration CLI And Report Writing

Status: done
Parent: P101
Root: P000
Source Ticket: T099 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P103
Body: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P103/README.md
Ticket(s): T101

## Problem
Operators need a safe command to run Queue migration planning, dry-run preflight, copy execution, semantic validation, and redacted report writing. The CLI must expose source/target/report options and return non-zero for blocked/error results without leaking DSNs or secret file paths.

## Success Criteria
- Provides a module entrypoint for Queue migration CLI.
- Supports `--sqlite-path`, `--postgres-dsn`, `--postgres-dsn-file`, `--report-path`, `--dry-run`, and `--allow-non-empty-target`.
- Dry-run runs planning/report writing without copy execution.
- Execution path initializes Postgres schema, copies data, validates semantics, writes the final report, and returns non-zero on blocked/error status.
- Report JSON is redacted and suitable for ledger artifacts.
- Tests cover argument handling, dry-run report writing, execution report writing, and error exit behavior without a live Postgres server.

## Subproblems
- none

## Results
- R097

## Latest Check
C105

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P103/README.md
- Ticket T101: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P103/tickets/T101.md
- Result R097: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P103/results/R097.md
- Check C105: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P103/checks/C105.md

## Follow-ups
- none
