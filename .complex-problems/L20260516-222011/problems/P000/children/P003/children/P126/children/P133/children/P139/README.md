# ContextEvent pure projection map

## Problem

`project_context_events` transforms ordered events into LLM-facing messages and stack. Its event handlers must be mapped so later projection work does not violate LIFO, folded summaries, tool result ordering, or notification behavior.

## Success Criteria

- Projection invariants for stream/root/sequence validation are documented.
- Event handlers for wake, skill, system, context messages, notifications, assistant tool calls, and tool results are mapped.
- The roles of `step_ref`, `payload_ref`, orphan tool result marking, and folded summary messages are documented.
- Projection tests are run and any active issue is fixed or split.
