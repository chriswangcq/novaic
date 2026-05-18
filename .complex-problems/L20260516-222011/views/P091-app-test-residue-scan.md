# P091: App test residue scan

Status: done
Parent: P067
Root: P000
Source Ticket: T082 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P091
Body: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P091/README.md
Ticket(s): T084

## Problem
`novaic-app/src` tests may contain stale skip/TODO/FIXME/compat/fallback/legacy/base64 fixtures that preserve old frontend behavior.

## Success Criteria
- Scan App tests for skip/xfail/TODO/FIXME/compat/fallback/legacy/base64/direct-tool markers.
- Classify hits as intentional guard, harmless fixture text, current product vocabulary, or stale residue.
- Clean tiny stale test residue when safe.
- Run focused App tests or explicit no-code-change verification.

## Subproblems
- none

## Results
- R079

## Latest Check
C093

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P091/README.md
- Ticket T084: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P091/tickets/T084.md
- Result R079: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P091/results/R079.md
- Check C093: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P091/checks/C093.md

## Follow-ups
- none
