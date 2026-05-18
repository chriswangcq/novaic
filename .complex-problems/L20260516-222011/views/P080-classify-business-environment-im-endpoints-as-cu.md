# P080: Classify Business environment IM endpoints as current shell boundary

Status: done
Parent: P077
Root: P000
Source Ticket: T068 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P080
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P080/README.md
Ticket(s): T071

## Problem
`business/internal/environment.py` still exposes `environment_im_read` and `environment_im_reply`. These names match old direct-tool concepts, but may now be the current shell `agentctl` boundary. The boundary needs explicit classification and non-misleading wording.

## Success Criteria
- Environment IM endpoints are confirmed current or removed if obsolete.
- Comments/docstrings/API names do not imply direct LLM tools.
- Any required current shell boundary tests still pass.

## Subproblems
- none

## Results
- R063

## Latest Check
C075

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P080/README.md
- Ticket T071: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P080/tickets/T071.md
- Result R063: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P080/results/R063.md
- Check C075: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/children/P076/children/P077/children/P080/checks/C075.md

## Follow-ups
- none
