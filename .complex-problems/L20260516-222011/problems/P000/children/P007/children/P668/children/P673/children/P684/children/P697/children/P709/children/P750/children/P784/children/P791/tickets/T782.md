# LogicalFS Public Contract Wording Ticket

## Problem Definition

LogicalFS public docs/metadata still over-emphasize snapshot/view/patch terms and should clearly present LogicalFS as live `/ro` and `/rw` file-operation authority beneath Cortex semantics.

## Proposed Solution

Inspect and patch LogicalFS public contract surfaces, likely:

- `novaic-logicalfs/README.md`
- `novaic-logicalfs/pyproject.toml`
- `novaic-logicalfs/logicalfs/__init__.py`
- `novaic-logicalfs/logicalfs/contracts.py`

Keep wording business-agnostic and avoid claiming Cortex semantics ownership.

## Acceptance Criteria

- Public wording emphasizes live RO/RW file operations/view authority.
- Snapshot/patch wording is retained only as implementation mechanics, not the primary identity.
- Cortex semantics ownership is not claimed by LogicalFS.
- Focused LogicalFS tests or import checks pass.

## Verification Plan

Run targeted `rg` scans before/after and focused LogicalFS tests.
