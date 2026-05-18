# P196: Factory provider request adapter media preservation

Status: done
Parent: P195
Root: P000
Source Ticket: T183 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P196
Body: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P196/README.md
Ticket(s): T184

## Problem
Audit Factory's provider request adapter so structured image content from runtime is sent to the provider API in the correct schema instead of being dropped, stringified, or flattened.

## Success Criteria
- Locate Factory provider adapter/client modules.
- Prove OpenAI-compatible `image_url` content survives to the provider request.
- Prove raw base64 is not moved into text fields.
- Add or verify focused adapter tests.

## Subproblems
- none

## Results
- R178

## Latest Check
C192

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P196/README.md
- Ticket T184: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P196/tickets/T184.md
- Result R178: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P196/results/R178.md
- Check C192: problems/P000/children/P003/children/P127/children/P185/children/P190/children/P195/children/P196/checks/C192.md

## Follow-ups
- none
