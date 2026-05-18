# P801: App generated VMuse asset copy sync

Status: done
Parent: P785
Root: P000
Source Ticket: T791 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P801
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P801/README.md
Ticket(s): T793

## Problem
`novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse` is a generated/committed VMuse copy that can still contain stale FastMCP/direct-media code after source cleanup.

## Success Criteria
- Generated Apple VMuse asset copy matches the cleaned app resource/source contract or is explicitly deleted if generated assets should not be committed.
- No stale FastMCP/SSE/stdio/direct-media markers remain in generated VMuse assets.
- A focused scan covers generated asset paths.

## Subproblems
- none

## Results
- R784

## Latest Check
C831

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P801/README.md
- Ticket T793: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P801/tickets/T793.md
- Result R784: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P801/results/R784.md
- Check C831: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P801/checks/C831.md

## Follow-ups
- none
