# P136: Repair Final SQLite Classification Rows For Gateway And Cortex

Status: done
Parent: P024
Root: P000
Source Ticket: none (none)
Source Check: C151
Package: problems/P000/children/P024/children/P136
Body: problems/P000/children/P024/children/P136/README.md
Ticket(s): T136

## Problem
The remaining service Postgres cutovers are complete, but the central SQLite classification table still has stale active top-level rows for Gateway and Cortex. This creates operational ambiguity because the live SQLite files are gone and later addenda document Postgres cutovers, but the primary table still says those paths are active.

## Success Criteria
- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` top-level row for `/opt/novaic/data/gateway.db` marks it rollback-only/non-current or archived, names Postgres `novaic_gateway` as the current source of truth, and points to the Gateway rollback/cutover archive.
- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` top-level row for `/opt/novaic/data/cortex/operational.sqlite3` marks it rollback-only/non-current or archived, names Postgres `novaic_cortex` as the current source of truth, and points to the Cortex rollback/cutover archive.
- A fresh final classification audit shows no stale active service-owned SQLite rows among Queue, Entangled, Gateway, and Cortex.
- Local ledger artifacts include sanitized evidence of the updated rows and audit results.
- New local artifacts are scanned for credential patterns before being cited.

## Subproblems
- none

## Results
- R136

## Latest Check
C152

## Bodies
- Problem: problems/P000/children/P024/children/P136/README.md
- Ticket T136: problems/P000/children/P024/children/P136/tickets/T136.md
- Result R136: problems/P000/children/P024/children/P136/results/R136.md
- Check C152: problems/P000/children/P024/children/P136/checks/C152.md

## Follow-ups
- none
