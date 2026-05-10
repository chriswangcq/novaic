# prepare_for_llm cut to event projection

## Summary

Changed `/v1/context/prepare_for_llm` to assemble LLM context through `ContextEventReadModel` instead of the DFS `ContextEngine`. Also tightened projection semantics so a newly started wake suppresses stale open wake stack/messages, preserving the current active wake as the prepared context source.

## Done

- Updated `novaic_cortex/api.py` so `context_prepare_for_llm` uses `ContextEventReadModel`.
- Removed render/control drift comparison from the prepare endpoint because messages and stack now come from the same event projection.
- Added API-compatible wake stack normalization in the read model (`skill_name="wake"` for wake frames).
- Updated API prepare tests to create scopes/messages through event-writing APIs instead of direct workspace projection helpers.
- Added projection coverage for stale wake suppression.

## Verification

- Focused related tests: `33 passed`.
- Static endpoint scan:
  - `ContextEngine: False`
  - `_collect_active_stack: False`
  - `stack.drift_detected: False`
- Full Cortex suite: `449 passed`.

## Residual Risk

- `context_status(include_usage=True)` still uses `ContextEngine`; this is intentionally left for P056.
- Some explicit DFS/ContextEngine tests remain as legacy/debug coverage until P057 cleanup.
