# No generic tool image injection check

## Status

success

## Result IDs

- R000

## Evidence

- Runtime expanded tool messages now carry an internal `_projection`.
- `process_multimodal_messages()` only extracts images for `_projection == "display_perception"`.
- Tests prove generic and historical tool images do not create user image messages.
- Tests prove explicit display perception still creates a user image message and strips `_projection`.

## Criteria Map

- Generic tool/tool_result messages no longer trigger image extraction: satisfied.
- Only messages marked as `display_perception` may be converted into provider-visible image user messages: satisfied.
- Runtime step-ref expansion marks projection mode and removes that internal marker before provider delivery: satisfied.
- Tests prove historical/generic tool image content is not injected and explicit display perception still works: satisfied.

## Execution Map

- Added transient projection marker in step-ref expansion.
- Gated multimodal extraction in context processing.
- Added focused tests and ran adjacent Runtime/Cortex tests.

## Stress Test

- A tool message with `_mcp_content` image but no projection stays a tool message only.
- A historical `display` tool message with image content stays a tool message only.
- A current explicit `display_perception` message produces a user image message and keeps tool content text-only.

## Residual Risk

- No residual risk for generic image injection. Helper deletion/resource-first display cleanup remains in later phases.
