# Result: Factory log request context boundary audited

## Summary

Factory logs are a stored LLM-call observability surface, not monitor preview state. Request bodies are produced from actual chat messages via `build_chat_log_snapshot`, and provider image bytes are redacted before persistence; the raw JSON tab renders the stored log bodies, not hidden monitor/tool payloads.

## Done

- Recorded scan output in `.complex-problems/L20260516-222011/tmp/p600/factory-log-boundary-scan.txt`.
- Scan command recorded:
  - `rg -n 'factory.?logs|Factory Logs|factory-log|llm.*log|request_body|response_body|Request Body|Response Body|raw JSON|raw_json|base64|image_url|image_ref|display_perception' -S . --glob '!**/.complex-problems/**' --glob '!**/.git/**' --glob '!**/node_modules/**'`
- Cited `novaic-llm-factory/factory/contracts.py:88-147`, where log snapshots recursively redact OpenAI `image_url` data URLs and Anthropic base64 image sources before JSON serialization.
- Cited `novaic-llm-factory/factory/routes/chat_routes.py:130-160`, where `request_body` is created from the chat request via `build_chat_log_snapshot`; provider execution still uses `request.messages` separately.
- Cited `novaic-llm-factory/factory/routes/log_routes.py:40-62` and `93-102`, where detail bodies are bounded for API responses.
- Cited `novaic-llm-factory/static/factory-logs.html:471-579`, where visual/raw tabs parse and render stored `request_body`/`response_body` with HTML escaping.
- Cited redaction tests in `novaic-llm-factory/tests/test_chat_routes.py:148-202` and `novaic-llm-factory/tests/test_log_routes.py:120-160`.

## Verification

- Focused test command:
  - `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-llm-factory python -m pytest novaic-llm-factory/tests/test_chat_routes.py::test_chat_log_snapshot_redacts_openai_image_url_data novaic-llm-factory/tests/test_chat_routes.py::test_chat_log_snapshot_redacts_anthropic_image_source_data novaic-llm-factory/tests/test_log_routes.py::test_log_detail_returns_redacted_multimodal_request_body -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p600/factory-log-boundary-tests.txt`.
- Outcome: `3 passed in 0.18s`.

## Known Gaps

- None for factory log request-context/raw JSON boundary.
- Raw JSON can legitimately show redacted provider request structure; that is observability of stored call records, not monitor preview or durable tool text.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p600/factory-log-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p600/factory-log-boundary-tests.txt`
