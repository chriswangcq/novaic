# Cortex prepare_for_llm read-model authority result

## Summary

Cortex `/v1/context/prepare_for_llm` is wired to `ContextEventReadModel.prepare()`, which reads the ContextEvent stream and pure projection; it does not call `read_context` or parse `context.jsonl`.

## Done

- Mapped endpoint at `novaic-cortex/novaic_cortex/api.py:925-946`.
- Mapped read-model authority at `novaic-cortex/novaic_cortex/context_event_read_model.py:66-117`.
- Verified `prepare()` reads events through `ContextEventStore.read_events` and `project_context_events`.
- Source scan found `read_context` in `api.py` only under `/v1/context/read`, not `prepare_for_llm`.

## Verification

- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_read_model.py novaic-cortex/tests/test_context_event_projection.py`.
- Result: `33 passed in 0.09s`.

## Known Gaps

- Runtime caller/LLM assembly authority is sibling `P157`.
- Static guard coverage is sibling `P158`.

## Artifacts

- No code changes for this leaf.
