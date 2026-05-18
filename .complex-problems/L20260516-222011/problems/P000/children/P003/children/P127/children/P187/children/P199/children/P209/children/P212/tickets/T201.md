# Bound generic unknown-dict projection fallback

## Problem Definition

`parse_tool_result` currently serializes unknown dict payloads directly into text. This avoids image projection, but it can still inject very large JSON/base64-like strings into LLM context because formatted step reads do not always pass a text limit.

## Proposed Solution

Retain the unknown-dict fallback as diagnostic text, but make it explicitly bounded and labeled. Add regression tests proving unknown dicts are text-only and large payloads are truncated before formatter-level projection.

## Acceptance Criteria

- Unknown dict fallback cannot emit image/display files.
- Unknown dict fallback has an internal maximum text size.
- The fallback text is labeled as an unknown tool result rather than silently pretending to be normal output.
- Focused Cortex projection tests pass.

## Verification Plan

Patch `parse_tool_result` fallback, add/adjust tests in Cortex projection tests, and rerun focused projection tests.

## Risks

- Very detailed unknown diagnostic payloads may be truncated; that is acceptable because full raw payload remains available through payload inspection.

## Assumptions

- Unknown dict fallback is for diagnostics only, not a first-class business contract.
