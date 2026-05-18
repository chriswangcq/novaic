# P744: Disposition Device VmControl screenshot route

Status: done
Parent: P723
Root: P000
Source Ticket: T733 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P744
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P744/README.md
Ticket(s): T736

## Problem
`novaic-device/device/vmcontrol_routes.py` exposes `/api/vmcontrol/vms/{vm_id}/screenshot` returning inline MCP image bytes. It may be legacy/debug compatibility, but because it is mounted it must be dispositioned carefully rather than left as ambiguous residue.

## Success Criteria
- Identify in-repo callers and route ownership.
- Decide whether to retire, mark legacy/debug-only, or convert to Blob/artifact manifest.
- If route behavior changes, update tests and any affected clients.
- If safe disposition cannot be completed in one child, split into a deeper child with exact blockers.

## Subproblems
- P745: Analyze Device screenshot route usage and ownership
- P746: Implement Device screenshot route disposition

## Results
- R730

## Latest Check
C775

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P744/README.md
- Ticket T736: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P744/tickets/T736.md
- Result R730: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P744/results/R730.md
- Check C775: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P744/checks/C775.md

## Follow-ups
- none
