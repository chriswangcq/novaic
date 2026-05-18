# context.jsonl helper implementation map result

## Summary

Mapped all workspace `context.jsonl` helpers and fixed the same silent-corruption class found in step indexes: corrupt projection lines now raise instead of disappearing.

## Done

- `read_context`: `novaic-cortex/novaic_cortex/workspace.py:856-878`; materialized/debug projection reader, not source-of-truth by itself.
- `append_context`: `workspace.py:880-885`; single-message projection append.
- `append_context_projection`: `workspace.py:887-889`; event-projection wrapper around `append_context`.
- `append_context_batch`: `workspace.py:891-899`; batch projection append.
- `append_context_batch_projection`: `workspace.py:901-907`; event-projection wrapper around batch append.
- Changed `read_context` corrupt JSON handling from silent skip to `ValueError`.
- Added `test_read_context_rejects_corrupt_jsonl_projection`.

## Verification

- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_api_context_writes.py novaic-cortex/tests/test_context_event_read_model.py novaic-cortex/tests/test_context_event_projection.py`.
- Result: `38 passed in 0.34s`.

## Known Gaps

- Caller classification and active LLM prepare authority are sibling problems `P153` and `P154`; this result only maps helper behavior.

## Artifacts

- Modified `novaic-cortex/novaic_cortex/workspace.py`.
- Modified `novaic-cortex/tests/test_context_event_api_context_writes.py`.
