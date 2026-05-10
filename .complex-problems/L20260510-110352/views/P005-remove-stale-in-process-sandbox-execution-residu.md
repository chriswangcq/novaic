# P005: Remove stale in-process sandbox execution residue

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T005

## Problem
After sandboxd is the active server path, stale old-path helpers and compatibility branches must be removed or explicitly scoped as test adapters. This prevents future agents from accidentally reconnecting the old logic.

## Success Criteria
- Searches for old sandbox execution modules/classes and Cortex command wrapping residue find no active production path.
- Any remaining direct runner is named/documented as a test/local adapter, not a fallback.
- Historical imports and deleted modules are cleaned from tests and docs touched by this change.
- Code size/residue changes are reviewed against the AI-era programming principle: no misleading half-deleted paths.

## Subproblems
- none

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T005: problems/P000/children/P005/tickets/T005.md
- Result R004: problems/P000/children/P005/results/R004.md
- Check C004: problems/P000/children/P005/checks/C004.md

## Follow-ups
- none
