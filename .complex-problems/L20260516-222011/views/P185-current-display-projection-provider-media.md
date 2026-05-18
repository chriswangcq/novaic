# P185: Current display projection provider media

Status: done
Parent: P127
Root: P000
Source Ticket: T174 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185
Body: problems/P000/children/P003/children/P127/children/P185/README.md
Ticket(s): T176

## Problem
Current-round display output must be projected into provider-usable image input while keeping the original tool message placeholder-only. This path must be audited from Cortex formatted step read through runtime multimodal conversion.

## Success Criteria
- Map display current projection in `step_result_projection.py`, `step_result_client.py`, and runtime multimodal conversion.
- Prove current display emits provider media input.
- Prove the tool message keeps a placeholder and does not retain raw base64 text.
- Fix or split any current-display branch that fails provider media conversion.

## Subproblems
- P188: Cortex current display projection contract
- P189: Runtime current display selection and active-stack ordering
- P190: Provider media adapter conversion
- P191: End-to-end display screenshot regression

## Results
- R183

## Latest Check
C197

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/README.md
- Ticket T176: problems/P000/children/P003/children/P127/children/P185/tickets/T176.md
- Result R183: problems/P000/children/P003/children/P127/children/P185/results/R183.md
- Check C197: problems/P000/children/P003/children/P127/children/P185/checks/C197.md

## Follow-ups
- none
