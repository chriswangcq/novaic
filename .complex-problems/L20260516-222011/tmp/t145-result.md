# Cortex API materialization call-site map result

## Summary

Mapped the active Cortex API call sites that either append authoritative ContextEvents, materialize workspace projections, or expose explicit payload/step retrieval. No new divergent active write path was found: the remaining projection writes are intentionally paired with event writes for context append/batch and tool step write, while read/preview/payload endpoints are explicit retrieval surfaces.

## Done

- Classified `novaic-cortex/novaic_cortex/api.py:840` `/v1/context/read` as a materialized `context.jsonl` projection read/debug surface, not an authoritative LLM context source.
- Classified `novaic-cortex/novaic_cortex/api.py:853` `/v1/context/append` as an authoritative `_append_context_message_event(...)` write paired with `ws.append_context_projection(...)` under a per-scope lock.
- Classified `novaic-cortex/novaic_cortex/api.py:876` `/v1/context/batch` as per-message authoritative event append paired with `ws.append_context_batch_projection(...)` under a per-scope lock.
- Classified `novaic-cortex/novaic_cortex/api.py:925` `/v1/context/prepare_for_llm` as the authoritative ContextEvent read model path, with no `context.jsonl` projection dependency.
- Classified `novaic-cortex/novaic_cortex/api.py:1526` `/v1/steps/write` as an authoritative `ToolStepRecorded` event write paired with `ws.write_step_projection(...)` for durable debug/history projection.
- Classified `novaic-cortex/novaic_cortex/api.py:1573`, `:1580`, and `:1591` step list/read/index endpoints as explicit materialized projection retrieval surfaces.
- Classified `novaic-cortex/novaic_cortex/api.py:1776` and `:1815` formatted/preview endpoints as explicit payload-backed step retrieval surfaces.
- Classified `novaic-cortex/novaic_cortex/api.py:1885` and `:1912` payload read/search endpoints as bounded explicit payload retrieval surfaces.
- Confirmed workspace projection writes flow through `novaic-cortex/novaic_cortex/workspace.py:787` `write_step_projection`, which delegates to the normalized `write_step` path and now records zero durations and observation artifacts correctly.

## Verification

- Source evidence collected with `rg` and line-numbered `nl -ba` slices over `novaic-cortex/novaic_cortex/api.py` and `novaic-cortex/novaic_cortex/workspace.py`.
- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_api_context_writes.py novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_payload_inspection_api.py novaic-cortex/tests/test_context_event_api_contract.py`.
- Result: `20 passed`.

## Known Gaps

- `/v1/context/read` remains a potentially confusing projection-read API name. It is not a current correctness blocker because runtime LLM context guards now target `prepare_for_llm`, but the naming should stay visible for future API cleanup.
- No duplicate active materialization write path was found in this ticket. Broader repo-level old-code cleanup remains governed by parent ledger problems rather than this call-site map ticket.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_payload_inspection_api.py`
- `novaic-cortex/tests/test_context_event_api_contract.py`
