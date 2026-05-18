# Ticket: Inventory Cortex Projection BlobRef No-Inline Tests

## Problem Definition

Cortex step-result projection must preserve BlobRef media references and avoid turning shell/display artifact manifests into inline base64, except for explicit already-inline data URL compatibility.

## Proposed Solution

Scan Cortex projection tests for `tool-output.v1`, `display_files`, `image_ref`, BlobRef, and no-inline assertions. Run focused Cortex projection tests that prove BlobRef artifacts remain references.

## Acceptance Criteria

- Exact scans and focused test commands are recorded.
- Tests proving `tool-output.v1` artifact images do not become inline media are cited.
- Tests proving display BlobRefs project as `image_ref` for explicit display perception are cited.
- Any missing direct coverage is recorded as a follow-up.

## Verification Plan

Run focused tests from `novaic-cortex/tests/test_tool_output_projection.py` and `novaic-cortex/tests/test_step_result_projection.py`.

## Risks

- Legacy data URL tests may still intentionally inline image data; the result must separate that compatibility path from BlobRef artifact behavior.

## Assumptions

- Runtime resolves BlobRef `image_ref` later for current display perception; Cortex projection should not fetch Blob data itself.
