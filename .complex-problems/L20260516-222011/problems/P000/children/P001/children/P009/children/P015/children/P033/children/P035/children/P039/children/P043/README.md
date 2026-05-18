# Child Problem: runtime activity projection test fixtures

## Problem

Runtime activity projection tests include archived direct `im_read` tool calls. This overlaps monitor projection behavior and should be coordinated with the monitor boundary cleanup.

## Success Criteria

- Archived direct-tool fixtures are named as legacy/historical records.
- Current-path activity tests use shell/agentctl examples.
- Focused activity projection tests pass.
