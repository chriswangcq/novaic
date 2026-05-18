# P051: Child Problem: display and LLM image projection avoids text base64

Status: done
Parent: P048
Root: P000
Source Ticket: T041 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/README.md
Ticket(s): T043

## Problem
The display/image path must not serialize image bytes as text inside LLM messages. When an image artifact is loaded for model perception, context assembly should use the provider's native image/multimodal content shape or a compact artifact reference, not a text blob containing base64.

## Success Criteria
- Display tool observations returned to text history remain concise and do not include image base64.
- LLM request assembly for displayed images uses model-native image content or the intended non-text image representation.
- Focused tests or request-shape inspections prove no `role=tool` text message contains display base64.

## Subproblems
- P054: Child Problem: display tool output is concise and non-binary
- P055: Child Problem: LLM context assembly preserves displayed images as images
- P056: Child Problem: provider adapters receive image payloads through the right contract

## Results
- R043

## Latest Check
C055

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/README.md
- Ticket T043: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/tickets/T043.md
- Result R043: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/results/R043.md
- Check C055: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/checks/C055.md

## Follow-ups
- none
