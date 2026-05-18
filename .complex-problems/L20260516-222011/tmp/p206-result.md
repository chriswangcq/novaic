# Factory/provider/log projection branch inventory result

## Summary

Completed a read-only factory/provider/log projection inventory. OpenAI-compatible requests preserve structured `image_url` content; Anthropic converts OpenAI-style image URLs to native base64 image blocks; log snapshots redact base64 while preserving structured shape. One likely active gap was found: Google/Gemini provider conversion stringifies list content and does not preserve multimodal `image_url` parts.

## Inventory

| Branch | Evidence | Classification | Reason |
| --- | --- | --- | --- |
| Runtime factory client preserves messages verbatim | `novaic-agent-runtime/task_queue/factory_client.py:52-72` | active | Sends `messages` directly in JSON payload; no serialization/stringification of structured content before Factory. |
| Factory chat route logs request body through explicit snapshot contract | `novaic-llm-factory/factory/routes/chat_routes.py:130-160` | active | Uses `build_chat_log_snapshot` for request body when logging is enabled. |
| Factory provider request keeps original messages in `ProviderChatInput` | `chat_routes.py:181-190` | active | Provider receives structured `messages=request.messages`. |
| OpenAI provider preserves structured content | `novaic-llm-factory/factory/providers.py:81-98` | active | Payload uses `request.messages` directly, so OpenAI-compatible image content remains structured. |
| Anthropic provider converts OpenAI-style `image_url` to native image source | `providers.py:201-252`, `:320-343` | active | Converts `data:image/...;base64,...` into Anthropic `{type: image, source: {type: base64}}`. |
| Anthropic non-data image URLs become text placeholders | `providers.py:241-244` | defensive compatibility | Avoids unsupported remote-image URLs becoming broken provider payloads. |
| Google/Gemini provider user list content stringification | `providers.py:360-377` | active gap candidate | If runtime sends OpenAI-style multimodal user content to Google, this path turns list content into text via `str(content)` instead of native Gemini inline data/parts. |
| Google/Gemini tool response stringification | `providers.py:400-419` | active/limited | Tool content is stringified into `functionResponse.result`; likely okay for text-only tool results, but it would not preserve multimodal content if ever routed there. |
| Log redacts OpenAI `image_url` data URLs | `novaic-llm-factory/factory/contracts.py:80-111`, `:136-147` | active | Keeps `image_url` shape while replacing base64 payload with redaction marker. |
| Log redacts Anthropic image source data | `contracts.py:113-128` | active | Replaces native base64 `source.data` with redaction marker. |
| Log list query omits large bodies; detail fetch includes full/redacted bodies | `novaic-llm-factory/factory/db.py:590-608`, `novaic-llm-factory/factory/routes/log_routes.py:36-70` | active | Summary list avoids large body columns; detail route returns specific stored body by id. |

## Cleanup / Fix Candidates

- Strong fix candidate: Google/Gemini provider content conversion should preserve multimodal content instead of stringifying list content. This is not stale deletion; it is a missing provider adapter path.
- No stale branch found in OpenAI/Anthropic/log redaction paths. They are distinct boundary responsibilities and should not be merged just because all mention `image`/`base64`.

## Verification

Read-only inventory commands used:

```bash
rg -n "messages|image_url|base64|redact|request_body|response_body|OpenAIProvider|content|multimodal|raw_request|log" novaic-agent-runtime/task_queue/factory_client.py novaic-llm-factory -g'*.py'
nl -ba novaic-agent-runtime/task_queue/factory_client.py | sed -n '1,220p'
nl -ba novaic-llm-factory/factory/contracts.py | sed -n '1,190p'
nl -ba novaic-llm-factory/factory/providers.py | sed -n '60,260p'
nl -ba novaic-llm-factory/factory/providers.py | sed -n '300,430p'
nl -ba novaic-llm-factory/factory/routes/chat_routes.py | sed -n '120,230p'
nl -ba novaic-llm-factory/factory/db.py | sed -n '590,615p'
nl -ba novaic-llm-factory/factory/routes/log_routes.py | sed -n '36,75p'
```

## Code Changes

None. This ticket was inventory-only.
