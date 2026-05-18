# Classify LogicalFS And Blob Authority Boundaries

## Problem Definition

P563 must determine whether Blob/Object APIs are staying below LogicalFS as cheap byte/object storage, or whether any code path lets Blob become a semantic RO/RW workspace authority bypass. `BlobObjectStore` was flagged by P552 and needs explicit classification.

## Proposed Solution

Run a focused, split-friendly inventory across LogicalFS, Cortex registry/store adapters, Blob service, and tests. Classify findings in small child problems:

- `BlobObjectStore` and Cortex registry/store adapter usage.
- LogicalFS object-store authority and key-prefix semantics.
- Blob service namespace/object API usage and whether it exposes realtime filesystem semantics.

Each child records exact scan commands, outputs, line slices, classification, and remediation candidates. The parent then rolls up any P554 cleanup items.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- `BlobObjectStore` is classified.
- Object APIs, namespace usage, and key-prefix usage are classified.
- Valid cheap object storage below LogicalFS is separated from invalid blob-as-realtime-filesystem semantics.
- Any high-confidence risky residue is forwarded to P554.

## Verification Plan

Use targeted `rg` scans and line-numbered slices over `novaic-logicalfs`, `novaic-cortex`, `novaic-blob-service`, and relevant tests. Check the parent only after child classifications and command manifests are complete.

## Risks

- Broad blob terms can produce false positives from payload/artifact paths; classify by authority boundary, not by keyword alone.
- `BlobObjectStore` may be intended if it is strictly a LogicalFS object adapter, so deletion must not be assumed before classification.

## Assumptions

- Blob is allowed as cheap byte/object storage and artifact delivery.
- LogicalFS should own realtime RO/RW semantics above Blob.
