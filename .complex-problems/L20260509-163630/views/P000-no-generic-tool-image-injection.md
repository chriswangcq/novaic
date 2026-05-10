# P000: No generic tool image injection

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
`process_multimodal_messages()` still scans every tool/tool_result message for `_mcp_content` images and turns those images into user messages. That means a historical or non-display tool result can still synthesize provider-visible image content after Cortex projection, even though the new model requires only explicit `display` perception to do that.

## Success Criteria
- Generic tool/tool_result messages no longer trigger image extraction.
- Only messages marked as `display_perception` may be converted into provider-visible image user messages.
- Runtime step-ref expansion marks the projection mode for the multimodal processor and removes that internal marker before provider delivery.
- Tests prove historical/generic tool image content is not injected and explicit display perception still works.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
