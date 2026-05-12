# P002: Display Media Survives Runtime Wrapping

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
The explicit `display` tool currently returns `_mcp_content` with image data, but the generic runtime `_ok()` wrapper demotes it into `tool-output.v1.text` because it is not already `tool-output.v1`. Preserve display media through runtime wrapping so current explicit display perception can become provider-facing structured image content.

## Success Criteria
- Runtime wrapping preserves direct `_mcp_content` display output without serializing image base64 into `tool-output.v1.text`.
- Cortex display-perception projection can parse the wrapped display result into `display_files`.
- Runtime multimodal conversion produces a separate structured `image_url` user content part for current display perception.
- The tool text message contains placeholders/metadata and no raw base64 image data.
- Historical/non-display projections still do not inject images.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
