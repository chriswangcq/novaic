# P188: Cortex current display projection contract

Status: done
Parent: P185
Root: P000
Source Ticket: T176 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P188
Body: problems/P000/children/P003/children/P127/children/P185/children/P188/README.md
Ticket(s): T177

## Problem
Audit Cortex display step projection for current-round display results. The projection must expose media as structured display/media metadata for current perception, while historical/tool-message text remains bounded and placeholder-like.

## Success Criteria
- Map display parsing and formatting functions in `novaic-cortex/novaic_cortex/step_result_projection.py` and `step_result_client.py`.
- Prove current display projection produces display/media content separate from plain text.
- Prove historical display projection remains manifest/text-only and does not rehydrate raw images.
- Fix or create follow-up work for any Cortex projection branch that mixes raw base64 into text.

## Subproblems
- none

## Results
- R173

## Latest Check
C187

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P188/README.md
- Ticket T177: problems/P000/children/P003/children/P127/children/P185/children/P188/tickets/T177.md
- Result R173: problems/P000/children/P003/children/P127/children/P185/children/P188/results/R173.md
- Check C187: problems/P000/children/P003/children/P127/children/P185/children/P188/checks/C187.md

## Follow-ups
- none
