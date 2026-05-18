# P788: Cortex Step Result Projection BlobRef Contract Cleanup

Status: done
Parent: P783
Root: P000
Source Ticket: T776 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/README.md
Ticket(s): T778

## Problem
`novaic-cortex/novaic_cortex/step_result_projection.py` still has compatibility paths for direct MCP inline image/data URL display perception. The final contract should avoid preserving raw media payloads in context and prefer BlobRef/tool-output manifest paths.

## Success Criteria
- Direct inline image/data URL compatibility is removed or narrowed to a safe manifest-only projection.
- Existing BlobRef/display behavior remains intact.
- Focused Cortex tests cover the projection behavior.
- Targeted scans show no active path reintroduces base64/data URL display payloads into LLM context.

## Subproblems
- P789: Cortex Projection Contract Inspection
- P790: Cortex Projection BlobRef-Only Patch

## Results
- R771

## Latest Check
C817

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/README.md
- Ticket T778: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/tickets/T778.md
- Result R771: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/results/R771.md
- Check C817: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/checks/C817.md

## Follow-ups
- none
