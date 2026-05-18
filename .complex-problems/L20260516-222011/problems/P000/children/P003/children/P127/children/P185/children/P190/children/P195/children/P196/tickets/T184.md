# Audit factory provider request adapter media preservation

## Problem Definition

Factory provider adapters must preserve structured image content in provider API requests. OpenAI-compatible `image_url` items should remain structured and raw base64 must not be copied into plain text fields.

## Proposed Solution

Locate Factory service code and provider adapter modules. Inspect request pass-through/conversion for chat completions. Verify existing tests or add a focused adapter test that sends a message with `content: [{"type":"image_url", ...}]` and captures the provider request payload.

## Acceptance Criteria

- Factory provider adapter/client modules are mapped.
- OpenAI-compatible `image_url` content survives to the provider request.
- Raw base64 does not appear in text fields.
- Focused provider adapter tests pass.

## Verification Plan

Use `rg` to locate Factory chat completion handler and OpenAI-compatible client. Run focused Factory tests. Add a test with a fake provider transport if current tests do not capture outbound provider JSON.

## Risks

- The Factory code may live in a sibling package; this ticket must avoid changing unrelated service boundaries.
- Provider routing may support multiple adapters; this ticket should cover the active OpenAI-compatible route used by the current model.

## Assumptions

- Runtime has already preserved structured image content when calling Factory, covered by P194.
