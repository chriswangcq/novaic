# P727: Display current-round LLM image projection discovery

Status: done
Parent: P722
Root: P000
Source Ticket: T715 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P727
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P727/README.md
Ticket(s): T721

## Problem
Discover how the display tool consumes Blob/artifact references and how current-round displayed images are projected into LLM requests. This must verify whether images are sent through the model API as image content rather than serialized base64 text.

## Success Criteria
- Display tool handler/executor code is identified with file pointers.
- LLM request construction path for display image projection is identified with file pointers.
- Tests or logs proving current-round image projection behavior are identified where present.
- Any active path that converts displayed images into text/base64 in LLM messages is listed as a remediation candidate.

## Subproblems
- none

## Results
- R713

## Latest Check
C757

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P727/README.md
- Ticket T721: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P727/tickets/T721.md
- Result R713: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P727/results/R713.md
- Check C757: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P727/checks/C757.md

## Follow-ups
- none
