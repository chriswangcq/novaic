# Audit historical display and artifact manifest projection

## Problem Definition

Historical display outputs and shell-created artifacts should remain manifest/text-only in LLM history. They must not rehydrate old image bytes, re-inject stale screenshots, or turn artifact metadata into raw base64 text.

## Proposed Solution

Inspect Cortex projection and runtime history handling for historical display/artifact results. Verify tests that tool-output artifacts render as manifest text, old display steps use history projection, and historical image content does not create user image messages. Add or tighten tests if any stale-image reinjection branch is uncovered.

## Acceptance Criteria

- Historical artifact/display projection code paths are mapped.
- Tool-output artifacts render as manifest text with display access hints, not image content.
- Historical display steps use `history`, not `display_perception`.
- Historical image-like tool results do not create provider image messages.
- Focused tests pass.

## Verification Plan

Run Cortex tool output projection tests and runtime historical image injection guard tests. Include old-display-after-new-tool-block coverage from runtime step-ref tests.

## Risks

- Current display projection is intentionally allowed to create image input; tests must distinguish current from historical.
- Artifact manifest text should remain useful enough for the agent to decide whether to call `display` explicitly.

## Assumptions

- Current-round display provider media is covered by P185.
