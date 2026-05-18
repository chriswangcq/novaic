# P816: Child Problem: Factory logs rendering inventory

Status: done
Parent: P812
Root: P000
Source Ticket: T805 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P816
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P816/README.md
Ticket(s): T806

## Problem
Before editing `factory-logs.html`, map every raw request/response/message/tool rendering entrypoint so the scrub layer is not attached to only one tab while another tab keeps leaking raw payloads.

## Success Criteria
- Inventory lists all relevant rendering functions and the raw values they render.
- Each rendering entrypoint is assigned to either safe metadata, projected payload, or removed.
- The inventory identifies the minimal helper shape needed for implementation.

## Subproblems
- none

## Results
- R796

## Latest Check
C845

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P816/README.md
- Ticket T806: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P816/tickets/T806.md
- Result R796: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P816/results/R796.md
- Check C845: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P816/checks/C845.md

## Follow-ups
- none
