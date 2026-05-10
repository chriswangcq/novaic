# P015: Phase 2.2: Projection scope stack and fold semantics

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P015
Body: problems/P000/children/P003/children/P015/README.md
Ticket(s): T012

## Problem
Implement projection of skill scope lifecycle events into active stack and folded context messages. This belongs under Phase 2 because skill folding is the core behavior currently embedded in DFS `ContextEngine` logic.

## Success Criteria
- Projector handles `SkillScopeOpened` and `SkillScopeClosed` with LIFO validation.
- Non-empty closed skills render `[Skill '<name>' completed]\n<report>`.
- Blank structural closed scopes do not emit empty summaries.
- Nested skill scopes project deterministically.
- Newest open sibling remains active and stale open siblings are suppressed.
- Tests cover simple fold, blank structural close, nested fold, LIFO violation, and stale open sibling suppression.

## Subproblems
- P018: Phase 2.2.1: Projection scope stack and LIFO validation
- P019: Phase 2.2.2: Projection fold rendering and stale sibling suppression

## Results
- R014

## Latest Check
C015

## Bodies
- Problem: problems/P000/children/P003/children/P015/README.md
- Ticket T012: problems/P000/children/P003/children/P015/tickets/T012.md
- Result R014: problems/P000/children/P003/children/P015/results/R014.md
- Check C015: problems/P000/children/P003/children/P015/checks/C015.md

## Follow-ups
- none
