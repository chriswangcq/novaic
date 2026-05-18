# P199: Projection production stale branch cleanup

Status: done
Parent: P187
Root: P000
Source Ticket: T188 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/README.md
Ticket(s): T195

## Problem
After inventory, stale production branches should be physically removed rather than carried as confusing fallback logic. Active or compatibility branches must remain only when justified by current call paths or persisted data.

## Success Criteria
- Remove production branches classified stale by the inventory.
- Keep active/compatibility branches only with a clear reason in the result.
- Do not introduce broad compatibility fallbacks or local-only fallbacks.
- Run focused production-side projection tests after edits.

## Subproblems
- P207: Prove stale production projection helper has no live callers
- P208: Delete stale projection helper and export residue
- P209: Audit retained production projection compatibility branches

## Results
- R197

## Latest Check
C211

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/README.md
- Ticket T195: problems/P000/children/P003/children/P127/children/P187/children/P199/tickets/T195.md
- Result R197: problems/P000/children/P003/children/P127/children/P187/children/P199/results/R197.md
- Check C211: problems/P000/children/P003/children/P127/children/P187/children/P199/checks/C211.md

## Follow-ups
- none
