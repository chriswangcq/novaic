# P033: Phase 3C4 Skill End LIFO SQLite Cutover

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P004/children/P019/children/P033
Body: problems/P000/children/P004/children/P019/children/P033/README.md
Ticket(s): T029

## Problem
`skill_end` still validates stack-empty and mismatch cases by resolving active scope from file-walk state. It must validate current top scope from SQLite active-stack projection and preserve structured error semantics.

## Success Criteria
- `skill_end` empty-stack detection reads SQLite active-stack projection.
- `skill_end` mismatch detection compares requested id with SQLite top scope id.
- Successful `skill_end` uses SQLite top frame path as the child path to close.
- Existing error fields (`error_code`, `requested_scope_id`, `actual_stack_top`, `stack`, `stack_depth`) remain compatible.
- Tests cover stack-empty, wrong-scope close, and successful close.

## Subproblems
- none

## Results
- R026

## Latest Check
C028

## Bodies
- Problem: problems/P000/children/P004/children/P019/children/P033/README.md
- Ticket T029: problems/P000/children/P004/children/P019/children/P033/tickets/T029.md
- Result R026: problems/P000/children/P004/children/P019/children/P033/results/R026.md
- Check C028: problems/P000/children/P004/children/P019/children/P033/checks/C028.md

## Follow-ups
- none
