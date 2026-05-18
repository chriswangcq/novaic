# P211: Audit MCP image/data-url projection branch

Status: done
Parent: P209
Root: P000
Source Ticket: T198 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P211
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P211/README.md
Ticket(s): T200

## Problem
`parse_tool_result` still accepts MCP image blocks with inline `data` and turns them into data URLs; `_format_mcp_content` can emit image blocks only when `include_display=True`. This branch must be constrained to explicit display perception and must not leak into history/current-tool text contexts.

## Success Criteria
- The branch is either removed or explicitly justified as current display-perception-only behavior.
- Tests prove history/current-tool projections do not emit image content.
- Tests prove explicit display perception still works if the branch is retained.

## Subproblems
- none

## Results
- R194

## Latest Check
C208

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P211/README.md
- Ticket T200: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P211/tickets/T200.md
- Result R194: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P211/results/R194.md
- Check C208: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P211/checks/C208.md

## Follow-ups
- none
