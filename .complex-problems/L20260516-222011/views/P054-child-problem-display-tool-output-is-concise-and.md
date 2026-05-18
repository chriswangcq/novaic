# P054: Child Problem: display tool output is concise and non-binary

Status: done
Parent: P051
Root: P000
Source Ticket: T043 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P054
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P054/README.md
Ticket(s): T044

## Problem
The `display` tool result that is written into tool history must stay concise. It should acknowledge loading or projecting the artifact without embedding base64 image bytes, data URLs, or large JSON text.

## Success Criteria
- Active `display` tool handler returns compact tool text for images.
- Display tool observation text never includes raw image base64 or `data:image/*;base64`.
- Focused tests prove the tool-result text contract.

## Subproblems
- none

## Results
- R038

## Latest Check
C048

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P054/README.md
- Ticket T044: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P054/tickets/T044.md
- Result R038: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P054/results/R038.md
- Check C048: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P054/checks/C048.md

## Follow-ups
- none
