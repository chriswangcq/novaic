# P003: Full Path Regression Tests And Audit

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Existing tests cover idealized direct inputs but missed the actual executor-wrapper-Cortex-runtime path. Add or update tests so the real path catches both shell contract regressions and display base64 leakage.

## Success Criteria
- A regression test exercises display executor output through `_ok()`, Cortex `parse_tool_result` / `format_for_display_perception_llm`, and runtime `process_multimodal_messages`.
- Tests prove shell large output is bounded and does not include full raw stdout/stderr in diagnostics.
- Tests prove current display creates structured image content and history/current non-display projections do not inject images.
- Relevant focused tests pass.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
