# ActivityTimeline shell-first cleanup and focused tests

## Problem
ActivityTimeline currently treats retired direct IM tool names as normal product examples. The UI path should make shell/agentctl records primary and isolate or remove legacy direct-tool assumptions.

## Description
Patch ActivityTimeline and focused tests based on the inventory.

## Success Criteria
- Current-path tests use shell/agentctl-shaped records for read/reply behavior.
- Any remaining old tool names in component code are under explicit legacy naming.
- Public labels remain correct and raw low-level names stay hidden.
- Focused ActivityTimeline tests pass.
- Focused grep classifies any remaining old names.
