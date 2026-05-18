# Wake-finalize payload positive generation

## Problem

`wake_finalize` payload construction must not silently convert missing `session_generation` to `0`. A missing or non-positive generation should become an explicit validation failure before a `session.ended` effect is published.

## Success Criteria

- Remove `session_generation or 0` fallback from `task_queue/sagas/wake_finalize.py`.
- Ensure `_build_session_ended_payload(...)` requires positive generation and preserves scope/finalize reason/remaining stack.
- Add tests for valid positive generation and missing/zero generation rejection.
- Run focused tests and source guards proving the wake-finalize payload builder no longer emits zero-generation session-ended payloads.
