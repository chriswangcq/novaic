# P020: Phase 2.2.2.1: Projection closed-scope fold rendering

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P003/children/P015/children/P019/children/P020
Body: problems/P000/children/P003/children/P015/children/P019/children/P020/README.md
Ticket(s): T015

## Problem
Implement fold rendering for ordinary closed scopes and blank structural scopes. This belongs under P019 because fold rendering should be solved before stale sibling suppression adds extra stack behavior.

## Success Criteria
- Closing a skill with a non-empty report emits `[Skill '<name>' completed]\n<report>` into the parent message stream.
- Closing a skill with a blank report emits no empty summary.
- Blank structural parent close exposes child fold messages.
- Nested folds render deterministically.
- Tests cover non-empty fold, blank close, and nested structural fold.

## Subproblems
- none

## Results
- R011

## Latest Check
C012

## Bodies
- Problem: problems/P000/children/P003/children/P015/children/P019/children/P020/README.md
- Ticket T015: problems/P000/children/P003/children/P015/children/P019/children/P020/tickets/T015.md
- Result R011: problems/P000/children/P003/children/P015/children/P019/children/P020/results/R011.md
- Check C012: problems/P000/children/P003/children/P015/children/P019/children/P020/checks/C012.md

## Follow-ups
- none
