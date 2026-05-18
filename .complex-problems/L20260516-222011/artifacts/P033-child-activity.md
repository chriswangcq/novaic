# Child Problem: monitor/activity projection legacy boundary

## Problem

Activity projection still maps direct-tool names for historical monitor readability. That is useful, but the implementation and tests should make it impossible to confuse those labels with active tool execution policy.

## Success Criteria

- Keep historical monitor rendering if needed.
- Move/rename legacy direct-tool labels behind explicit historical naming.
- Ensure shell-first `agentctl` activity is the primary current-path behavior.
- Run activity projection/UI focused tests.
