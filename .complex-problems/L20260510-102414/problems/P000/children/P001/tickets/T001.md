# Audit active shell layering and decide canonical model

## Problem Definition

The current code layout obscures whether Cortex, Sandbox, LogicalFS, Workspace/store, and Blob are layered correctly.

## Proposed Solution

Inspect active runtime imports, `Sandbox` composition, LogicalFS materialization/flushing, Workspace/store APIs, and tests. Record the canonical call flow and dependency flow, then identify cleanup targets.

## Acceptance Criteria

- File/function evidence is cited.
- The user-facing mental model is reconciled with implementation terminology.
- Cleanup items are concrete enough for the extraction and dependency-boundary tickets.

## Verification Plan

- Use `rg`, `sed`, and import inspection only.
- Record result in the ledger before marking success.

## Risks

- Confusing call flow with dependency flow could produce the wrong module boundary.

## Assumptions

- The no-local-fallback mount namespace path is the intended current runtime path.
