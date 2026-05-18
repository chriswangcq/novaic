# Ticket: audit provider image payload and log redaction contract

## Problem Definition

Runtime/Cortex may produce correct image content, but LLM provider adapters and Factory logging must preserve it as image payload while redacting image bytes in logs. A correct runtime request can still fail if the provider adapter flattens images to plain text or if logs expose base64.

## Proposed Solution

- Inspect LLM Factory contracts/provider adapters for OpenAI/Anthropic-style image content handling.
- Inspect Factory log redaction behavior for `data:image` and base64-source image payloads.
- Update tests or code if provider payloads are flattened or logs display raw image bytes.

## Acceptance Criteria

- Provider adapters pass image content through provider-native payload shapes.
- Factory log detail redaction replaces image bytes with bounded redaction markers.
- Focused tests prove both URL data image and base64-source image redaction.

## Verification Plan

- Run focused LLM Factory tests covering provider contracts and chat route redaction.
- Search provider/logging code for raw image/base64 text exposure.
- Patch if active provider/log paths leak image bytes.

## Risks

- Provider-native payloads may legitimately contain base64 in structured image fields; this ticket forbids leaking those bytes in logs or plain text message content, not the provider-required transport representation.

## Assumptions

- Runtime-level image block creation is covered by `P055`; this ticket focuses on Factory/provider adaptation.
