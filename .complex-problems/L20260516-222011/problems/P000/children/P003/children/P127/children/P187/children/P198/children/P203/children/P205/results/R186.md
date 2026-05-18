# Runtime projection branch inventory result

## Summary

Completed a read-only runtime projection inventory. Runtime now has a clear active boundary: Cortex step refs are expanded through explicit projection modes, shell output is bounded terminal text plus durable raw payload, and only current `display_perception` tool messages can become provider-native image messages. No stale runtime production branch was proven in this inventory, but several compatibility branches should be kept intentionally or reviewed in later test cleanup.

## Inventory

| Branch | Evidence | Classification | Reason |
| --- | --- | --- | --- |
| Step-ref expansion requires Cortex bridge identity and `tool_call_id` | `novaic-agent-runtime/task_queue/utils/step_result_client.py:12-42`, `:166-212` | active | This is the live boundary that replaces raw tool message content with Cortex-formatted projections just before LLM call. |
| Current-vs-history projection selection | `step_result_client.py:119-139` | active | Old rounds return `history`; current display returns `display_perception`; current non-display returns `current_tool_result`. |
| Latest tool call fallback for missing `_round_id` | `step_result_client.py:85-98`, `:128-132` | compatibility/active | Needed for messages without explicit round metadata while still avoiding old display reinjection. Tests cover this. |
| `_projection` internal marker retained through sanitize | `novaic-agent-runtime/task_queue/utils/context.py:76-92` | active | Internal handoff marker is preserved until multimodal conversion, then stripped before provider request. |
| Tool result ordering and missing tool placeholders | `context.py:98-180` | active/defensive | Required for provider API ordering; not projection-specific but affects tool-result validity. |
| Non-display tool messages cannot inject media | `context.py:217-222` | active safety branch | If `_projection` is not `display_perception`, runtime appends text-only tool message and skips media extraction. |
| Explicit display perception image injection | `context.py:224-252`; `novaic-agent-runtime/task_queue/utils/multimodal.py:12-72`, `:75-101` | active | Only this path converts display `_mcp_content` image data to OpenAI/Anthropic image content. |
| Display tool public history sanitization | `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:118-139` | active | Public tool content replaces image bytes with placeholders. |
| Display durable payload retains true image bytes for immediate perception | `tool_handlers.py:142-164`, `:257-263`, `:362-422` | active | The durable payload stores `llm_content` with image data so current display can be projected once; public history remains sanitized. |
| Shell terminal text projection | `tool_handlers.py:167-242`, `:288-320` | active | Shell returns bounded stdout/stderr text and stores raw result under durable payload, preventing huge terminal output in model context while keeping full data in Cortex. |
| Generic unstructured executor result sanitization | `tool_handlers.py:50-115` | defensive compatibility | Unknown tool dicts are JSON-serialized after recursively omitting image `data`. This is a safety fallback, not preferred new contract. |
| User content attachment descriptions | `novaic-agent-runtime/task_queue/utils/user_content.py:30-59` | active | User uploads are described and require explicit `display(file_url=...)`; base64 is not injected automatically. |

## Cleanup Candidates

- No runtime production branch is clearly stale from this inventory alone.
- Review candidate: `context.py:271-272` keeps old pure-string user message compatibility. This is likely harmless and active for normal text messages, but the comment says "兼容旧格式"; test cleanup can ensure it is not preserving a stale structured attachment shape.
- Review candidate: generic unstructured executor fallback in `tool_handlers.py:50-115` should stay as a safety net only if all direct CLI tools already emit `tool-output.v1` or display contract. Downstream cleanup should verify no normal active tool relies on this fallback.

## Verification

Read-only inventory commands used:

```bash
rg -n "expand_messages_for_llm|process_multimodal_messages|_projection|display_perception|current_tool_result|history|image_url|_placeholder|data:image|base64|tool-output\\.v1|manifest_only|stdout_truncated|_shell_result" novaic-agent-runtime/task_queue novaic-agent-runtime/tests -g'*.py'
rg -n "step_result|projection|multimodal|display" novaic-agent-runtime/task_queue -g'*.py'
nl -ba novaic-agent-runtime/task_queue/utils/step_result_client.py | sed -n '1,260p'
nl -ba novaic-agent-runtime/task_queue/utils/context.py | sed -n '1,290p'
nl -ba novaic-agent-runtime/task_queue/utils/multimodal.py | sed -n '1,170p'
nl -ba novaic-agent-runtime/task_queue/handlers/tool_handlers.py | sed -n '1,440p'
```

## Code Changes

None. This ticket was inventory-only.
