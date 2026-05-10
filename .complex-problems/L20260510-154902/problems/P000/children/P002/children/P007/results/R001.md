# ContextEvent schema result

## Summary

Implemented the pure ContextEvent schema and validation layer for Cortex. The new code is deliberately independent of workspace IO, clocks, generated IDs, environment reads, and endpoint integration.

## Done

- Added `novaic-cortex/novaic_cortex/context_events.py`.
- Defined `CONTEXT_EVENT_SCHEMA_VERSION`, `CONTEXT_EVENT_TYPES`, `ContextEventError`, `ContextEvent`, `build_stream_id`, and stable JSON helpers.
- Added validation for required strings, schema version, positive sequence, valid event type, optional non-empty idempotency key, object payload, and stream/root suffix consistency.
- Added deterministic `to_dict`, `to_json_line`, `canonical_semantic_body`, and `canonical_semantic_json` helpers.
- Added `novaic-cortex/tests/test_context_event_model.py` with 18 focused tests.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_model.py -q` passed: 18 passed.
- Static `rg` over the new domain module found no hidden `uuid`, `time.`, `os.environ`, `Workspace`, `read_text`, `write_text`, `_sys_`, `context.jsonl`, `summary.md`, or `steps/_index` usage in `context_events.py`.
- A naked local pytest run without the sibling dependency path failed during import because existing package initialization requires `logicalfs` and `sandbox_sdk`; rerunning with the sibling repo paths succeeded.

## Known Gaps

- Storage append/read is not implemented in P007; it is tracked by P008 and P009.
- Existing write/read endpoints are not cut over; that remains tracked by P004 and P005.

## Artifacts

- `novaic-cortex/novaic_cortex/context_events.py`
- `novaic-cortex/tests/test_context_event_model.py`
