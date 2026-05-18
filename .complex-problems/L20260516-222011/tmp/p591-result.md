# Display perception cleanup and regression audit result

## Summary

Completed the display perception cleanup pass. Focused runtime, Cortex, multimodal, factory-client, and shell/blob contract tests now pass for the new contract. Targeted searches found no remaining active durable-base64 expectations.

## Verification

- Display chain focused tests:
  - `PYTHONPATH="/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime:/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-cortex:${PYTHONPATH:-}" python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_resolves_current_display_image_ref novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_does_not_resolve_history_image_ref novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_image_ref_fetch_failure_becomes_text novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py::test_expand_messages_for_llm_uses_display_projection_only_for_display_tool novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py -q`
  - Passed: `41 passed in 0.09s`.
- Related boundary tests:
  - `PYTHONPATH="/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime:/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-cortex:${PYTHONPATH:-}" python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py novaic-agent-runtime/tests/test_tool_surface_boundary.py novaic-agent-runtime/tests/test_runtime_tool_path_contract.py novaic-cortex/tests/test_shell_capabilities_blob_contract.py -q`
  - Passed: `19 passed in 1.35s`.
- Search artifact:
  - `.complex-problems/L20260516-222011/tmp/p591/display-contract-search.txt`

## Search Findings

- No matches for the suspicious durable/base64 query:
  - `durable_payload.*data`
  - `llm_content.*data`
  - `["durable_payload"].*["data"]`
  - `durable.*_mcp_content.*data`
- Remaining `YWJjMTIz` fixture matches are legitimate:
  - direct multimodal conversion tests,
  - provider request image tests,
  - assertions that public/durable/history text does not contain the fixture,
  - legacy data-URL compatibility tests in Cortex.

## Boundary Note

A broad run of the full `test_pr71_no_tool_retry_context_cleanup.py` file still has unrelated `session_generation` failures in non-display tests. Those failures predate and sit outside the display perception contract; they should be handled by a separate session-generation cleanup problem if the overall ledger selects it.

## Residual Risk

No display-specific stale durable-base64 residue was found in the checked surface. End-to-end live smoke with actual Blob Service/runtime service is still outside this local unit cleanup ticket.
