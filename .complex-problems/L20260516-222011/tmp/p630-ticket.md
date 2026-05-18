# Remove Workspace.materialize Direct Materialization API

## Problem Definition

`Workspace.materialize()` is stale Cortex direct materialization residue. It can mislead future code into bypassing the intended LogicalFS materialized view and sandboxd execution boundary, even if the inventory found no production caller today.

## Proposed Solution

Scan all references to `Workspace.materialize` and related `materialize(` calls, remove the method from `novaic_cortex.workspace.Workspace`, and delete or rewrite tests that only assert the old direct materialization behavior. Preserve only current LogicalFS/sandboxd boundary behavior in tests.

## Acceptance Criteria

- No `Workspace.materialize` API remains in production code unless a current caller proves it is necessary and it is renamed/hidden as internal non-bypass plumbing.
- Tests no longer encode the old direct materialization contract.
- Any remaining `materialize(` references are classified and justified.
- Focused Cortex workspace/logicalfs tests pass.

## Verification Plan

Run `rg -n "Workspace\.materialize|def materialize|\.materialize\(|materialize\(" novaic-cortex`, then run focused Cortex tests around workspace, logicalfs, shell execution, and any edited tests.

## Risks

- Some tests may be using `Workspace.materialize()` as fixture setup and need a cleaner LogicalFS-oriented replacement.
- There may be similarly named methods in LogicalFS that are legitimate and should not be deleted blindly.

## Assumptions

- P562/P553 inventory is correct that there is no production caller requiring the API.
- Physical deletion is preferred over retaining compatibility helpers.
