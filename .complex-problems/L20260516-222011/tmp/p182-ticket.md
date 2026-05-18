# Verify active stack plus current display media regression coverage

## Problem Definition

Current display media must still be projected as visual input when an active-stack system message follows the display tool result. P182 must prove this exact regression path and ensure historical display outputs remain text/manifest-only.

## Proposed Solution

Inspect display/media projection tests and source paths for the exact ordering case. Run focused runtime tests covering display projection, historical no-reinjection, shell/tool manifest-only output, and LLM preparation. Add or tighten tests if the exact active-stack-after-display scenario is not already covered.

## Acceptance Criteria

- A focused test exists for current display tool output followed by an active stack system message.
- That test proves the image is injected into provider messages as a visual input and the original tool message keeps a placeholder instead of raw media.
- Historical display messages remain history/text-only.
- Tests pass after any changes.

## Verification Plan

Run runtime unit tests for no historical image injection, display chat history, tool output contract, shell output contract, and runtime explicit LLM call contract.

## Risks

- If the existing test only checks role ordering but not actual image input content, a new assertion or test will be required.

## Assumptions

- P181 already identified the active stack injection point; P182 focuses on regression coverage and media projection behavior.
