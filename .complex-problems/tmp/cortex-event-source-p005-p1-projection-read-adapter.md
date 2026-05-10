# Build event projection read adapter

## Problem

API read paths need a small adapter that reads ordered ContextEvents, replays `project_context_events`, applies budget compaction, and returns messages/stack/token estimates without touching DFS context files.

## Success Criteria

- A reusable read adapter exists for prepared context/status usage.
- Adapter reads from `ContextEventStore` and `project_context_events`.
- Adapter has focused tests for notification hints, active messages, assistant tool calls, tool results, and closed skill summaries.
- Adapter does not fallback to `ContextEngine` or DFS files.
