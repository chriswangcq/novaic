# P123: Display Tool History Sanitization Audit

Status: done
Parent: P104
Root: P000
Source Ticket: T116 (split)
Source Check: none
Package: problems/P000/children/P002/children/P104/children/P123
Body: problems/P000/children/P002/children/P104/children/P123/README.md
Ticket(s): T118

## Problem
`display(blob://...)` may produce current-turn perception content, but public/history tool output must stay sanitized so future context does not contain raw image base64 or data URLs.

## Success Criteria
- Inspect runtime display executor wrapping and Cortex step-result projection.
- Verify historical display tool messages are text or placeholders only.
- Verify current non-display history also remains text-only.
- Fix any projection path that reinserts raw base64 into ordinary context.

## Subproblems
- none

## Results
- R115

## Latest Check
C129

## Bodies
- Problem: problems/P000/children/P002/children/P104/children/P123/README.md
- Ticket T118: problems/P000/children/P002/children/P104/children/P123/tickets/T118.md
- Result R115: problems/P000/children/P002/children/P104/children/P123/results/R115.md
- Check C129: problems/P000/children/P002/children/P104/children/P123/checks/C129.md

## Follow-ups
- none
