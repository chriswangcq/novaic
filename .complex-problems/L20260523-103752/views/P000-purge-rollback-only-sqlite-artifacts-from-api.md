# P000: Purge rollback-only SQLite artifacts from api

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The previous Postgres unification work intentionally retained rollback-only SQLite files and snapshots. The user now wants all remaining SQLite artifacts removed, including rollback files, so no SQLite database files remain under the production NovAIC filesystem except non-state tooling caches if explicitly excluded.

## Success Criteria
- Inventory all SQLite database files and sidecars under `/opt/novaic` on `api.gradievo.com` before deletion.
- Confirm no live production process holds any targeted SQLite file before deletion.
- Delete remaining rollback-only SQLite database files and sidecars, including active-looking app data files and rollback archives.
- Preserve an audit report with deleted paths, sizes, hashes, and any skipped non-targets.
- Update `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` so deleted rollback artifacts are not described as retained files.
- Verify no targeted SQLite database files or sidecars remain under `/opt/novaic` after deletion.
- Verify live services still report healthy/readiness where lightweight checks exist.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
