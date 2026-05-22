# P073: Implement Queue Postgres Schema And Database Boundary

Status: done
Parent: P028
Root: P000
Source Ticket: T072 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P073
Body: problems/P000/children/P024/children/P028/children/P073/README.md
Ticket(s): T073

## Problem
Queue currently uses a SQLite-specific `common.db.Database` boundary and schema under `queue_service/db/schema.py`. Before repositories can be ported, Queue needs an explicit Postgres database boundary and schema that preserve table ownership, primary/unique keys, JSONB/timestamptz choices, indexes, transaction behavior, and startup configuration without a production SQLite fallback.

## Success Criteria
- A Queue Postgres schema exists for all active task, saga, session, worker lease, outbox, config, and idempotency tables.
- JSON columns use the agreed JSONB behavior and timestamp columns use the agreed timestamptz behavior.
- Required primary keys, unique idempotency constraints, partial indexes, candidate indexes, and JSON expression indexes are represented.
- Queue runtime can be configured explicitly for `sqlite` or `postgres` during development/cutover, with production intended to use Postgres.
- Unit tests verify schema generation/initialization and database-boundary transaction behavior without touching production.

## Subproblems
- P078: Add Queue Postgres JSON Expression Indexes

## Results
- R071

## Latest Check
C077

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P073/README.md
- Ticket T073: problems/P000/children/P024/children/P028/children/P073/tickets/T073.md
- Result R071: problems/P000/children/P024/children/P028/children/P073/results/R071.md
- Check C075: problems/P000/children/P024/children/P028/children/P073/checks/C075.md
- Check C077: problems/P000/children/P024/children/P028/children/P073/checks/C077.md

## Follow-ups
- P078: Add Queue Postgres JSON Expression Indexes
