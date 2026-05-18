# P590: Runtime resolves current display image refs for LLM calls

Status: done
Parent: P586
Root: P000
Source Ticket: T576 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P590
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P590/README.md
Ticket(s): T580

## Problem
Once Cortex returns display media references instead of image bytes, runtime LLM request assembly must resolve only current-round `display_perception` image refs through Blob Service and convert them into provider-ready multimodal content. This must not happen for history, summaries, or non-display tools.

## Success Criteria
- Step-ref expansion resolves `image_ref` only when projection is `display_perception`.
- Blob Service access is explicit and dependency-bounded through runtime config/client inputs.
- Resolved images feed the existing `process_multimodal_messages` path as image MCP content.
- Non-display and historical tool outputs are not fetched as images.
- Oversized or unreadable BlobRefs degrade to bounded text diagnostics, not base64 or crashes.

## Subproblems
- none

## Results
- R573

## Latest Check
C610

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P590/README.md
- Ticket T580: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P590/tickets/T580.md
- Result R573: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P590/results/R573.md
- Check C610: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P590/checks/C610.md

## Follow-ups
- none
