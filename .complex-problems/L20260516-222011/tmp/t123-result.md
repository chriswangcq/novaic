# ContextEvent stream and read model split result

## Summary

Closed the ContextEvent stream/read-model split by completing its three child slices: append-only store, pure projection, and read-model budget boundary. One improvement was made: added a read-model empty-root-path regression test.

## Done

- Completed P138 / R120:
  - Mapped `ContextEventStore` event path, read behavior, append/idempotency behavior, explicit clock/id provider boundary, and root initialization.
  - Verified `novaic-cortex/tests/test_context_event_store.py`.
- Completed P139 / R121:
  - Mapped pure `project_context_events` snapshot shape, replay invariants, event handlers, folded summaries, stale scope suppression, notification hints, and tool result `step_ref`/`payload_ref` behavior.
  - Verified `novaic-cortex/tests/test_context_event_projection.py`.
- Completed P140 / R122:
  - Mapped `ContextEventReadModel.prepare`, reset-required behavior, budget compaction, token/usage calculation, and top-first stack normalization.
  - Added `test_event_read_model_empty_root_path_returns_closed_empty_context`.
  - Verified focused read-model tests and the combined ContextEvent bundle.

## Verification

- Store:

```text
16 passed in 0.12s
```

- Projection:

```text
29 passed in 0.07s
```

- Read model:

```text
4 passed in 0.09s
```

- Combined ContextEvent bundle:

```text
49 passed in 0.16s
```

## Known Gaps

- None for this split scope.
- Workspace materialized projections, runtime prepare-context handoff, tool/display formatting, and provider media boundaries remain intentionally covered by sibling problems under P126/P003.

## Artifacts

- Child result R120: ContextEvent append-only store audit.
- Child result R121: ContextEvent pure projection audit.
- Child result R122: ContextEvent read model and budget boundary audit.
- Test changed: `novaic-cortex/tests/test_context_event_read_model.py`.
