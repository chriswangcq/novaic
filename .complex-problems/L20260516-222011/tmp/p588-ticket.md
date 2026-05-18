# Ticket: Rewrite Runtime Display Durable Payload

## Summary

Change runtime display durable payload construction so it stores a BlobRef-backed media reference instead of copying base64 image bytes.

## Problem Definition

Runtime `display` currently fetches Blob bytes, builds image MCP content, then `_display_durable_payload` copies the full image item into durable `llm_content`. This makes Cortex step payloads carry base64 and defeats the BlobRef boundary.

## Proposed Solution

Update `_display_durable_payload` to derive a durable media-reference shape from display result metadata (`file_url`, `mime_type`, `size`) and public text. Keep public output sanitization intact. Rewrite the focused runtime display test to assert durable payload references BlobRefs and contains no `data` field.

## Acceptance Criteria

- Durable display payload contains `image_ref` or equivalent BlobRef-backed reference.
- Durable display payload contains no image `data` base64.
- Public display output still strips image data.
- Focused runtime display handler tests pass.

## Verification Plan

Run `pytest novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py` and targeted `rg` checks around durable display payload base64 expectations.
