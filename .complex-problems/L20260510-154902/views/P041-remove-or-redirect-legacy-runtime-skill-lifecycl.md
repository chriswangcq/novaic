# P041: Remove or redirect legacy runtime skill lifecycle bypass

Status: done
Parent: P040
Root: P000
Package: problems/P000/children/P004/children/P027/children/P040/children/P041
Body: problems/P000/children/P004/children/P027/children/P040/children/P041/README.md
Ticket(s): T038

## Problem
Older JWT endpoints `/v1/skill/begin` and `/v1/skill/end` call `Cortex.skill_begin/end`, and those runtime methods directly create/close scope filesystem state without emitting `SkillScopeOpened` or `SkillScopeClosed`. This bypass means lifecycle events are not yet the single write path.

## Success Criteria
- `/v1/skill/begin` and `/v1/skill/end` can no longer create or close skill scopes without `SkillScopeOpened/Closed` events.
- Either the legacy endpoints are deleted/disabled with explicit tests, or they are redirected through the event-wired context lifecycle path.
- `Cortex.skill_begin/end` direct filesystem lifecycle code is removed or made unreachable for runtime lifecycle writes.
- Focused tests prove the old endpoints cannot bypass lifecycle events.
- Full Cortex suite passes.

## Subproblems
- none

## Results
- R035

## Latest Check
C037

## Bodies
- Problem: problems/P000/children/P004/children/P027/children/P040/children/P041/README.md
- Ticket T038: problems/P000/children/P004/children/P027/children/P040/children/P041/tickets/T038.md
- Result R035: problems/P000/children/P004/children/P027/children/P040/children/P041/results/R035.md
- Check C037: problems/P000/children/P004/children/P027/children/P040/children/P041/checks/C037.md

## Follow-ups
- none
