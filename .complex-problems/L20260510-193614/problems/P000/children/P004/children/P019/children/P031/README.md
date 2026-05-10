# Phase 3C2 Context Status SQLite Stack Read Cutover

## Problem

`context_status` default stack output still uses file-walk stack collection. It must read stack frames from the SQLite active-stack projection while preserving the existing response shape and leaving `include_usage=True` semantic context assembly unchanged.

## Success Criteria

- `context_status(include_usage=False)` returns stack frames from SQLite active-stack projection.
- Empty projection returns the existing empty stack response shape.
- `context_status(include_usage=True)` remains semantic ContextEvent read-model based.
- Tests prove status reads persisted SQLite projection rather than walking scope files.
