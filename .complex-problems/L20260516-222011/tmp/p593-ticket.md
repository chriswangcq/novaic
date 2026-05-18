# Ticket: Inventory Current Display Image Injection Tests

## Problem Definition

The active display-perception path must be protected by tests: when a current-round `display` step returns a BlobRef image reference, runtime must fetch the Blob and pass image MCP content into the provider request.

## Proposed Solution

Use `rg` to find display-perception and image-ref tests, inspect the relevant slices, and run the focused runtime tests that prove projection selection and BlobRef resolution.

## Acceptance Criteria

- The scan commands and focused test commands are recorded.
- At least one cited test proves current-round display selects `display_perception`.
- At least one cited test proves `image_ref` resolves to provider image content.
- Any missing coverage is recorded as a follow-up instead of hand-waved.

## Verification Plan

Run the focused runtime tests around `prepare_llm_call_without_retry`, step-result resolution, and no-historical image injection. Preserve any unrelated failures as explicit residual risk.

## Risks

- A test may verify the helper in isolation but not the full active LLM-call path; the result must distinguish direct versus indirect coverage.

## Assumptions

- Current-round display perception is expected to be the only path that resolves BlobRefs into image content for provider calls.
