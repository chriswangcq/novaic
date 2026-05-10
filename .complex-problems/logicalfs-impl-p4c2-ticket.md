# Update Architecture Docs For LogicalFS Authority Boundary

## Problem Definition

Several architecture/reference docs still describe Cortex Workspace as Blob-backed or say Cortex uses Blob Service object APIs as its production backend. That wording conflicts with the intended boundary: LogicalFS/Cortex file authority owns live `RO` / `RW`; Blob owns cheap bytes and transitional persistence adapter internals.

## Proposed Solution

Update the known stale docs from the P006/P008 scans. Preserve useful Blob reference details for artifacts, display/download bytes, payload refs, and the transitional object adapter, but remove or narrow claims that Blob is the live Workspace authority.

## Acceptance Criteria

- Architecture docs no longer claim Blob is the live `RO` / `RW` authority.
- `BlobCortexStore` and `/v1/objects` docs are framed as transitional adapter/internal details.
- Blob reference docs continue to describe cheap `blob://` byte flows.
- A follow-up verification scan can classify remaining terms precisely.

## Verification Plan

- Run focused `rg` scans over `docs/architecture`, `docs/cortex`, and `docs/reference/blob-service.md`.
- Review changed snippets manually.

## Risks

- Over-removing Blob object API docs could lose needed reference material for current transitional internals.

## Assumptions

- This ticket updates docs only.
