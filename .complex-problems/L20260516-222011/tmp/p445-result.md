# Cortex context endpoint and test cleanup result

## Summary

Clarified Cortex materialized context endpoint/test wording. `/v1/context/read|append|batch` paths remain unchanged, but their docs/tests now state they read/write `context.jsonl` materialized projections, not LLM prepare history.

## Done

- Added endpoint docstrings to `context_read`, `context_append`, and `context_batch`.
- Renamed Cortex tests to include projection/materialization language.
- Preserved endpoint behavior and public paths.

## Verification

Focused Cortex tests:

```text
27 passed in 0.49s
```

Wording scan artifact confirms:

- `/v1/context/read` reads materialized `context.jsonl` projection and is not LLM prepare.
- `/v1/context/append` appends a ContextEvent and materializes projection.
- `/v1/context/batch` batch appends ContextEvents and materializes projection.
- Tests now use `emits_event_and_materializes_projection`, `context_projection`, and `read_context_projection` wording.

## Known Gaps

- None for Cortex endpoint/test wording. Parent P439 still needs aggregate result/check.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
- `novaic-cortex/tests/test_pr67_wake_child_api.py`
- `.complex-problems/L20260516-222011/tmp/p445/cortex-context-endpoint-focused-pytest.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p445/api-materialized-context-after-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p445/cortex-context-wording-after.txt`
