# P090: Runtime queue test residue scan

Status: done
Parent: P067
Root: P000
Source Ticket: T082 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P090
Body: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P090/README.md
Ticket(s): T083

## Problem
`novaic-agent-runtime/tests` may contain stale skip/TODO/FIXME/compat/fallback/legacy fixtures that keep deprecated queue/FSM/session behavior acceptable.

## Success Criteria
- Scan runtime tests for skip/xfail/TODO/FIXME/compat/fallback/legacy/direct-tool/base64 markers.
- Classify hits as intentional guard, harmless fixture text, or stale acceptance.
- Clean tiny stale test residue when safe.
- Run focused runtime tests or explicit no-code-change verification.

## Subproblems
- none

## Results
- R078

## Latest Check
C092

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P090/README.md
- Ticket T083: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P090/tickets/T083.md
- Result R078: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P090/results/R078.md
- Check C092: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P090/checks/C092.md

## Follow-ups
- none
