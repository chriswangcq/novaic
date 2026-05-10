# Ticket: Audit Active Shell Path And Host Substrate

## Problem Definition

Map current shell execution and host capabilities before implementation.

## Proposed Solution

Use read-only code search and host checks to document the current path, old logic, and impossible/available mount substrates.

## Acceptance Criteria

- Active code entry points are listed.
- Old temp projection symbols are listed.
- Host mount/FUSE/proot/unshare support is checked.
- Implementation constraints are recorded.

## Verification Plan

- `rg` evidence for code paths.
- Python import/host checks.
- File pointers to relevant implementation and tests.

## Risks

- Dirty worktree may include already-modified code; audit must describe current state only.

## Assumptions

- No writes outside ledger result file are needed for this audit.
