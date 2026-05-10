# Migrate Direct Cortex Constructor Tests

## Problem

Many tests still call `Cortex(MemoryStore(), agent_id)` or `Cortex(store, agent_id=...)`. Runtime no longer supports that path. This belongs under P028 because tests must prove the runtime uses `Cortex(workspace=...)` and not direct store construction.

## Success Criteria

- All Cortex runtime tests construct a Workspace explicitly and call `Cortex(workspace=...)`.
- No `Cortex(MemoryStore`, `Cortex(store`, or positional `Cortex(` store constructor remains in tests.
- Targeted runtime/tool/hook tests pass.
