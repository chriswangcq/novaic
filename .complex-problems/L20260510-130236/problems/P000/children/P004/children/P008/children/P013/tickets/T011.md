# Update Code-Adjacent Blob Boundary Language

## Problem Definition

Code docstrings and comments around registry/store/workspace still contain broad Blob-backed production wording. This can mislead future code generation into treating Blob object APIs as the live `RO` / `RW` authority.

## Proposed Solution

Update only code-adjacent language: registry docstrings/comments, store docstrings/comments, workspace authority comments, blob payload wording, and transitional adapter docstrings. Keep real adapter names and behavior unchanged.

## Acceptance Criteria

- No code comment claims Workspace live semantics are Blob-backed.
- `BlobCortexStore` is described as a transitional/internal persistence adapter where mentioned in code comments.
- Public/live Workspace authority comments point to LogicalFS/Cortex file authority.
- Runtime behavior remains unchanged except previously removed top-level adapter export.

## Verification Plan

- Run focused `rg` scans over `novaic-cortex/novaic_cortex`.
- Run the Blob boundary guardrail test.

## Risks

- Over-editing code while cleaning comments could accidentally change behavior.

## Assumptions

- This ticket does not remove `BlobCortexStore` itself.
