# Workspace step and payload normalization cleanup result

## Summary

P423 found the workspace step/payload normalization boundary already aligned with the pointer-oriented contract. Tool steps reject inline `result`, require an observation percept, require `payload_ref` when writing payloads, and externalized payloads are stored through Blob-backed manifests.

## Done

- Inspected `workspace.py` step/payload methods:
  - `write_payload`
  - `read_payload`
  - `normalize_step`
  - `write_step`
  - `write_step_projection`
- Ran a step/payload guard over workspace and focused tests.
- Ran focused workspace/payload/step projection tests.

## Verification

- Guard evidence:
  - `normalize_step()` raises on inline tool `result`.
  - `normalize_step()` raises when a tool step lacks an observation percept.
  - payload writing requires `payload_ref`.
  - large payload externalization requires a blob client.
  - payload manifest records source ref, blob ref, size, hash, and retention class.
- Focused tests:
  - `tests/test_workspace.py`
  - `tests/test_payload_inspection_api.py`
  - `tests/test_step_index_outcome.py`
  - `tests/test_step_result_projection.py`
  - `tests/test_tool_output_projection.py`
  - Result: `55 passed in 0.47s`.

## Known Gaps

No P423-specific workspace step/payload normalization gap was found. Archive semantics remain under P418, and API lifecycle/step read projection remains under P424.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p423/workspace-step-payload.inspect.txt`
- `.complex-problems/L20260516-222011/tmp/p423/workspace-step-payload-guard.txt`
