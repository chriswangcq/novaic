# P039: Phase 3.5.2: Emit SkillScopeClosed on skill_end success

Status: done
Parent: P027
Root: P000
Package: problems/P000/children/P004/children/P027/children/P039
Body: problems/P000/children/P004/children/P027/children/P039/README.md
Ticket(s): T036

## Problem
Successful `/v1/context/skill_end` writes `summary.md` and closes the child scope as filesystem truth, but does not append `SkillScopeClosed`. Failure paths must remain event-silent.

## Success Criteria
- Successful `context_skill_end` appends `SkillScopeClosed` with exact report text.
- LIFO mismatch, missing id, and empty stack failure responses append no close event.
- Existing structured failure payloads remain compatible.
- Focused API tests inspect event stream content and no-op failure behavior.

## Subproblems
- none

## Results
- R033

## Latest Check
C035

## Bodies
- Problem: problems/P000/children/P004/children/P027/children/P039/README.md
- Ticket T036: problems/P000/children/P004/children/P027/children/P039/tickets/T036.md
- Result R033: problems/P000/children/P004/children/P027/children/P039/results/R033.md
- Check C035: problems/P000/children/P004/children/P027/children/P039/checks/C035.md

## Follow-ups
- none
