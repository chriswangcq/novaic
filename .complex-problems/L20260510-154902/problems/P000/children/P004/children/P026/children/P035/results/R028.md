# Normalize tool step payloads before event emission result

## Summary

Implemented a reusable `Workspace.normalize_step(scope_path, step)` boundary so tool step validation and inline payload externalization can be performed before emitting `ToolStepRecorded` events. `Workspace.write_step` now consumes the same normalized shape, keeping file writes and upcoming event writes aligned.

## Done

- Added `Workspace.normalize_step` with the existing tool-step validation rules:
  - invalid step IDs are rejected;
  - tool steps cannot store inline `result`;
  - tool steps require an observation percept;
  - inline `payload` is externalized through `write_payload`;
  - the resulting `payload_ref` is mirrored into the observation.
- Changed `Workspace.write_step` to call `normalize_step` first and then append the step JSON and `_index.jsonl` entry.
- Made normalization non-mutating by deep-copying the caller-provided step before any payload/observation changes.
- Added tests proving:
  - direct `normalize_step` externalizes payload without mutating the input step;
  - `write_step` also preserves the caller input while still writing the normalized durable step;
  - existing payload/index behavior is preserved.

## Evidence

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_step_index_outcome.py`
- Targeted tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_step_index_outcome.py tests/test_workspace.py -q` → `23 passed`
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `443 passed`

## Residual Risk

- This ticket intentionally did not wire `/v1/steps/write` to `ToolStepRecorded`; that is the next child ticket.
- `normalize_step` still performs payload-store side effects because durable event emission needs the final payload ref. That matches the existing `write_step` ordering and is acceptable for this transitional write-path cutover.
