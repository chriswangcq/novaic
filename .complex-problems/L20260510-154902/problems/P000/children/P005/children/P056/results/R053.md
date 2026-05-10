# status usage cut to event projection

## Summary

Changed `context_status(include_usage=True)` to use `ContextEventReadModel` for projected stack, message count, token estimate, and usage ratio. The default `include_usage=False` path remains a cheap operational control-stack check via `_collect_active_stack`, explicitly documented as non-rendering/non-LLM usage.

## Done

- Updated `novaic_cortex/api.py` status usage path to load compact config and prepare via event projection.
- Removed `ContextEngine` from `context_status`.
- Added focused status test that creates event-authored root/wake/messages and verifies include-usage output comes from projection.
- Kept default status stack-only behavior intact and tested.

## Verification

- Focused status tests: `2 passed`.
- Static `context_status` section scan:
  - `ContextEngine: False`
  - `prepare_messages_for_llm: False`
  - `ContextEventReadModel: True`
  - `_collect_active_stack: True` only for documented default operational stack path.
- Full Cortex suite: `450 passed`.

## Residual Risk

- `_collect_active_stack` still exists for operational LIFO/status/error paths. P057 must classify or remove remaining DFS/control traversal residue.
