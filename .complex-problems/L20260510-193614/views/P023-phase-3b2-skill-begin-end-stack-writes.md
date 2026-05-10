# P023: Phase 3B2 Skill Begin End Stack Writes

Status: done
Parent: P018
Root: P000
Package: problems/P000/children/P004/children/P018/children/P023
Body: problems/P000/children/P004/children/P018/children/P023/README.md
Ticket(s): T018

## Problem
Successful `skill_begin` and `skill_end` currently return file-walk stacks but do not update operational SQLite active-stack projection. Runtime reads cannot cut over safely until begin/end writes are authoritative.

## Success Criteria
- Successful `skill_begin` writes the pushed stack to operational SQLite after child scope creation/event append.
- Successful `skill_end` writes the popped stack to operational SQLite after child close/event append.
- Error branches do not mutate SQLite stack projection.
- Tests cover nested begin/end projection state and restart-like store reuse.

## Subproblems
- P026: Phase 3B2 Follow-up Nested And Restart Projection Verification

## Results
- R015

## Latest Check
C018

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P023/README.md
- Ticket T018: problems/P000/children/P004/children/P018/children/P023/tickets/T018.md
- Result R015: problems/P000/children/P004/children/P018/children/P023/results/R015.md
- Check C016: problems/P000/children/P004/children/P018/children/P023/checks/C016.md
- Check C018: problems/P000/children/P004/children/P018/children/P023/checks/C018.md

## Follow-ups
- P026: Phase 3B2 Follow-up Nested And Restart Projection Verification
