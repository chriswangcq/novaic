# P000: Cortex explicit projection modes

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Cortex and Runtime still pass a generic `include_display` boolean through step result expansion. That boolean blurs distinct projection intents: history replay, current tool result, explicit display perception, and monitor preview. The shell/display architecture needs these modes explicit so historical or non-display tool outputs cannot accidentally re-inject image/base64 content into LLM context.

## Success Criteria
- Cortex exposes explicit projection functions for history, current tool result, display perception, and monitor/text preview.
- Runtime step-ref expansion chooses projection mode from message round/tool identity instead of relying on a generic current-round `include_display` boolean.
- Historical and current non-display tool outputs do not inline legacy image data.
- Current explicit `display` can still produce provider-visible image content.
- Focused Cortex and Runtime projection tests pass.

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
