# P036: Skill Begin Error And Projection Cleanup

Status: done
Parent: P020
Root: P000
Package: problems/P000/children/P004/children/P020/children/P036
Body: problems/P000/children/P004/children/P020/children/P036/README.md
Ticket(s): T033

## Problem
`context_skill_begin` still calls `_collect_active_stack(...)` in validation/duplicate/error responses and after successful child creation to seed the new active-stack projection. This means error surfaces and post-create writes can still reintroduce file-walk-derived stack authority.

This belongs under Phase 3D because `skill_begin` is a core runtime control path and its success path was only partially cut over in Phase 3C.

## Success Criteria
- Missing/invalid/duplicate/depth-limit `skill_begin` responses use SQLite projection-derived stack frames.
- Successful `skill_begin` computes the new stack by prepending the newly-created child frame to the projection frames already read for parent selection.
- `skill_begin` does not call `_collect_active_stack(...)` in success, validation, duplicate, or exception branches.
- Tests cover missing ID, invalid ID, duplicate ID, depth limit, and successful nested begin without file-walk stack collection.

## Subproblems
- none

## Results
- R030

## Latest Check
C032

## Bodies
- Problem: problems/P000/children/P004/children/P020/children/P036/README.md
- Ticket T033: problems/P000/children/P004/children/P020/children/P036/tickets/T033.md
- Result R030: problems/P000/children/P004/children/P020/children/P036/results/R030.md
- Check C032: problems/P000/children/P004/children/P020/children/P036/checks/C032.md

## Follow-ups
- none
