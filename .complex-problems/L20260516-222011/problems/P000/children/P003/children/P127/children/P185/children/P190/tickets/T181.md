# Audit provider media adapter conversion

## Problem Definition

After runtime context assembly creates provider-visible multimodal messages, the final LLM Factory/provider request must preserve image/media content in the provider-supported schema. It must not stringify image messages, drop media fields, or move base64 into plain text.

## Proposed Solution

Trace prepared runtime messages into the final LLM client/factory request builder and provider adapter code. Verify how OpenAI-compatible and any other supported providers serialize multimodal content. Add or tighten tests that assert image content appears as provider media fields and raw base64 does not appear in ordinary text fields.

## Acceptance Criteria

- Provider adapter/request builder code path is mapped.
- OpenAI-compatible image messages are preserved as `image_url` content items, not flattened into text.
- Anthropic or other supported provider image messages are either preserved correctly or explicitly outside active runtime scope.
- Raw base64 does not appear in text-only fields.
- Focused provider/request serialization tests pass.

## Verification Plan

Search and inspect LLM client, factory client, request logging, and provider adapter tests. Run focused tests for LLM call preparation and provider request serialization. Add a regression test if current coverage only checks prepared messages but not the actual request sent to the factory/provider.

## Risks

- The runtime may send already-provider-shaped messages to LLM Factory, while Factory may do another conversion layer; both boundaries must be distinguished.
- LLM Factory logs may display raw request JSON; this ticket should judge actual request structure, not UI rendering alone.

## Assumptions

- Runtime projection and active-stack preservation are covered by P188/P189.
