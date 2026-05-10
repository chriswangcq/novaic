# Phase 2: Context projections and replay

## Problem

Implement projections from the context event stream to LLM context state and workspace-compatible views. This includes folded summaries, active stack, tool observations, notification hints, and replay/repair behavior.

## Success Criteria

- A pure replay/projector can derive prepared LLM messages and active stack from events.
- Projection handles wake start, system prompt, notification hint, assistant message, tool step, skill begin, skill end, and wake archive events.
- Projection output is generation-checked and can be rebuilt from event stream.
- Tests cover fold behavior, nested skills, stale open sibling suppression, tool result placement, and notification hint semantics.
