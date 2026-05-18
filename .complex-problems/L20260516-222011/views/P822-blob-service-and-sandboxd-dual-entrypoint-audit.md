# P822: Blob service and Sandboxd dual entrypoint audit

Status: done
Parent: P698
Root: P000
Source Ticket: T814 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P822
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P822/README.md
Ticket(s): T817

## Problem
Both `novaic-blob-service` and `novaic-sandbox-service` have two entrypoint files each: a `main_*.py` wrapper at the repo root level and an internal `*/main.py`. Need to verify the wrapper pattern is intentional (thin launcher delegating to internal app) rather than a stale duplicate.

## Success Criteria
- Each dual-entrypoint pair is classified: wrapper pattern (keep both) or duplicate (remove one).
- If wrapper pattern, the relationship is clear (wrapper imports internal).
- No stale or divergent launch logic between the two files.

## Subproblems
- none

## Results
- R811

## Latest Check
C860

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P822/README.md
- Ticket T817: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P822/tickets/T817.md
- Result R811: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P822/results/R811.md
- Check C860: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P822/checks/C860.md

## Follow-ups
- none
