# ToolOutputV1 substrate implemented

## Summary

Implemented the Phase 1 pure output-contract substrate without changing existing Runtime tool execution behavior. The new module defines `ToolOutputV1`, artifact/event manifests, diagnostics, and pure helper constructors with deterministic truncation and validation.

## Done

- Added `novaic-agent-runtime/task_queue/tool_output.py`.
- Added `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`.
- Implemented:
  - `ToolOutputV1`
  - `ArtifactManifest`
  - `ToolEventManifest`
  - `ToolDiagnostics`
  - `artifact_manifest`
  - `event_manifest`
  - `tool_text`
  - `tool_error`
- Kept constructors pure:
  - no clock reads;
  - no UUID generation;
  - no env/filesystem/db/network access;
  - caller supplies all identity/time/source metadata explicitly.
- Kept current Runtime `_ok()` / executor behavior untouched.

## Verification

- `cd novaic-agent-runtime && python -m pytest tests/unit/task_queue/test_tool_output_contract.py -q`
  - Passed: `7 passed in 0.04s`
- `cd novaic-agent-runtime && python -m pytest tests/test_tool_surface_boundary.py -q`
  - Passed: `4 passed in 0.05s`
- `cd novaic-agent-runtime && python -m pytest tests/test_runtime_tool_path_contract.py tests/test_llm_prompt_contract.py tests/test_runtime_explicit_contracts.py -q`
  - Passed: `18 passed in 0.11s`
- Existing dirty Runtime files from earlier work remain present and were not modified by this phase. This phase added:
  - `task_queue/tool_output.py`
  - `tests/unit/task_queue/test_tool_output_contract.py`

## Known Gaps

- `_ok()` does not yet normalize executor outputs to `ToolOutputV1`; planned for a later phase.
- Cortex does not yet parse `ToolOutputV1`; planned for Phase 2.
- Display/device/shell producers do not yet emit `ToolOutputV1`; planned for later phases.

## Artifacts

- `novaic-agent-runtime/task_queue/tool_output.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`
