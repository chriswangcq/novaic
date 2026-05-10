# P050: Phase 5B2 Archive Tree Projection Quarantine

Status: done
Parent: P046
Root: P000
Package: problems/P000/children/P006/children/P046/children/P050
Body: problems/P000/children/P006/children/P046/children/P050/README.md
Ticket(s): T048

## Problem
After live lookup and uniqueness move to SQLite, `_walk_scope_tree` should not remain a generic authority-sounding helper. If it is still needed to build `/ro/scopes/_index.jsonl`, it must be renamed and confined to archive/debug projection behavior.

## Success Criteria
- `_walk_scope_tree` is removed or renamed to an archive/debug projection-specific helper.
- No API live control path calls the archive projection helper.
- `/ro/scopes/_index.jsonl` generation, if retained, is clearly projection/debug-only.
- Tests prove root archive still writes the expected historical projection without making it runtime authority.

## Subproblems
- none

## Results
- R045

## Latest Check
C048

## Bodies
- Problem: problems/P000/children/P006/children/P046/children/P050/README.md
- Ticket T048: problems/P000/children/P006/children/P046/children/P050/tickets/T048.md
- Result R045: problems/P000/children/P006/children/P046/children/P050/results/R045.md
- Check C048: problems/P000/children/P006/children/P046/children/P050/checks/C048.md

## Follow-ups
- none
