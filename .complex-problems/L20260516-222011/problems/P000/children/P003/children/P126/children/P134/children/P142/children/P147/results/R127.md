# step index metadata audit result

## Summary

The step index now preserves compact metadata more completely and no longer silently swallows corrupt JSONL lines. I fixed two metadata edge cases and added corruption failure coverage.

## Done

- Mapped index construction at `novaic-cortex/novaic_cortex/workspace.py:756-779`.
- Mapped index reading at `novaic-cortex/novaic_cortex/workspace.py:794-812`.
- Changed `duration_ms` indexing from truthy-only to explicit `is not None`, so `0` remains visible.
- Added artifact detection for `observation.artifacts`, not only top-level `artifacts`.
- Changed corrupt `_index.jsonl` handling from silent `pass` to `ValueError` with path and line number.
- Added tests for zero duration, observation artifacts, and corrupt index JSONL.

## Verification

- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_workspace.py novaic-cortex/tests/test_step_index_outcome.py novaic-cortex/tests/test_context_event_api_steps_write.py`.
- Result: `36 passed in 0.46s`.

## Known Gaps

- This result does not audit whether all active API call sites populate `step_ref`/`payload_ref`; that remains under `P148`.

## Artifacts

- Modified `novaic-cortex/novaic_cortex/workspace.py`.
- Modified `novaic-cortex/tests/test_step_index_outcome.py`.
