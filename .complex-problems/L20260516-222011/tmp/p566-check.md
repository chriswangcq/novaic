# P566 Check: Materialize API Classification Accepted

## Summary

Success. Result `R555` classifies the target Cortex materialization residue and records a concrete remediation candidate for P554 instead of trying to fix it inside the inventory child.

## Evidence

- `R555` records scan and slice artifacts.
- Artifact anchors confirm:
  - `Workspace.materialize()` definition.
  - `/rw/scratch` write path.
  - global `/rw/scratch` layout initialization.
  - only test callers for `Workspace.materialize()`.

## Criteria Map

- Records exact Cortex scan commands and outputs: satisfied by `materialize-scan.txt`.
- Reads relevant code slices with line references: satisfied by `materialize-slices.txt`.
- Classifies each hit bucket: satisfied by `R555` Summary/Verification/Known Gaps.
- Identifies remediation candidate for P554: satisfied, `Workspace.materialize()` plus legacy global `/rw/scratch`.

## Execution Map

- P566 one-go leaf scan executed.
- Result `R555` recorded.
- No production code changed.

## Stress Test

One-go skepticism: the result would fail if it only said "materialize exists." It instead checked callers, identified the write target, separated intended LogicalFS provider materialization from stale `Workspace.materialize()`, and recorded concrete P554 cleanup items.

## Residual Risk

- The final deletion decision depends on other P553 children not proving an active need for `/rw/scratch`.
- This residual risk is non-blocking for classification and is explicitly carried to P554.

## Result IDs

- R555
