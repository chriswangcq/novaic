# Audit MCP image/data-url projection branch

## Problem

`parse_tool_result` still accepts MCP image blocks with inline `data` and turns them into data URLs; `_format_mcp_content` can emit image blocks only when `include_display=True`. This branch must be constrained to explicit display perception and must not leak into history/current-tool text contexts.

## Success Criteria

- The branch is either removed or explicitly justified as current display-perception-only behavior.
- Tests prove history/current-tool projections do not emit image content.
- Tests prove explicit display perception still works if the branch is retained.
