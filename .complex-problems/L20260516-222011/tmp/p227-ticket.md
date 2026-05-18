# Verify active-stack system ordering around current display media

## Problem Definition

A system Active Skill Stack message may follow a display tool result in prepared context. We need to ensure current display media is still inserted as a provider image user message and the display tool result text is sanitized.

## Proposed Solution

Inspect and run the targeted runtime test that models assistant display tool call, display tool result, then following system message. Confirm prepared messages contain the image user message and sanitized tool result.

## Acceptance Criteria

- A targeted test covers display result followed by active-stack/system message.
- Prepared messages include the generated image user message.
- Tool result content contains placeholder/sanitized image metadata, not base64.
- Test passes.

## Verification Plan

Run the specific runtime test file and cite the assertion lines for ordering and sanitization.

## Risks

- If provider APIs require image message to be after every system message, this test only proves current in-repo contract. That would need a separate design change, not silent mutation here.

## Assumptions

- The current intended contract is: assistant tool call, sanitized tool result, generated user image message, then Active Skill Stack system message.
