# P020: Phase 3D Quarantine File-Walk Stack Authority

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P020
Body: problems/P000/children/P004/children/P020/README.md
Ticket(s): T031

## Problem
After SQLite read cutover, `_collect_active_stack` and projection-file walking must not remain on runtime authority paths. If kept, they need a repair/debug name and explicit isolation.

## Success Criteria
- Runtime API paths no longer call file-walk active stack collection for authority decisions.
- Any remaining file-walk stack code is renamed or documented as repair/debug only.
- Tests or grep guards catch reintroduction of file-walk authority into `skill_begin`, `skill_end`, and default `context_status`.
- Old tests that assert file-walk authority are rewritten or deleted.

## Subproblems
- P035: Archive Finalize Stack Snapshot Cutover
- P036: Skill Begin Error And Projection Cleanup
- P037: Skill End Exception Diagnostic Cleanup
- P038: Active Path Routing Endpoint Cutover
- P039: File-Walk Helper Deletion And Guard Rails

## Results
- R034

## Latest Check
C036

## Bodies
- Problem: problems/P000/children/P004/children/P020/README.md
- Ticket T031: problems/P000/children/P004/children/P020/tickets/T031.md
- Result R034: problems/P000/children/P004/children/P020/results/R034.md
- Check C036: problems/P000/children/P004/children/P020/checks/C036.md

## Follow-ups
- none
