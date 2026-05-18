# P742: Update stale VMuse protocol mapping documentation

Status: done
Parent: P723
Root: P000
Source Ticket: T733 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P742
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P742/README.md
Ticket(s): T734

## Problem
Discovery found the doc can mislead future work into reintroducing direct MCP/media tool exposure. The current design is shell/device proxy for action, Blob/tool-output manifests for shell text, and explicit `display` for current-round visual perception.

## Success Criteria
- The doc clearly marks old direct MCP exposure material as historical or replaces it with the current shell/device-proxy boundary.
- The doc states that shell/history must not carry raw base64/media bytes as text.
- The doc points to Blob manifests and display projection as the current contract.
- Documentation-only checks or a targeted grep confirm no stale live-design claim remains in that file.

## Subproblems
- none

## Results
- R726

## Latest Check
C771

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P742/README.md
- Ticket T734: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P742/tickets/T734.md
- Result R726: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P742/results/R726.md
- Check C771: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P723/children/P742/checks/C771.md

## Follow-ups
- none
