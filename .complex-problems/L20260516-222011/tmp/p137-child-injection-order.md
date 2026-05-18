# Active stack final context injection ordering map

## Problem

The `[Active skill stack ...]` system message appears in final LLM context. Its injection point and ordering relative to assistant tool calls, tool results, and context-event messages must be mapped so late system messages do not alter current-round tool-result semantics.

## Success Criteria

- Identify the production code that converts projected active stack state into final LLM messages.
- Document exact ordering relative to tool result expansion and provider-specific formatting.
- Add or tighten tests if ordering is only implied by snapshots or not covered.
- Fix or split any duplicate stack injection path.
