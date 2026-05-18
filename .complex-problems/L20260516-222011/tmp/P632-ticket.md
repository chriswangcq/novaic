# Run Final LogicalFS Sandbox Fallback Guard

## Problem Definition

After cleanup work around direct materialization and root scratch, the repository still needs a guard against reintroducing old local sandbox/materialization semantics: direct workspace materialization, `novaic-cortex-sandbox-*` backing paths as contract, runtime-local shell fallback, or Blob-as-workspace authority.

## Proposed Solution

Run targeted static scans across the relevant repositories for materialization/fallback/sandbox/temp/blob-authority terms. Inspect remaining hits enough to classify them as current intended LogicalFS/sandbox service behavior, deleted/stale residue, lower-layer generic tests, or follow-up-worthy active risk. Run focused Cortex LogicalFS/workspace/sandbox boundary tests that prove the intended path still works.

## Acceptance Criteria

- Static scans are recorded for the requested terms.
- Every meaningful remaining hit is classified.
- Focused boundary tests pass.
- Any risky active fallback/materialization residue becomes a follow-up problem.

## Verification Plan

Use `rg` scans for `materialize`, `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/rw/scratch`, fallback terms, and Blob/workspace authority terms. Run focused Cortex tests around workspace, logical_fs, sandboxd wiring, runtime path abuse, and workspace paths. Run LogicalFS tests if lower-layer hits need validation.

## Risks

- `materialize` is an overloaded term: LogicalFS provider materialization may be intended while Cortex Workspace materialization is legacy.
- Historical docs/tests may contain old strings; classify rather than blindly edit.
- This guard may uncover broader architecture residue that should be split instead of one-go patched.

## Assumptions

- Root scratch cleanup is already closed by P631.
- The desired final shape is Cortex using LogicalFS/sandbox service boundaries, not direct local workspace materialization fallback.
