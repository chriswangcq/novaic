# Cortex finalize mutation identity guards

## Problem

Cortex-facing finalize or scope-end handlers must not close or archive a newer wake/skill stack from a stale finalize task. Identify and enforce expected wake scope/session generation checks before Cortex mutation where the handler mutates state.

## Success Criteria

- Inspect `task_queue/handlers/cortex_handlers.py`, related bridge code, and tests.
- Verify scope/generation identity is checked before `scope_end`, stack archive, input append, or message acknowledgement.
- Add tests for missing/stale scope and generation if a mutating path lacks coverage.
- If Cortex mutation is structurally keyed by scope path rather than session generation, document why that is safe or add the missing check.
