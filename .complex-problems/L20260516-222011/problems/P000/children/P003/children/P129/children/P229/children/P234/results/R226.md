# Result: combined large shell/display projection boundary audited

## Summary

The combined large-output regression boundary is covered. Shell output remains bounded terminal text with raw stdout only in durable payload. Display image data is allowed only through current `display_perception` structured image conversion, while tool text/history uses placeholders. A combined focused runtime test set passed.

## Done

- Searched runtime code/tests for `data:image`, `_mcp_content`, base64, raw shell diagnostics, and projection markers.
- Confirmed suspicious base64/image references are limited to intended display-perception conversion, display durable payload tests, user-content comments, and assertions that shell text does not include image data.
- Ran combined focused tests for shell output contract, no historical image injection, and step-ref context expansion.

## Verification

- Search evidence: `data:image` appears in multimodal conversion/test assertions where current display perception creates structured image content, not default shell/history text.
- Search evidence: `raw_shell_result` appears only in tests asserting it is absent from public diagnostics.
- Search evidence: `user_content.py` comments explicitly state attachments are not inserted as base64 and require tools to inspect.
- Test command: `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`.
- Test result: `29 passed in 0.10s`.
- Supporting closed evidence: `P237`/`R220` for shell, `P238`/`R221` for display/media, and `P233`/`R225` for default context expansion.

## Known Gaps

- No blocking gap for this combined projection boundary.
- CLI command-specific contract coverage remains under `P230`.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
