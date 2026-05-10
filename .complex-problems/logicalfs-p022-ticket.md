# Move Blob Object Store Adapter Into LogicalFS

## Problem Definition

`BlobCortexStore` currently lives in `novaic-cortex` and is constructed by `WorkspaceRegistry`, so live workspace persistence still appears Cortex-owned. Blob object persistence should be a generic adapter below LogicalFS, while Cortex receives only the LogicalFS authority/file boundary.

## Proposed Solution

Add a generic Blob object-store adapter in `novaic-logicalfs`, update tests to cover it there, and remove the Cortex-owned `BlobCortexStore` live path. Update `WorkspaceRegistry` so it no longer imports or constructs `novaic_cortex.blob_store.BlobCortexStore`; it should use the LogicalFS-owned object adapter as the lower persistence primitive. Leave full Workspace constructor cutover to P023.

## Acceptance Criteria

- `novaic-logicalfs` owns the Blob object-store adapter implementation used beneath LogicalFS.
- `novaic-cortex/novaic_cortex/registry.py` no longer imports or constructs `BlobCortexStore`.
- `novaic-cortex/novaic_cortex/blob_store.py` is removed from active source or made unreachable from production imports.
- Blob object adapter tests live under LogicalFS and do not import Cortex.
- Existing Cortex and LogicalFS tests that cover affected paths pass.

## Verification Plan

- Add LogicalFS tests for Blob adapter put/get/list/move behavior using a mocked HTTP client.
- Update registry imports/construction and remove/update old Cortex Blob store tests.
- Run targeted tests for LogicalFS and Cortex registry/blob-boundary policy.
- Run residue scans for `BlobCortexStore` and `/v1/objects`.

## Risks

- Removing the old file can break docs or guardrail allowlists before P024 cleanup.
- Registry may still type itself around `CortexStore`; if so, P023 must complete the type boundary cleanup.

## Assumptions

- `BlobObjectStore` can implement the same async object-store method shape required by `StoreBackedLogicalFileAuthority`.
- Cortex cutover to a LogicalFS authority constructor remains P023.
