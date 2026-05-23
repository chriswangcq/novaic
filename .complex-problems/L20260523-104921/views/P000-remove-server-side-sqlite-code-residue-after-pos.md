# P000: Remove server-side SQLite code residue after Postgres cutover

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Postgres is now the intended server-side persistence boundary, but the repository still contains active-looking SQLite runtime branches, startup flags, migration CLIs, admin scripts, comments, and tests. This residue makes future humans and AI likely to reintroduce queue.db, gateway.db, device.db, entangled.db, or Cortex operational.sqlite3 paths after the cutover.

Scope is server-side production and developer runtime code in this workspace. Client-local cache SQLite is out of scope unless it crosses into server persistence. Archived historical docs are lower priority unless they are referenced by current runbooks or scripts.

## Success Criteria
- Server startup paths no longer pass or document SQLite database files for migrated services.
- Queue, Gateway, Device, Entangled, and Cortex current runtime entry points no longer expose SQLite as the normal or fallback server backend after the Postgres cutover.
- Migration/admin scripts that only exist to operate old SQLite server databases are removed or moved out of executable current paths.
- Current tests and residue guards reflect the Postgres-only server shape instead of preserving SQLite compatibility as a goal.
- Any remaining SQLite references are either client-local cache, historical archive, or explicitly justified non-server test substrate with a follow-up if not removable in this pass.

## Subproblems
- P001: Remove SQLite from current startup and deployment entry points
- P002: Remove Queue Service SQLite runtime fallback
- P003: Remove Gateway and Device server SQLite utilities
- P004: Remove Cortex and Entangled server SQLite fallback paths
- P005: Update residue guards, tests, and ledger evidence

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R005: problems/P000/results/R005.md
- Check C005: problems/P000/checks/C005.md

## Follow-ups
- none
