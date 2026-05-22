# P002: Classify SQLite state owners and stale residue

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Current SQLite files include both active state and likely residue. Before migration or cleanup, each file and major code path must be classified with evidence so that cleanup does not delete current state and future agents do not follow stale paths.

## Success Criteria
- Every SQLite file under `/opt/novaic/data` and `/opt/novaic/llm-factory/data` is classified as active, projection/cache, migrate candidate, archive/delete residue, or defer.
- Evidence includes size, mtime, tables, row counts, runtime process owner, startup path, and code references.
- `business.db` and `device.db` receive explicit disposition decisions.
- Any retained residue is labeled or documented so it no longer appears to be a current state owner.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
