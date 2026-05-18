# Result: Display handler durable ImageRef tests inventoried

## Summary

Display handler durable payloads have direct regression coverage. Tests prove public display output removes inline image data, durable payload stores BlobRef `image_ref` and `display_files` metadata, and the durable contract does not depend on inline image bytes.

## Done

- Recorded scan output in `.complex-problems/L20260516-222011/tmp/p598/display-durable-scan.txt`.
- Scan command recorded:
  - `rg -n 'durable|image_ref|display_files|inline image|"data"|does_not_depend|placeholder' novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py -S`
  - `nl -ba ... | sed -n ...` slices for display handler and no-historical tests.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:65-120`, which checks fetched image data is redacted from public output and durable payload stores `image_ref` plus `display_files`.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:123-156`, which checks durable `image_ref` does not depend on inline image data when the image exceeds inline budget.
- Cited `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:167-212`, which checks `_ok` persists a reference rather than media bytes.

## Verification

- Focused test command:
  - `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py::test_display_fetches_blob_service_image_as_mcp_content novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py::test_display_durable_image_ref_does_not_depend_on_inline_image_data novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py::test_runtime_display_wrapper_persists_reference_not_media_bytes -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p598/display-durable-tests.txt`.
- Outcome: `3 passed in 0.05s`.

## Known Gaps

- None for display handler durable ImageRef coverage.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p598/display-durable-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p598/display-durable-tests.txt`
