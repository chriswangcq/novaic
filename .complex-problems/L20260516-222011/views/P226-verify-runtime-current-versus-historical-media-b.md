# P226: Verify runtime current versus historical media boundary

Status: done
Parent: P128
Root: P000
Source Ticket: T216 (split)
Source Check: none
Package: problems/P000/children/P003/children/P128/children/P226
Body: problems/P000/children/P003/children/P128/children/P226/README.md
Ticket(s): T218

## Problem
Current-round display can become provider media, but historical/non-display tool results must remain bounded text/manifest. Verify the runtime enforces this boundary.

## Success Criteria
- Current display uses `display_perception` and can produce provider image content.
- Historical display and non-display tools do not create provider image messages.
- Shell/blob/payload results stay bounded text/manifest in LLM context.
- Targeted tests pass.

## Subproblems
- none

## Results
- R215

## Latest Check
C229

## Bodies
- Problem: problems/P000/children/P003/children/P128/children/P226/README.md
- Ticket T218: problems/P000/children/P003/children/P128/children/P226/tickets/T218.md
- Result R215: problems/P000/children/P003/children/P128/children/P226/results/R215.md
- Check C229: problems/P000/children/P003/children/P128/children/P226/checks/C229.md

## Follow-ups
- none
