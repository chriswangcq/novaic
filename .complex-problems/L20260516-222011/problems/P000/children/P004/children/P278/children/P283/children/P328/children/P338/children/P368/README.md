# Child Problem: Cortex Archive Diagnostics Binding

## Problem

Cortex scope archive metadata must not record finalize reason or generation diagnostics for the wrong wake. The archive boundary should rely on explicit payload identity, not active lookup.

## Success Criteria

- Verify or fix `task_queue/handlers/cortex_handlers.py`, wake-finalize payload builders, and Cortex bridge calls.
- Tests prove stale or missing generation cannot archive.
- Tests prove valid archive records the intended reason/generation metadata.
- No direct archive path uses inferred active generation.
