# Ticket: Delete Old Cortex Authority Source

## Problem Definition

Old production source still contains `CortexLogicalFileAuthority` and source comments that describe CortexStore as sitting below that old authority.

## Proposed Solution

Physically delete `workspace_files.py`, update source comments/docstrings in `store.py` and nearby source to describe object-store adapters below LogicalFS, then run source residue scans and relevant tests.

## Acceptance Criteria

- `workspace_files.py` is gone.
- Source no longer defines/imports `CortexLogicalFileAuthority` or `BlobCortexStore`.
- Source comments do not point future work back to the old authority.
- Relevant tests and source scans pass.

## Verification Plan

- Run `rg` scans over `novaic-cortex/novaic_cortex`.
- Run full Cortex tests or at least affected test suite if no runtime code changed beyond deletion/docs.

## Risks

- Hidden import of `workspace_files.py` may only appear at runtime; residue scan and full tests should catch it.

## Assumptions

- No compatibility shim is required.
