# Clean Stale Blob Workspace Ownership Language

## Problem Definition

P006 found comments and docs still saying or implying Blob owns live Cortex Workspace semantics. That wording is dangerous because future generated code may treat Blob object APIs as an acceptable live `RO` / `RW` authority.

## Proposed Solution

Split the cleanup into code comments/docstrings, architecture/reference docs, and a final residual scan. The intended wording is: Blob owns cheap bytes and transitional object persistence internals; LogicalFS/Cortex file authority owns live `RO` / `RW` semantics.

## Acceptance Criteria

- Code comments/docstrings around `WorkspaceRegistry`, `CortexStore`, `BlobCortexStore`, and Workspace authority are narrowed.
- Architecture/reference docs no longer claim Blob is the live `RO` / `RW` authority.
- Transitional Blob object API terms remain only where they clearly describe the adapter/internal persistence layer.
- A final scan records any intentional remaining terms.

## Verification Plan

- Use focused `rg` scans before and after edits.
- Run targeted docs/source residual scans.
- Run relevant Cortex guardrail tests after text/code-comment cleanup.

## Risks

- Removing all mentions of Blob object APIs would erase useful reference documentation for the transitional adapter.
- Leaving broad "Blob-backed Workspace" wording would preserve the exact future-agent hazard this ticket is meant to remove.

## Assumptions

- This ticket should not remove the transitional `BlobCortexStore` adapter itself; it only fixes misleading ownership language.
