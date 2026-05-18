# LogicalFS Sandbox VMuse Service Cleanup Ticket

## Problem Definition

Clean infrastructure/service residue in LogicalFS, Sandbox, and VMuse without mixing unrelated ownership boundaries.

## Proposed Solution

Split into separate children:

- LogicalFS public docs/metadata wording cleanup around live `/ro` and `/rw` authority.
- Sandbox unused filesystem helper deletion/relocation after confirming inactivity.
- VMuse stale FastMCP direct-media entry cleanup and focused tests.

## Acceptance Criteria

- LogicalFS docs/metadata emphasize live RO/RW file authority and avoid stale snapshot/view/patch-first wording.
- Unused Sandbox filesystem helper surface is deleted or relocated if inactive.
- VMuse no longer exposes stale FastMCP direct-media entry path.
- Focused tests pass for touched packages.

## Verification Plan

Inspect exact files first, split if needed, patch minimally, and run package-specific tests/lints.
