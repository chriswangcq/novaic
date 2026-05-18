# Inventory Workspace Materialize References

## Problem Definition

`Workspace.materialize()` cannot be safely removed until current references are inventoried and classified. Broad `materialize(` hits may include legitimate LogicalFS internals, so the scan must distinguish stale Workspace API usage from intended lower-layer materialization.

## Proposed Solution

Run exact static scans in `novaic-cortex` for `Workspace.materialize`, `def materialize`, `.materialize(`, and broad `materialize(`. Record command outputs and inspect the relevant slices. Classify each hit and produce an implementation target list for P634.

## Acceptance Criteria

- Scan commands and outputs are recorded.
- Each hit is classified as stale Workspace API, test-only dependency, intended LogicalFS internals, or unrelated.
- The result names exact files/functions that P634 should edit or delete.
- No code is changed in this inventory ticket.

## Verification Plan

Use `rg` with line numbers plus targeted `sed`/`nl` slices for each hit. The check should reject the result if commands are missing or classifications are vague.

## Risks

- The term `materialize` may appear in intended LogicalFS code; deleting all hits blindly would be wrong.
- Tests may encode stale behavior but still contain useful assertions that should be migrated.

## Assumptions

- This ticket is read-only inventory; implementation happens in P634.
