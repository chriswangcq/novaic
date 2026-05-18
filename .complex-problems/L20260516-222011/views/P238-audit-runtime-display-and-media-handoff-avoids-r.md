# P238: Audit runtime display and media handoff avoids raw image text

Status: done
Parent: P236
Root: P000
Source Ticket: T225 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P238
Body: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P238/README.md
Ticket(s): T227

## Problem
The runtime display/media path must present visual artifacts to the model through the correct media/content channel or compact tool result, not as raw base64 text in normal history.

This belongs under `P236` because display/media outputs have different contracts from shell stdout and previously risked raw image text entering context.

## Success Criteria
- Display/media tool result handling and LLM message conversion paths are mapped with file/function pointers.
- Evidence shows normal tool result text is compact and image data is not passed as raw text history.
- Focused display/media tests pass, including no historical tool image/base64 injection.

## Subproblems
- none

## Results
- R221

## Latest Check
C235

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P238/README.md
- Ticket T227: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P238/tickets/T227.md
- Result R221: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P238/results/R221.md
- Check C235: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P238/checks/C235.md

## Follow-ups
- none
