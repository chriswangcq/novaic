# Cut status usage and stack reads to event semantics

## Problem

`context_status(include_usage=True)` still renders through DFS `ContextEngine`, and default stack reads still rely on filesystem active stack traversal. Phase 4 needs status usage to come from projection and stack semantics to move toward event replay without breaking LIFO validation.

## Success Criteria

- `context_status(include_usage=True)` uses the event projection read adapter for message/token usage.
- Stack frames returned by status are event projection frames or explicitly justified operational control frames.
- Tests cover include_usage and stack output from event-authored state.
- Any remaining DFS stack traversal is classified as operational validation/debug, not LLM read source.
