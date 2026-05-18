# Ticket: implement direct Anthropic image conversion test

## Problem Definition

The provider adapter image contract still lacks direct unit-test proof. Static inspection is insufficient because an accidental future conversion change could flatten image bytes into text without being caught by log-redaction tests.

## Proposed Solution

Add a focused unit test in the LLM Factory test suite that instantiates the Anthropic provider adapter and verifies `_convert_content` converts an OpenAI-style image data URL block into Anthropic-native structured image content.

## Acceptance Criteria

- The new test asserts the converted content contains a `type=image` block.
- The new test asserts the converted block has `source.type=base64`, the expected media type, and the original base64 payload in `source.data`.
- The new test asserts no text block contains the base64 payload.
- Existing image redaction route tests pass together with the new provider conversion test.

## Verification Plan

Run focused `novaic-llm-factory` pytest tests for the provider conversion test and existing chat route image redaction tests.

## Risks

- The provider conversion method is currently private; the test may couple to the existing adapter implementation. That is acceptable here because the goal is to pin the exact adapter boundary contract.

## Assumptions

- No production behavior change should be required unless the test reveals the adapter does not preserve image payloads correctly.
