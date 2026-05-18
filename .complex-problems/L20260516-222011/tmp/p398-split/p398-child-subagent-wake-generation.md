# Subagent wake session generation boundary

## Problem

`novaic-agent-runtime/task_queue/sagas/subagent_wake.py` coerces `ctx["session_generation"]` through `int(...)`. Because this value is passed into subagent wake/session creation logic, it may be live session authority and needs an explicit boundary rather than an inline coercion.

## Success Criteria

- Inspect the subagent wake saga context contract for `session_generation`.
- Replace inline coercion with an explicit validator or prove with code evidence that the value is already typed and non-authority.
- Add focused regression tests for malformed/bool/missing generation if the path is live.
- Rerun targeted tests for subagent wake or related saga behavior.
- Document the final classification in the result.
