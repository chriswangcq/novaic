# P217: Fix Google/Gemini multimodal provider conversion

Status: done
Parent: P201
Root: P000
Source Ticket: T206 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217
Body: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/README.md
Ticket(s): T208

## Problem
Inventory found that Google/Gemini provider handling does not preserve/convert list multimodal message content, so display image perception can silently degrade or stringify.

## Success Criteria
- Google/Gemini provider converts text + image content into a native request shape.
- Provider tests prove base64 image data is not placed into text parts.
- Existing OpenAI/Anthropic behavior remains intact.

## Subproblems
- P219: Implement Gemini multimodal content conversion
- P220: Add Gemini multimodal provider regression tests

## Results
- R205

## Latest Check
C219

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/README.md
- Ticket T208: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/tickets/T208.md
- Result R205: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/results/R205.md
- Check C219: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/checks/C219.md

## Follow-ups
- none
