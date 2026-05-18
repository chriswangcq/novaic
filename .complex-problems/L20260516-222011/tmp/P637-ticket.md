# Final RW Scratch Contract Guard

## Problem Definition

The RW scratch cleanup changed the Cortex default layout and rewrote many fixtures. The final guard must skeptically prove the tree no longer presents root `/rw/scratch` as the preferred/default scratch contract, while preserving legitimate arbitrary RW path behavior and lower-layer LogicalFS generic tests.

## Proposed Solution

Run a fresh repository-level classification pass for root `/rw/scratch`, `RW_SCRATCH`, and `/rw/subagents` across Cortex and LogicalFS. Confirm that Cortex-only root scratch hits are negative guards or absent, confirm subagent-aware scratch remains the active shell contract, and rerun the focused tests that protect layout, fixture behavior, and lower-layer generic path handling.

## Acceptance Criteria

- Fresh scans are recorded and classify every remaining `/rw/scratch` hit.
- Cortex does not expose root `/rw/scratch` as default/canonical scratch in production code or positive test fixtures.
- Current subagent-aware `RW_SCRATCH` behavior remains covered.
- Focused Cortex and LogicalFS tests pass.
- Any suspicious remaining hit becomes a follow-up instead of being waved away.

## Verification Plan

Run `rg` scans across `novaic-cortex` and `novaic-logicalfs`, then run the focused Cortex workspace/runtime/path/sandboxd suite and the LogicalFS layout/authority suite with explicit dependency paths.

## Risks

- The scan may find root scratch in lower-layer generic tests; those must be classified precisely, not blindly removed.
- A broad test suite can hide dependency path issues; rerun with corrected `PYTHONPATH` rather than accepting collection failures.

## Assumptions

- P636 and children completed their implementation work.
- No code changes should be necessary unless the final guard finds a real residue.
