# Audit runtime-to-factory multimodal request preservation

## Problem Definition

Runtime prepares LLM messages with provider-shaped multimodal content. The runtime transport/client must send these messages to LLM Factory as structured JSON arrays, not stringify them into plain text or discard image fields.

## Proposed Solution

Inspect runtime LLM call contracts, transport/client code, and tests around `prepare_llm_call` and factory request execution. Verify that a prepared OpenAI-style `image_url` message remains structured in the request payload. Add a focused test if existing tests stop at `PreparedLLMCall` and do not cover transport serialization.

## Acceptance Criteria

- Runtime LLM transport/request builder is mapped.
- Structured `image_url` content is preserved in the request sent to LLM Factory.
- Base64 image bytes do not appear in ordinary text content fields.
- Focused runtime tests pass.

## Verification Plan

Search for the runtime factory client and LLM call request schemas. Run focused runtime LLM contract tests. Add a regression that passes a prepared image message through the runtime request builder/client boundary and inspects the outbound JSON body.

## Risks

- Tests may mock the factory call too high-level and miss JSON serialization behavior.
- This ticket does not validate Factory's downstream provider adapter; that is P195.

## Assumptions

- `prepare_llm_call` already produces the image message, covered by P193.
