# Audit and refactor Cortex shell layering boundaries

## Problem Definition

`novaic_cortex/sandbox.py` is doing too many jobs at once, making it unclear whether LogicalFS, Blob/store, Sandbox execution, and Cortex workspace ownership are properly layered. The runtime may be functionally correct but physically ambiguous, which is dangerous for future AI-assisted maintenance.

## Proposed Solution

Audit current active code and tests, decide the canonical dependency model, then refactor the code into explicit modules if the audit confirms physical boundary drift. The likely target shape is:

- Cortex workspace owns durable scope/RW data and delegates storage to Blob/store substrate.
- LogicalFS presents a live stable `/cortex/{ro,rw}` filesystem view over the workspace/store port.
- Sandbox composes LogicalFS with process execution and policy checks.
- Shell capability CLI is a separate shell-facing interface bundle, not part of LogicalFS or process execution.
- Public `Sandbox` remains the top-level facade used by runtime/API code.

No fallback path should be added. Displaced code should be deleted or moved, not duplicated.

## Acceptance Criteria

- A concise architecture decision is recorded in the ledger result.
- Code is split into module boundaries that match responsibilities.
- `sandbox.py` becomes a thin facade/orchestrator rather than a monolithic implementation bucket.
- LogicalFS dependencies on Workspace/store are explicit enough to show that Blob/store is a lower substrate, not a caller of LogicalFS.
- Tests/imports pass after the move.
- Residue scan does not find local fallback, command rewrite fallback, or stale duplicate implementations.

## Verification Plan

- Run targeted `novaic-cortex` tests covering sandbox sync, mount namespace requirements, shell capability runtime, output projection, and incremental sync.
- Run import/compile checks for `novaic_cortex.sandbox`, new extracted modules, and public tests.
- Run residue scans for fallback/rewrite names and for old direct imports that bypass the intended facade.

## Risks

- Large file extraction can accidentally change behavior if imports or helper visibility are mishandled.
- Tests may depend on private helpers from `sandbox.py`; compatibility re-exports may be needed temporarily, but must not obscure the new canonical modules.
- Workspace/store port cleanup could grow beyond a single coherent refactor; if it does, split a follow-up rather than mixing unrelated changes.

## Assumptions

- Existing dirty changes are intentional prior work and must not be reverted.
- The active mounted LogicalFS path is the current desired runtime path; local fallback remains forbidden.
