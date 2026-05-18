# Ticket: add focused provider image adapter tests

## Problem Definition

The provider image payload contract currently relies on static inspection plus logging redaction tests. That is not enough to prove the active Anthropic adapter preserves image content as provider-native structured image blocks.

## Proposed Solution

Add a focused LLM Factory unit test that constructs an OpenAI-style multimodal content list containing a `data:image/...;base64,...` image URL, passes it through the Anthropic provider conversion helper, and asserts the output is a structured Anthropic image block rather than text.

## Acceptance Criteria

- The new test proves data URL image content converts to `{type: "image", source: {type: "base64", media_type, data}}`.
- The new test proves the converted block is not represented as a text block containing base64.
- Existing Factory chat-route log redaction tests continue to pass.

## Verification Plan

Run focused LLM Factory tests covering the provider conversion test and existing redaction tests.

## Risks

- The test may need to call a private helper because provider conversion is currently implemented inside the provider adapter class.

## Assumptions

- This follow-up only covers provider adapter contract proof; runtime display and Cortex image projection were handled by previous child tickets.
