# P034 Result

## What Changed

- Clarified `novaic-agent-runtime/task_queue/tool_surface_policy.py` so migrated interface names are explicitly denylist/classification data, not active Runtime executors.
- Removed unused `CortexBridge.payload_*` helper methods from `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`.
- Renamed Cortex payload FastAPI handler functions to endpoint names while keeping route URLs stable:
  - `payload_read_endpoint`
  - `payload_search_endpoint`
  - `payload_summarize_endpoint`
  - `payload_qa_endpoint`
- Changed payload Factory `call_type` values from old direct-tool shaped names to `cortex_payload_summarize` / `cortex_payload_qa`.
- Changed shell reply-cap counter key from `im_reply` to `reply_action`.
- Changed media audio Factory `call_type` from `audio_qa` to `media_audio_qa`.
- Updated focused tests for the renamed endpoint/counter/call-type vocabulary.

## Verification

- `python3 -m py_compile novaic-agent-runtime/task_queue/tool_surface_policy.py novaic-agent-runtime/task_queue/utils/cortex_bridge.py novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/shell_capabilities.py`
- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_payload_inspection_api.py tests/test_pr67_wake_child_api.py tests/test_tool_schemas_limits.py`
  - 26 passed
- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/test_tool_surface_boundary.py tests/test_runtime_tool_path_contract.py`
  - 13 passed
- Focused scan over policy/API files now leaves direct-tool tokens only in the migrated-interface denylist in `tool_surface_policy.py`.

## Remaining Gap

This child only addressed policy/API vocabulary. Test fixture cleanup, activity projection legacy labeling, and final residue exception inventory remain in sibling problems.
