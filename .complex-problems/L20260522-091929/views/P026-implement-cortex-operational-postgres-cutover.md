# P026: Implement Cortex Operational Postgres Cutover

Status: done
Parent: P024
Root: P000
Source Ticket: T024 (split)
Source Check: none
Package: problems/P000/children/P024/children/P026
Body: problems/P000/children/P024/children/P026/README.md
Ticket(s): T030

## Problem
Cortex still owns active durable operational state in `/opt/novaic/data/cortex/operational.sqlite3`. It should be migrated to the existing `novaic_cortex` Postgres database while preserving event, projection, active-stack, and payload-manifest behavior.

## Success Criteria
- Cortex has a Postgres-backed production operational store.
- All five operational tables are migrated: `cortex_operational_meta`, `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
- Idempotency keys, active-stack semantics, projection reads, and payload manifest behavior are preserved.
- Existing Cortex SQLite state is backed up and migrated with row-count and semantic checks.
- Cortex runtime config is switched to Postgres and health/readiness/API smoke checks pass.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.

## Subproblems
- P033: Implement Cortex Postgres Operational Store
- P034: Cut Over Cortex Production Operational Store to Postgres

## Results
- R034

## Latest Check
C035

## Bodies
- Problem: problems/P000/children/P024/children/P026/README.md
- Ticket T030: problems/P000/children/P024/children/P026/tickets/T030.md
- Result R034: problems/P000/children/P024/children/P026/results/R034.md
- Check C035: problems/P000/children/P024/children/P026/checks/C035.md

## Follow-ups
- none
