# P734: Complete residual production media-byte classification

Status: done
Parent: P732
Root: P000
Source Ticket: none (none)
Source Check: C758
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/README.md
Ticket(s): T724

## Problem
Close the remaining gaps in the active non-test media-byte surface classification. Re-scan the production code hits, inspect each remaining unclassified surface, and decide whether each path is active shell/runtime, current-round display/provider transport, standalone MCP/plugin, internal encoding, legacy compatibility, or remediation candidate. In particular, resolve `novaic-device/device/vmcontrol_routes.py`, all `novaic-mcp-vmuse` screenshot/file/base64 surfaces, and any smaller missed hits such as `tools/windows.py`.

## Success Criteria
- Every remaining non-test media-byte/base64 hit from the production scan is either classified with a file pointer or explicitly declared irrelevant with evidence.
- `novaic-device/device/vmcontrol_routes.py` screenshot route has a clear status: active product path, legacy compatibility, safe-to-retire, or remediation candidate.
- `novaic-mcp-vmuse` media/file base64 surfaces are classified by module rather than only as a broad package.
- The final result lists exact remediation candidates for the parent cleanup phase.

## Subproblems
- P735: Classify Device VmControl screenshot route
- P736: Classify VMuse MCP tool media-byte surfaces
- P737: Classify VMuse HTTP and file binary API surfaces

## Results
- R720

## Latest Check
C764

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/README.md
- Ticket T724: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/tickets/T724.md
- Result R720: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/results/R720.md
- Check C764: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/checks/C764.md

## Follow-ups
- none
