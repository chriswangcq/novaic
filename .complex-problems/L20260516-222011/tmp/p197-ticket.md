# Audit factory multimodal log detail serialization

## Problem Definition

Factory log/detail serialization must make multimodal calls debuggable without dumping raw image bytes. Request bodies should preserve message structure and redact data-url/base64 media, not collapse to `{}` or render media as giant text blobs.

## Proposed Solution

Inspect Factory logging contracts, chat route log writes, log route reads, and UI-facing response shape. Verify existing tests for `build_chat_log_snapshot` and add/adjust tests if detail routes can return `{}` or if multimodal bodies lose structure. Confirm the log snapshot redacts OpenAI `image_url` and Anthropic `image.source.data`.

## Acceptance Criteria

- Factory log snapshot and detail route code paths are mapped.
- Multimodal request logs preserve structure and redact image bytes.
- Log detail APIs return request/response bodies rather than empty `{}` for populated logs.
- Focused log/detail tests pass.

## Verification Plan

Run Factory chat/log route tests. Add a focused log route test if current tests only cover snapshot helper and not the detail API response.

## Risks

- UI display bugs can be frontend-only even if API is correct; this ticket focuses on backend serialization/API.
- Redaction must preserve enough metadata to debug without exposing huge binary payloads.

## Assumptions

- Provider adapter payload preservation is covered by P196.
