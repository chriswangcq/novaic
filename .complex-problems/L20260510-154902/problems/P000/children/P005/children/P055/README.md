# Cut prepare_for_llm API to event projection

## Problem

`/v1/context/prepare_for_llm` still instantiates DFS `ContextEngine` and reads legacy projection files as source. It must use the event projection read adapter as the primary and only source.

## Success Criteria

- `context_prepare_for_llm` no longer imports or instantiates `ContextEngine`.
- Prepared context messages come from ContextEvent projection.
- Focused API tests cover active wake, notification hints, tool results, and closed skills from events.
- No silent DFS fallback exists.
