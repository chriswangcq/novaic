# ContextEvent stream and read model map

## Problem

The ContextEvent stream is intended to be the authoritative cross-wake source for LLM context, but the exact write/read/projection chain must be verified from code and tests.

## Success Criteria

- `context_event_store.py`, `context_event_projection.py`, and `context_event_read_model.py` are mapped with active entrypoints and output shapes.
- The relationship between event sequence, root scope, projected messages, folded summaries, and active stack snapshot is documented.
- Existing tests covering replay order, skill stack, notifications, and tool results are identified and run.
- Any discovered stale or duplicate event projection path is flagged for cleanup or split into a follow-up.
