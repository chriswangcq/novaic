# P800: App VMuse resource copy sync

Status: done
Parent: P785
Root: P000
Source Ticket: T791 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P800
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P800/README.md
Ticket(s): T792

## Problem
`novaic-app/src-tauri/resources/novaic-mcp-vmuse` is a committed VMuse copy that can drift from source VMuse cleanup and still carry stale FastMCP/direct-media code.

## Success Criteria
- App resource VMuse copy matches source VMuse for cleaned source files or is explicitly removed if it should not be committed.
- No stale FastMCP/SSE/stdio/direct-media markers remain in the app resource VMuse copy.
- A focused diff/scan proves resource copy consistency.

## Subproblems
- none

## Results
- R783

## Latest Check
C830

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P800/README.md
- Ticket T792: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P800/tickets/T792.md
- Result R783: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P800/results/R783.md
- Check C830: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P800/checks/C830.md

## Follow-ups
- none
