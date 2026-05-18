# Runtime continuity and context.read residue classification

## Problem

Runtime still has context read, notification-hint, idempotency, or continuity-looking paths. These must be classified so safe side paths are not confused with provider-message authority, and stale paths do not survive as hidden fallback logic.

## Success Criteria

- `novaic-agent-runtime/task_queue/handlers/context_handlers.py`, `runtime_handlers.py`, and relevant bridge/context-read callers are mapped.
- Remaining `read_context`, `context.read`, continuity, cross-wake, or historical context paths are classified as active-safe, dead, or stale.
- Any active stale path that can influence LLM provider input is fixed or split.
- Focused tests or static guards covering the classification are identified and run.
