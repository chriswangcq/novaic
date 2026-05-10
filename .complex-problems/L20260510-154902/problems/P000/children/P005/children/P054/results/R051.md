# Event projection read adapter implemented

## Summary

Built the Phase 4 read-path adapter that prepares LLM context from the authoritative ContextEvent stream instead of DFS materialized artifacts. The adapter is not wired into API handlers yet; it is a narrow boundary for the next cutover tickets.

## Done

- Added `novaic_cortex.context_event_read_model.ContextEventReadModel`.
- Added `ContextEventPreparedContext` with prepared messages, top-first stack, estimated tokens, usage ratio, applied sequence, projection snapshot, and `status()`.
- Read path is explicit: workspace + root scope path + optional compact config/token counter/event store.
- Adapter reads `ContextEventStore`, projects with `project_context_events`, then applies existing `budget_compact` and token counting.
- Added focused tests for notification rendering, assistant tool-call/tool-result pairing, closed skill summary projection, projected stack/status, and budget compaction.

## Verification

- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_read_model.py` -> `2 passed`.
- Static scan on adapter/test found no `ContextEngine`, DFS reader, or materialized artifact dependency.
- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests` -> `448 passed`.

## Residual Risk

- API handlers still use the old DFS `ContextEngine`; that is intentionally deferred to P055/P056.
- The adapter returns stack in API/control order (current top first). Later cutover tickets must avoid double-reversing it.
