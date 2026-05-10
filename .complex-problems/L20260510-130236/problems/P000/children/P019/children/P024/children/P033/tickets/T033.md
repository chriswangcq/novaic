# Ticket: Tighten LogicalFS Boundary Guardrails

## Problem Definition

The boundary policy tests still allow old transitional Cortex live-file paths and object API patterns.

## Proposed Solution

Update `tests/blob_boundary_policy.py` and related guard tests so Cortex runtime cannot directly own Blob object APIs or old live authority files. Keep Blob object API allowance only in LogicalFS/Blob layers and docs that describe Blob itself.

## Acceptance Criteria

- No allowlist entry for `novaic_cortex/workspace_files.py`.
- No transitional `BlobCortexStore` policy snippets.
- Cortex runtime source remains blocked from `/v1/objects` direct access.
- Guardrail tests pass.

## Verification Plan

- Run `tests/test_blob_boundary_guard.py`.
- Run residue scans for old policy snippets.

## Risks

- Tests may scan too broad a doc set and catch intentionally historical roadmap notes; classify docs in P034.

## Assumptions

- Guardrails should protect active source and canonical tests, while docs cleanup is a separate child.
