# Risky Saga Optional Residue Closure Gate

## Problem

Verify that the only risky residue found during static classification, the saga optional-step API, is fully removed from live code after P540. This child belongs under P533 because the parent audit cannot close if the known risky residue still exists.

## Success Criteria

- Directly checks for `SagaStep.optional`, `optional=True`, `optional: bool`, and `optional=optional` in the saga implementation paths.
- Confirms `wake_finalize` no longer registers an optional cortex scope end step.
- Runs or cites focused saga/finalize tests that cover the modified area.
- Creates a follow-up if any risky optional-step live-code path remains.
