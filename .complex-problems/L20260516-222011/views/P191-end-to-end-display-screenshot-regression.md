# P191: End-to-end display screenshot regression

Status: done
Parent: P185
Root: P000
Source Ticket: T176 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P191
Body: problems/P000/children/P003/children/P127/children/P185/children/P191/README.md
Ticket(s): T186

## Problem
Create or verify an end-to-end regression path that represents the real user flow: shell/device screenshot creates a blob artifact, display perceives it, and the next LLM request receives the image while the tool result remains placeholder-only.

## Success Criteria
- Build or identify a focused regression test covering shell artifact -> display tool -> next context assembly.
- Assert provider-visible image/media input exists.
- Assert display tool result content is placeholder-only, with no raw base64 or large JSON payload.
- Assert active-stack injection after the display result does not break image attachment.

## Subproblems
- none

## Results
- R182

## Latest Check
C196

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P191/README.md
- Ticket T186: problems/P000/children/P003/children/P127/children/P185/children/P191/tickets/T186.md
- Result R182: problems/P000/children/P003/children/P127/children/P185/children/P191/results/R182.md
- Check C196: problems/P000/children/P003/children/P127/children/P185/children/P191/checks/C196.md

## Follow-ups
- none
