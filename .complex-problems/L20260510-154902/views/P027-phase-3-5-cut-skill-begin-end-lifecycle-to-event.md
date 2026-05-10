# P027: Phase 3.5: Cut skill begin/end lifecycle to events

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P027
Body: problems/P000/children/P004/children/P027/README.md
Ticket(s): T034

## Problem
Skill begin/end currently create child scope directories, update scope meta, and write `summary.md` as direct source-of-truth facts. The authoritative lifecycle facts must become `SkillScopeOpened` and `SkillScopeClosed` events while preserving LIFO failure behavior.

## Success Criteria
- `skill_begin` appends `SkillScopeOpened`.
- `skill_end` appends `SkillScopeClosed` with exact report text.
- LIFO mismatch continues to return structured failure and does not append a close event.
- Event payloads are sufficient for fold rendering and active stack replay.
- Tests verify event stream content and failure no-op behavior.

## Subproblems
- P038: Phase 3.5.1: Emit SkillScopeOpened on skill_begin success
- P039: Phase 3.5.2: Emit SkillScopeClosed on skill_end success
- P040: Phase 3.5.3: Verify skill lifecycle cutover boundaries

## Results
- R036

## Latest Check
C039

## Bodies
- Problem: problems/P000/children/P004/children/P027/README.md
- Ticket T034: problems/P000/children/P004/children/P027/tickets/T034.md
- Result R036: problems/P000/children/P004/children/P027/results/R036.md
- Check C039: problems/P000/children/P004/children/P027/checks/C039.md

## Follow-ups
- none
