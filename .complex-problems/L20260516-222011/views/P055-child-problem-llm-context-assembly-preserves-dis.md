# P055: Child Problem: LLM context assembly preserves displayed images as images

Status: done
Parent: P051
Root: P000
Source Ticket: T043 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P055
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P055/README.md
Ticket(s): T045

## Problem
After `display(blob://...)`, the next LLM request must contain the displayed image as model-visible image content, not just an `OK` text marker and not a base64 blob inside a text message. The context assembly layer is responsible for preserving the semantic image reference into the model call.

## Success Criteria
- A displayed image artifact becomes model-visible image content in the assembled request.
- The assembled request does not put image bytes into `role=tool` text content.
- Focused tests inspect the actual assembled message/request shape.

## Subproblems
- none

## Results
- R039

## Latest Check
C049

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P055/README.md
- Ticket T045: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P055/tickets/T045.md
- Result R039: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P055/results/R039.md
- Check C049: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P055/checks/C049.md

## Follow-ups
- none
