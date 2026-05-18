# P219: Implement Gemini multimodal content conversion

Status: done
Parent: P217
Root: P000
Source Ticket: T208 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P219
Body: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P219/README.md
Ticket(s): T209

## Problem
GoogleProvider needs to convert OpenAI-style list content into Gemini parts instead of stringifying it.

## Success Criteria
- Text items become `{"text": ...}` parts.
- Data URL `image_url` items become inline image parts.
- Image base64 is not inserted into text parts.
- Plain string behavior remains unchanged.

## Subproblems
- none

## Results
- R203

## Latest Check
C217

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P219/README.md
- Ticket T209: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P219/tickets/T209.md
- Result R203: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P219/results/R203.md
- Check C217: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P219/checks/C217.md

## Follow-ups
- none
