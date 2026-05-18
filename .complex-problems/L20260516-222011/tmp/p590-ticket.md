# Ticket: Resolve Current-Round Display ImageRefs In Runtime

## Summary

Teach runtime step-ref expansion to resolve Cortex `image_ref` display perception content through Blob Service and convert it into image MCP content before provider multimodal conversion.

## Problem Definition

Runtime display durable payloads now store BlobRef image refs, and Cortex display projection now preserves those refs. The LLM request path still needs to turn current-round display refs into actual image content. This must happen only for `display_perception`, not history, summaries, or non-display tools.

## Proposed Solution

Add an explicit runtime resolver in the step-ref expansion path. After `read_step_formatted(... projection="display_perception")`, parse the formatted MCP content, fetch `image_ref.file_url` from Blob Service with tenant headers, replace it with `{"type":"image","data":base64,"mimeType":...}`, and leave failures/oversized blobs as bounded text diagnostics.

## Acceptance Criteria

- `display_perception` image refs become image MCP content for current LLM calls.
- History/current non-display projections do not fetch or inject images.
- Blob Service dependency is explicit in runtime code and testable.
- Fetch failures produce bounded text diagnostics, not crashes or base64 leakage in history.
- Focused runtime expansion tests pass.

## Verification Plan

Run focused runtime step-ref expansion tests and multimodal tests covering image-ref resolution, historical non-resolution, and failure fallback.
