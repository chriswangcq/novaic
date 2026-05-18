# Runtime current display selection and active-stack ordering

## Problem

Audit runtime context assembly to ensure current display media is selected by current-round/tool metadata rather than fragile adjacency. The active-stack system message can appear after tool messages, but must not prevent current display media from being attached to the next LLM request.

## Success Criteria

- Map runtime/common code that chooses current display media for LLM context.
- Prove display selection survives a following `[Active skill stack]` system message.
- Prove the tool result message remains small and placeholder-only after display.
- Fix or create follow-up work for any positional or ordering-sensitive branch.

