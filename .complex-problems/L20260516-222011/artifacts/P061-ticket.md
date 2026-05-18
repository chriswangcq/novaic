# Ticket: add media-like shell stdout regression test

## Problem Definition

Existing runtime/Cortex tests cover large generic stdout, but the observed failure involved screenshot-like base64 payloads. A regression test should simulate media-like stdout so future changes cannot accidentally treat shell output as image/display content.

## Proposed Solution

Add focused test coverage around shell output and Cortex projection using JPEG-like base64 text. Assert the LLM-facing public shell content is bounded terminal text, contains truncation diagnostics, and does not produce display/image projection content.

## Acceptance Criteria

- Test simulates large `/9j/`-style base64 stdout.
- Public shell observation is bounded and marked truncated at the shell-result diagnostic layer.
- Cortex projection of the durable shell payload does not create display files or image blocks.
- Focused runtime and Cortex tests pass.

## Verification Plan

Run focused runtime shell output tests and Cortex tool projection tests after adding the regression coverage.

## Risks

- Base64-like text is still text if printed by shell; the test should not assert it disappears completely, only that it is bounded and not reclassified as media.

## Assumptions

- Durable raw stdout may retain the full base64-like text for explicit RO/payload inspection.
