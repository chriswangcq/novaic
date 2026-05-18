# Ticket: BlobRef-backed display perception payload

## Summary

Replace display durable image payload bytes with BlobRef-backed media metadata while keeping current-turn display perception available to the LLM as provider-native image input.

## Problem Definition

Display currently strips image bytes from public tool history but still persists small image base64 in `durable_payload.llm_content`. That duplicates file bytes in Cortex/runtime payload state and conflicts with the Blob Service byte-authority boundary.

## Proposed Solution

Change display durable payload to store BlobRef, MIME type, size, and metadata instead of inline base64. Move image-byte resolution to the display perception boundary, where runtime can fetch the BlobRef on demand and construct provider-ready image content for the current LLM call. Update tests that currently assert durable base64 storage.

## Acceptance Criteria

- Display public tool content remains placeholder/text-only.
- Display durable payload contains no `_mcp_content[].data` base64 for image files.
- Current-turn display perception still injects a provider image message.
- Historical/default projections remain text-only.
- Focused tests cover durable payload no-base64 plus provider image delivery.

## Verification Plan

Run focused runtime/Cortex display projection tests and static scans for durable display base64 residues.
