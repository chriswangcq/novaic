# T571 Result: Provider Request Serialization And Multimodal Projection Inventory

## Summary

Provider request serialization is aligned with the intended multimodal contract. Shell stays text-only, current-round display perception can produce a provider-native image message, history replay remains text-only, the runtime client preserves structured image content, and the LLM Factory service adapters preserve or convert image blocks appropriately. No P554 remediation is forwarded from this ticket.

## Scope

Audited the runtime-to-factory request projection and the LLM Factory provider adapters for multimodal image handling, with special attention to the recent failure mode where screenshot base64 appeared as textual tool content in the LLM request.

## Evidence

- Runtime prepares provider-ready requests through `LLMCallInput.prepare_llm_call`: expand step refs, sanitize, then `process_multimodal_messages`; see `novaic-agent-runtime/task_queue/contracts/llm_call.py:124-146`.
- The multimodal projection gate is narrow: only tool messages tagged `_projection == "display_perception"` may produce image messages; shell and historical tool results remain text receipts; see `novaic-agent-runtime/task_queue/utils/context.py:183-284` and `novaic-agent-runtime/task_queue/utils/multimodal.py:1-5`.
- OpenAI projection uses structured content with `{"type":"image_url","image_url":{"url":"data:<mime>;base64,<data>"}}`, not a text field; Anthropic projection uses native `{"type":"image","source":{"type":"base64",...}}`; see `novaic-agent-runtime/task_queue/utils/multimodal.py:58-110`.
- The display tool payload is converted to a bounded text-only tool receipt plus a following user image message; base64 is removed from the tool result text; see `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:48-90` and `:190-209`.
- Ordering is explicitly tested: the injected user image message appears before the following active-stack/system message; see `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:212-289`.
- History replay is explicitly tested: shell manifest and historical display results do not re-inject images and do not carry base64 text; see `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:291-458`.
- `FactoryLLMClient` posts the already-structured `messages` unchanged to `/v1/chat/completions`; see `novaic-agent-runtime/task_queue/factory_client.py:52-72`.
- The runtime factory-client unit test verifies structured `image_url` survives the client boundary and that base64 is absent from text fields; see `novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py:49-78`.
- LLM Factory chat route passes `request.messages` unchanged into `ProviderChatInput`; see `novaic-llm-factory/factory/routes/chat_routes.py:181-190`.
- OpenAI-compatible provider forwards `request.messages` unchanged as provider JSON; see `novaic-llm-factory/factory/providers.py:81-98`.
- Anthropic provider converts OpenAI-style data-url `image_url` blocks into Anthropic native image blocks; see `novaic-llm-factory/factory/providers.py:201-244` and `:320-343`.
- Google provider converts OpenAI-style data-url `image_url` blocks into Gemini `inlineData`; see `novaic-llm-factory/factory/providers.py:360-422`.
- Factory log snapshots redact OpenAI `image_url` data URLs and Anthropic base64 image source data before storing request bodies; see `novaic-llm-factory/factory/contracts.py:80-147` and tests in `novaic-llm-factory/tests/test_chat_routes.py:148-202`.
- Factory provider tests cover OpenAI preservation, Anthropic conversion, and Google conversion; see `novaic-llm-factory/tests/test_chat_routes.py:205-360`.

## Result

The current intended request projection is coherent:

- Shell returns terminal text only.
- A current-round `display` perception result may become a provider-native image input.
- The tool result itself is text-only and bounded.
- Runtime history replay does not revive image bytes.
- Runtime client and LLM Factory provider adapters preserve/convert structured image blocks instead of treating base64 as ordinary text.
- Factory logs redact image bytes when body logging is enabled.

No P554 remediation item is forwarded from this ticket.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p579/provider-serialization-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p579/provider-serialization-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p579/llm-factory-provider-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p579/llm-factory-provider-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p579/scan-command-manifest.md`
