# P585 scan command manifest

## Commands

- `rg -n "display|display_perception|llm_content|display_files|image_ref|_display_durable_payload|_display_content_for_llm|expand_step_ref_to_content|process_multimodal|read_formatted|Blob" novaic-agent-runtime/task_queue novaic-agent-runtime/tests novaic-cortex/novaic_cortex novaic-cortex/tests | head -220`
- `sed -n '118,170p' novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `sed -n '340,430p' novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `sed -n '1,250p' novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `sed -n '140,250p' novaic-cortex/novaic_cortex/step_result_projection.py`
- `sed -n '60,115p' novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p585/call-path-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p585/runtime-path-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p585/cortex-path-slices.txt`

## Boundary

This ticket only mapped the BlobRef-backed display perception call path. It did not change runtime code, Cortex code, tests, or deployment state.
