# P019: Phase 2.2.2: Projection fold rendering and stale sibling suppression

Status: done
Parent: P015
Root: P000
Package: problems/P000/children/P003/children/P015/children/P019
Body: problems/P000/children/P003/children/P015/children/P019/README.md
Ticket(s): T014

## Problem
Implement rendering behavior for closed scopes and suppression of stale open siblings. This belongs under P015 because it is the event-sourced replacement for DFS folded summary rendering.

## Success Criteria
- Non-empty `SkillScopeClosed.report` renders `[Skill '<name>' completed]\n<report>` into the parent message stream.
- Blank structural closed scopes emit no empty summary and expose child fold messages.
- Nested folds render deterministically inside parents.
- When a new open sibling appears under the same parent, older still-open sibling output is suppressed and removed from active stack.
- Tests cover non-empty fold, blank structural close, nested fold, and stale open sibling suppression.

## Subproblems
- P020: Phase 2.2.2.1: Projection closed-scope fold rendering
- P021: Phase 2.2.2.2: Projection stale open sibling suppression

## Results
- R013

## Latest Check
C014

## Bodies
- Problem: problems/P000/children/P003/children/P015/children/P019/README.md
- Ticket T014: problems/P000/children/P003/children/P015/children/P019/tickets/T014.md
- Result R013: problems/P000/children/P003/children/P015/children/P019/results/R013.md
- Check C014: problems/P000/children/P003/children/P015/children/P019/checks/C014.md

## Follow-ups
- none
