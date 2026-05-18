# Run Final RW Scratch Residue Scan

## Problem Definition

After multiple cleanup steps, stale root `/rw/scratch` strings could still exist in source or tests and mislead future agents into treating root scratch as canonical. A fresh scan must classify every remaining hit.

## Proposed Solution

Run targeted `rg` scans across `novaic-cortex` and `novaic-logicalfs` for `/rw/scratch`, `rw/scratch`, `RW_SCRATCH`, and `/rw/subagents`. Record the raw scan output, then classify each remaining root `/rw/scratch` hit as a negative guard, lower-layer generic test, or follow-up-worthy residue.

## Acceptance Criteria

- Scan commands and outputs are recorded.
- Every remaining root `/rw/scratch` hit is classified.
- Cortex production code has no positive root `/rw/scratch` contract/default reference.
- Suspicious hits are not waved away; they become a follow-up if found.

## Verification Plan

Use `rg -n` scans and inspect the relevant hit lines with `sed`/`nl` only as needed for classification.

## Risks

- Lower-layer LogicalFS tests may intentionally use `/rw/scratch`; classification must avoid deleting unrelated generic test coverage.
- Negative Cortex guards contain the old path by design; they must be described clearly.

## Assumptions

- Prior implementation already removed and rewrote the main Cortex residue; this ticket is a fresh guard, not a planned implementation change.
