# Projection test branch inventory result

## Summary

Completed read-only projection test inventory. Most projection tests protect the new contract rather than legacy behavior. One stale test island was found: `novaic-cortex/tests/test_resolve_for_llm.py` tests a production helper that has no production callers and still asserts small-image base64 inline behavior. One missing test gap was found: Google/Gemini provider lacks a multimodal request preservation/conversion test.

## Inventory

| Test Area | Evidence | Classification | Reason |
| --- | --- | --- | --- |
| `resolve_for_llm` tests | `novaic-cortex/tests/test_resolve_for_llm.py:1-71` | stale test candidate | Tests unused production helper and explicitly asserts base64 inline images at `:10-18`. Should be removed with the stale helper. |
| Cortex parser accepts MCP image data/url | `novaic-cortex/tests/test_step_result_projection.py:9-45` | compatibility/active | Covers persisted/current display-style `_mcp_content` shapes. Should remain unless parser support is intentionally removed. |
| Cortex history truncation and display perception data URL | `test_step_result_projection.py:57-96` | active contract | Guards bounded history and explicit display perception. |
| `tool-output.v1` artifact manifest tests | `novaic-cortex/tests/test_tool_output_projection.py:47-71` | active contract | Protects manifest-only artifacts and avoids image inlining. |
| Shell durable payload ignores raw shell payload | `test_tool_output_projection.py:88-146` | active contract | Directly protects against shell media-like stdout becoming display media. |
| Display tool durable payload projection modes | `test_tool_output_projection.py:149-196` | active contract | Confirms history/current stay text-only while display perception can carry image. |
| Runtime generic/history image denial tests | `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:28-61` | active contract | Protects no image injection except explicit display perception. |
| Runtime legacy content/nested result denial tests | `test_no_historical_tool_image_injection.py:63-107` | defensive guard, not legacy endorsement | These tests intentionally assert old shapes are not treated as image projection contracts. Keep or rename to emphasize guard behavior. |
| Runtime display wrapper/media preservation tests | `test_no_historical_tool_image_injection.py:110-182` | active contract | Protects public placeholder plus durable image payload for immediate display perception. |
| Runtime active-stack-after-display ordering test | `test_no_historical_tool_image_injection.py:185-262` | active regression contract | Covers the exact system-message-after-display issue reported by the user. |
| Runtime non-display media-like tool denial | `test_no_historical_tool_image_injection.py:265-280` | active safety contract | Ensures shell/non-display tools cannot smuggle `_mcp_content` images. |
| Shell output contract tests | `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py:52-170` | active contract | Protects `tool-output.v1`, bounded text, durable raw payload, and no `_mcp_content` for shell. |
| Factory log/provider multimodal tests | `novaic-llm-factory/tests/test_chat_routes.py:148-291`, `novaic-llm-factory/tests/test_log_routes.py:79-119` | active contract | Protects log redaction, OpenAI preservation, and Anthropic conversion. |
| Google/Gemini request multimodal tests | only response conversion exists at `novaic-llm-factory/tests/test_chat_routes.py:294-317` | missing coverage | No test asserts Google provider preserves/converts `image_url` request content; matches production inventory gap. |

## Cleanup / Follow-up Candidates

- Remove `novaic-cortex/tests/test_resolve_for_llm.py` with the stale `resolve_for_llm` helper.
- Add Google/Gemini multimodal request conversion tests when fixing provider support.
- Consider renaming "legacy content array" / "nested result wrapper" tests to make clear they are negative safety guards, not old-contract support.

## Verification

Read-only inventory commands used:

```bash
rg -n "resolve_for_llm|legacy|nested|_mcp_content|display_perception|history_projection|tool-output\\.v1|image_url|base64|redact|GoogleProvider|Gemini|str\\(content\\)|placeholder|raw_shell_result" novaic-cortex/tests novaic-agent-runtime/tests novaic-llm-factory/tests -g'*.py'
nl -ba novaic-cortex/tests/test_resolve_for_llm.py | sed -n '1,120p'
nl -ba novaic-cortex/tests/test_step_result_projection.py | sed -n '1,115p'
nl -ba novaic-cortex/tests/test_tool_output_projection.py | sed -n '1,220p'
nl -ba novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py | sed -n '1,310p'
nl -ba novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py | sed -n '1,210p'
nl -ba novaic-llm-factory/tests/test_chat_routes.py | sed -n '130,330p'
nl -ba novaic-llm-factory/tests/test_log_routes.py | sed -n '1,140p'
```

## Code Changes

None. This ticket was inventory-only.
