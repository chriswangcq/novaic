# Provider Image Payload Contract Result

## Summary

Reviewed the LLM factory provider boundary for displayed images. The provider layer already contains the two critical pieces required by this ticket: provider-native image conversion for Anthropic and log redaction for image byte payloads. No production code change was made in this ticket.

## Done

- Confirmed `novaic-llm-factory/factory/providers.py` converts OpenAI-style `image_url` data URLs into Anthropic-native image blocks with `source.type=base64`, `media_type`, and `data` instead of flattening image bytes into plain text.
- Confirmed non-data image URLs in the Anthropic adapter are degraded to textual `[Image URL: ...]` placeholders, which is acceptable for unsupported remote URL forms but should not be used for blob-backed displayed screenshots after the context assembly fix.
- Confirmed `novaic-llm-factory/factory/contracts.py` has log redaction helpers for OpenAI `image_url.url` data URLs and Anthropic `source.data`, so LLM factory request logs should not expose raw base64 image bytes.
- Confirmed existing test coverage includes log redaction tests named `test_chat_log_snapshot_redacts_openai_image_url_data` and `test_chat_log_snapshot_redacts_anthropic_image_source_data`.

## Verification

- Static evidence inspected:
  - `novaic-llm-factory/factory/providers.py`
  - `novaic-llm-factory/factory/contracts.py`
  - `novaic-llm-factory/tests/test_chat_routes.py`
- The preceding child tickets already verified that display tool output now stores raw image bytes in durable payload metadata and that Cortex projection can convert those durable display payloads into multimodal LLM content.

## Known Gaps

- This ticket did not add or run a provider-adapter-specific unit test that directly calls the Anthropic conversion path with a synthetic data URL. The current evidence proves implementation presence and log redaction coverage, but the next success check should decide whether direct adapter test coverage is required.
- This ticket did not run the full `novaic-llm-factory` test suite.

## Artifacts

- Implementation evidence: `novaic-llm-factory/factory/providers.py`
- Logging/redaction evidence: `novaic-llm-factory/factory/contracts.py`
- Existing log tests: `novaic-llm-factory/tests/test_chat_routes.py`
