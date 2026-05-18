# Verify Risky Saga Optional Residue Is Removed

## Problem Definition

P550 must directly prove that the known risky static residue found in P538 and fixed in P540, the saga optional-step API, is gone from live saga implementation paths and remains covered by focused tests.

## Proposed Solution

Run targeted `rg` checks for `SagaStep.optional`, `optional=True`, `optional: bool`, and `optional=optional` under `novaic-agent-runtime/task_queue`, inspect `wake_finalize`, and rerun the focused saga/finalize tests used by P540. Record exact outputs as artifacts.

## Acceptance Criteria

- Targeted `rg` artifact proves no live optional-step API remains in `task_queue`.
- `wake_finalize.py` has no `optional=True` registration.
- Focused saga/finalize tests pass.
- Any remaining optional-related hit is explained as benign or escalated.

## Verification Plan

Use `rg -n` with specific optional API terms, store output and exit codes, and run the focused pytest subset from P540 in `novaic-agent-runtime`.

## Risks

- Generic `optional` words can occur in benign diagnostics or comments.
- Focused tests prove the changed area, not the whole runtime.

## Assumptions

- `novaic-agent-runtime/task_queue` is the live implementation boundary for this risky residue.
- The P540 focused test list is still the relevant regression set.
