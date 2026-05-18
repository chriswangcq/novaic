# P728: Legacy and standalone media-byte surface classification

Status: done
Parent: P722
Root: P000
Source Ticket: T715 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/README.md
Ticket(s): T722

## Problem
Classify remaining screenshot/image/base64-producing surfaces, especially standalone MCP/plugin code such as `novaic-mcp-vmuse`, so legitimate non-shell media APIs are not confused with active shell/runtime context behavior.

## Success Criteria
- Remaining media-byte or image-content emitting code paths are listed with file pointers.
- Each path is classified as active shell/runtime, standalone plugin/MCP, test fixture, doc, or obsolete residue.
- Active violations are forwarded to remediation candidates.
- Obsolete or misleading residue candidates are forwarded to remediation candidates for deletion or doc correction.

## Subproblems
- P732: Active non-test media-byte surface classification
- P733: Docs and test media-byte residue classification

## Results
- R724

## Latest Check
C769

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/README.md
- Ticket T722: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/tickets/T722.md
- Result R724: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/results/R724.md
- Check C769: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/checks/C769.md

## Follow-ups
- none
