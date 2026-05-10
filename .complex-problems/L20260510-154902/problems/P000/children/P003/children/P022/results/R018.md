# Projection replay watermark implemented

## Summary

Implemented explicit replay watermark and sequence validation in the pure ContextEvent projector. Projection now exposes stream id, first seq, applied seq, and root scope id, and rejects malformed replay order instead of silently accepting corrupted event streams.

## Done

- Extended `ContextProjectionSnapshot` with:
  - `stream_id`;
  - `first_seq`;
  - existing `root_scope_id`;
  - existing `applied_seq`.
- Added replay-order validation in `project_context_events`:
  - first event must start at seq `1`;
  - all events must share the same `stream_id`;
  - all events must share the same `root_scope_id`;
  - event seq must be contiguous and in caller-provided order.
- Added tests for:
  - empty deterministic snapshot shape;
  - valid stream watermark;
  - first seq not starting at 1;
  - mixed stream id;
  - duplicate seq;
  - seq gap;
  - out-of-order first event;
  - mixed root stream rejection.

## Verification

- Focused ContextEvent tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_projection.py tests/test_context_event_model.py tests/test_context_event_store.py -q`
  - Result: `68 passed in 0.12s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `423 passed in 0.70s`
- Static projector dependency scan returned no matches for Workspace/file/legacy DFS/payload/env/time/id patterns.

## Residual Risk

- No endpoint/read-path integration was done in this follow-up; that remains owned by Phase 4.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`
