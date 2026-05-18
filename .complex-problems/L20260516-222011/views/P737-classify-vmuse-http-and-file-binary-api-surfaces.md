# P737: Classify VMuse HTTP and file binary API surfaces

Status: done
Parent: P734
Root: P000
Source Ticket: T724 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P737
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P737/README.md
Ticket(s): T729

## Problem
Classify `novaic-mcp-vmuse` HTTP server and file binary APIs that expose or accept base64 content. These may be legitimate standalone transport APIs, but they should not be mistaken for the active shell/display contract.

## Success Criteria
- HTTP screenshot endpoints in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py` are classified with file pointers.
- Binary file pull/push paths in `tools/files.py` and `http_server.py` are classified with file pointers.
- The result states whether each API is standalone compatibility, active shell/runtime, or remediation candidate.
- Exact cleanup/remediation candidates are listed if any path is stale or contract-violating.

## Subproblems
- none

## Results
- R719

## Latest Check
C763

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P737/README.md
- Ticket T729: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P737/tickets/T729.md
- Result R719: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P737/results/R719.md
- Check C763: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P737/checks/C763.md

## Follow-ups
- none
