# P038: Phase 3.5.1: Emit SkillScopeOpened on skill_begin success

Status: done
Parent: P027
Root: P000
Package: problems/P000/children/P004/children/P027/children/P038
Body: problems/P000/children/P004/children/P027/children/P038/README.md
Ticket(s): T035

## Problem
Successful `/v1/context/skill_begin` currently creates a child scope directory and root scope id index, but does not append the authoritative `SkillScopeOpened` event.

## Success Criteria
- Successful `context_skill_begin` appends `SkillScopeOpened` after child scope creation.
- Event payload includes child scope id, parent scope id, skill name, and display name/task.
- Duplicate/invalid/depth-limit failure paths do not append open events.
- Focused API tests inspect the event stream.

## Subproblems
- none

## Results
- R032

## Latest Check
C034

## Bodies
- Problem: problems/P000/children/P004/children/P027/children/P038/README.md
- Ticket T035: problems/P000/children/P004/children/P027/children/P038/tickets/T035.md
- Result R032: problems/P000/children/P004/children/P027/children/P038/results/R032.md
- Check C034: problems/P000/children/P004/children/P027/children/P038/checks/C034.md

## Follow-ups
- none
