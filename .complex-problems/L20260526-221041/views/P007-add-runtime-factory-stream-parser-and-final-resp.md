# P007: Add Runtime Factory stream parser and final response aggregator

Status: done
Parent: P002
Root: P000
Source Ticket: T004 (split)
Source Check: none
Package: problems/P000/children/P002/children/P007
Body: problems/P000/children/P002/children/P007/README.md
Ticket(s): T005

## Problem
Runtime Factory client must consume Factory normalized SSE chunks and aggregate them into a complete OpenAI-style chat completion response compatible with current saga code.

## Success Criteria
- Runtime can parse Factory SSE `data:` lines with `type=delta`, `type=done`, and `type=error`.
- Aggregator builds final assistant message fields for `content`, `reasoning_content`, `tool_calls`, `finish_reason`, `usage`, and `x_factory` where present.
- Unit tests cover reasoning/content accumulation, tool-call argument fragments, terminal/error handling, and non-streaming client behavior.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/children/P007/README.md
- Ticket T005: problems/P000/children/P002/children/P007/tickets/T005.md
- Result R003: problems/P000/children/P002/children/P007/results/R003.md
- Check C003: problems/P000/children/P002/children/P007/checks/C003.md

## Follow-ups
- none
