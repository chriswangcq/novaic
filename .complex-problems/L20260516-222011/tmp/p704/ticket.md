# Foundational boundary residue remediation

## Problem Definition

P704 must remediate the active cleanup candidates discovered by P703 and verify boundary guard coverage. Current candidates:

1. `docs/runtime/tool-chain-dispatch.md` says `Cortex owns scope/context/sandbox`, which blurs Cortex orchestration with Sandboxd execution ownership.
2. `novaic-cortex/requirements.txt` says Redis is optional and default in-memory backend is safe, which contradicts current distributed scope-lock requirement and no-local-fallback policy.

## Proposed Solution

Patch both active residues with precise current-state wording. Then run focused scans and guard/tests to ensure no important boundary regression remains.

## Acceptance Criteria

- `docs/runtime/tool-chain-dispatch.md` distinguishes Cortex scope/context/shell orchestration from Sandboxd execution ownership.
- `novaic-cortex/requirements.txt` no longer claims Redis is optional or that an in-memory production backend is safe.
- Boundary guard/lint checks pass.
- Targeted stale scans show the patched claims are gone.
- Any remaining residual risk is recorded.

## Verification Plan

- Patch the two files.
- Run `python3 scripts/ci/lint_blob_workspace_boundary.py`.
- Run targeted `rg` scans for the retired phrases.
- Run syntax/static checks if touched files require them.

## Risks

- Requirements comments are not executable, but stale dependency comments can mislead deployment decisions.
- Runtime dispatch docs are active architecture docs, so wording should be exact rather than marketing-ish.

## Assumptions

- These are safe active-doc/comment patches and do not require compatibility preservation.
