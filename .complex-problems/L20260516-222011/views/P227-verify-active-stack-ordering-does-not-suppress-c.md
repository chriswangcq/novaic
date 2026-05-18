# P227: Verify active-stack ordering does not suppress current display media

Status: done
Parent: P128
Root: P000
Source Ticket: T216 (split)
Source Check: none
Package: problems/P000/children/P003/children/P128/children/P227
Body: problems/P000/children/P003/children/P128/children/P227/README.md
Ticket(s): T219

## Problem
The active skill stack/system message is appended near the end of context. Verify current display-derived media remains present and correctly ordered even when a system Active Skill Stack message follows the display tool result.

## Success Criteria
- There is a targeted test for display result followed by active-stack/system message.
- The prepared LLM messages still include a provider image user message.
- The display tool result text is sanitized with placeholders rather than base64.

## Subproblems
- none

## Results
- R216

## Latest Check
C230

## Bodies
- Problem: problems/P000/children/P003/children/P128/children/P227/README.md
- Ticket T219: problems/P000/children/P003/children/P128/children/P227/tickets/T219.md
- Result R216: problems/P000/children/P003/children/P128/children/P227/results/R216.md
- Check C230: problems/P000/children/P003/children/P128/children/P227/checks/C230.md

## Follow-ups
- none
