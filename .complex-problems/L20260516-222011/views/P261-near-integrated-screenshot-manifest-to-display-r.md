# P261: Near-integrated screenshot manifest to display replay regression

Status: done
Parent: P132
Root: P000
Source Ticket: T254 (split)
Source Check: none
Package: problems/P000/children/P003/children/P132/children/P261
Body: problems/P000/children/P003/children/P132/children/P261/README.md
Ticket(s): T263

## Problem
Local Cortex and runtime tests can pass independently while the real flow still breaks. Add or verify a near-integrated regression that models shell screenshot artifact manifest output, explicit display/current media projection, and later historical replay without raw base64 text leakage.

## Success Criteria
- A near-integrated test exists or is added for screenshot manifest -> display/current projection -> historical replay.
- The test uses realistic `tool-output.v1` and/or `tool-step-payload.v1` shapes.
- The test asserts the display/current path has image media only when explicit display perception is selected.
- The test asserts later history replay contains no raw base64/data URL text.

## Subproblems
- P269: Near-integrated screenshot/display coverage inventory
- P270: Near-integrated screenshot/display regression implementation
- P271: Near-integrated screenshot/display focused verification

## Results
- R268

## Latest Check
C283

## Bodies
- Problem: problems/P000/children/P003/children/P132/children/P261/README.md
- Ticket T263: problems/P000/children/P003/children/P132/children/P261/tickets/T263.md
- Result R268: problems/P000/children/P003/children/P132/children/P261/results/R268.md
- Check C283: problems/P000/children/P003/children/P132/children/P261/checks/C283.md

## Follow-ups
- none
