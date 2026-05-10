# P040 not-success check

## Summary

Not success. R034 found a real lifecycle bypass: older JWT `/v1/skill/begin` and `/v1/skill/end` can still call `Cortex.skill_begin/end`, which directly create/close scope filesystem state without lifecycle events.

## Blocking Gaps

- `/v1/skill/begin` is not event-wired and can create child scopes through `Cortex.skill_begin`.
- `/v1/skill/end` is not event-wired and can close child scopes through `Cortex.skill_end`.
- `Cortex.skill_begin/end` still contain direct `Workspace.create_scope/complete_child_scope` lifecycle writes, so the event path is not yet the only write path.

## Result IDs

- R034
