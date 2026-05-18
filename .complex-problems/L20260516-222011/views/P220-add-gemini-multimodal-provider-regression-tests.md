# P220: Add Gemini multimodal provider regression tests

Status: done
Parent: P217
Root: P000
Source Ticket: T208 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P220
Body: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P220/README.md
Ticket(s): T210

## Problem
The Gemini conversion gap needs tests that fail on the old stringification behavior and pass only when native image parts are emitted.

## Success Criteria
- Tests cover OpenAI-style `image_url` data URL list content.
- Tests assert no image base64 appears in text parts.
- Existing factory provider tests pass.

## Subproblems
- none

## Results
- R204

## Latest Check
C218

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P220/README.md
- Ticket T210: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P220/tickets/T210.md
- Result R204: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P220/results/R204.md
- Check C218: problems/P000/children/P003/children/P127/children/P187/children/P201/children/P217/children/P220/checks/C218.md

## Follow-ups
- none
