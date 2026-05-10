# Add Blob Boundary Source Scanner Test

## Problem Definition

The Blob/LogicalFS boundary policy exists, but the repository does not yet enforce it. Without an automated source scanner, future edits could reintroduce direct Blob object-store authority in Workspace/API/runtime/sandbox code while tests still pass.

## Proposed Solution

Add a focused Cortex test that imports `tests/blob_boundary_policy.py`, scans Cortex runtime source and sandbox-service runtime source, and fails if forbidden direct object authority patterns appear outside the explicit allowlist. Keep the scanner narrow: source code only, not docs, and allow legitimate Blob byte paths.

## Acceptance Criteria

- The test scans `novaic-cortex/novaic_cortex/**/*.py` and `novaic-sandbox-service/sandbox_service/**/*.py`.
- The test fails on forbidden `BlobCortexStore` or `/v1/objects` patterns outside allowed transitional object authority files.
- The test allows `blob://` and `/v1/blobs` in allowed byte-flow files.
- The targeted test command passes in the current tree.

## Verification Plan

- Run the new targeted pytest file.
- Run it from `novaic-cortex` with the same PYTHONPATH style used by the Cortex suite.

## Risks

- The scanner may accidentally inspect test/policy fixtures and fail on synthetic strings.
- The scanner may under-scan sibling services if paths are resolved relative to the wrong root.

## Assumptions

- P012 will separately prove synthetic negative behavior; this ticket only implements the scanner and verifies current-tree pass.
