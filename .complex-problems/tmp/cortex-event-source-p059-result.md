# Old-data no-compat reset behavior implemented

## Summary

Implemented explicit reset-required behavior for non-empty root paths with missing/empty ContextEvent streams. Active prepare/status usage no longer silently returns empty context or falls back to DFS for legacy-only roots.

## Done

- Added `ContextEventReadModelResetRequired`.
- `ContextEventReadModel.prepare()` now raises reset-required for non-empty root paths with no events.
- `context_prepare_for_llm` and `context_status(include_usage=True)` translate reset-required into HTTP 409 with `error_code=context_event_reset_required`.
- Added read-model and API tests for legacy-only roots.

## Verification

- Focused no-compat/read-source tests: `7 passed`.
- Full Cortex suite: `455 passed`.

## Residual Risk

- Callers need to handle HTTP 409 by resetting/recreating the context stream. That is intentional per no-compat requirement.
