# Ticket: Inventory Durable Shell and Display Base64-Absence Tests

## Problem Definition

Durable shell/display outputs must avoid embedding large visual base64. Shell-visible screenshot output should be a BlobRef manifest, and display durable payload should store `image_ref` metadata instead of inline image bytes.

## Proposed Solution

Scan shell capability tests, display tool handler tests, and Cortex projection tests for artifact-manifest and no-base64 assertions. Run the focused tests that prove durable output uses BlobRefs and omits inline `data`.

## Acceptance Criteria

- Exact scans for base64/data-url assertions are recorded.
- Shell screenshot or equivalent CLI output has cited BlobRef artifact-manifest test coverage.
- Display durable payload has cited `image_ref`/no-`data` test coverage.
- Any missing direct coverage is recorded as a follow-up.

## Verification Plan

Run focused tests for shell capabilities Blob contract, display durable payload generation, and Cortex BlobRef projection.

## Risks

- Shell and display contracts live in different packages; the result must cite both and avoid treating one side as proof for the other.

## Assumptions

- The target contract is BlobRef manifest durability; provider-bound base64 is allowed only after current display perception resolves BlobRef at the LLM-call boundary.
