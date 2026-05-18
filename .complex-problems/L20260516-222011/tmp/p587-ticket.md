# Ticket: Final Verify Display No-Base64 Durability And Image Delivery

## Summary

Perform final verification for the BlobRef-backed display perception contract after implementation.

## Problem Definition

The implementation children are closed, but the full display contract must be verified as a whole: persisted durable payloads must remain base64-free, current display perception must still deliver image content to the provider request, and history must remain text/reference-only.

## Proposed Solution

Run consolidated focused test commands and static searches across runtime and Cortex. Inspect changed code paths and record any remaining gaps or unrelated failures separately.

## Acceptance Criteria

- Consolidated focused tests pass.
- Static search shows no active durable display base64 persistence.
- Provider request path still contains image input for current display perception.
- Historical replay path does not contain image input or base64 fixture.
- Any unrelated failures are named with exact boundary.

## Verification Plan

Use focused pytest commands, targeted `rg` scans, and code-diff review.
