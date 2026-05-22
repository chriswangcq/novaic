# P038: Implement Entangled Postgres adapter and runtime boundary

Status: done
Parent: P027
Root: P000
Source Ticket: T036 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P038
Body: problems/P000/children/P024/children/P027/children/P038/README.md
Ticket(s): T037

## Problem
Entangled currently relies on the SQLite `Database` implementation and `--db-path` runtime wiring. Add an explicit Postgres runtime boundary for Entangled so the rest of the service can use a Postgres-backed DB interface without scattered SQLite assumptions or a silent production fallback.

## Success Criteria
- Entangled has explicit config/runtime selection for Postgres using the existing `novaic_entangled` database.
- Postgres driver dependency and connection-pool adapter are added behind the existing database boundary.
- Adapter preserves dict-like rows, `execute`, `executemany`, `fetchone`, `fetchall`, `fetch_all`, `rowcount`, commit/rollback, transaction context, and `RETURNING` behavior where needed.
- Transaction locking maps existing global/resource lock semantics to Postgres-safe advisory or row locks.
- Production Postgres mode does not silently fall back to SQLite.
- Focused adapter/config tests and compile checks pass.

## Subproblems
- none

## Results
- R035

## Latest Check
C036

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P038/README.md
- Ticket T037: problems/P000/children/P024/children/P027/children/P038/tickets/T037.md
- Result R035: problems/P000/children/P024/children/P027/children/P038/results/R035.md
- Check C036: problems/P000/children/P024/children/P027/children/P038/checks/C036.md

## Follow-ups
- none
