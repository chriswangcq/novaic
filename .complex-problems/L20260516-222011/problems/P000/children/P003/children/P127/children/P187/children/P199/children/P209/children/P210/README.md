# Audit nested result wrapper projection branch

## Problem

`parse_tool_result` still unwraps a nested `result` dict before projection. This may be needed for older persisted tool payloads or may be stale compatibility. Decide branch fate with evidence and tests.

## Success Criteria

- Current/persisted reason for nested `result` unwrapping is proven or the branch is removed.
- Tests reflect the decision.
- History/current-tool projections remain text/manifest-only.
