# Run Final Tests And Residue Scans

## Problem Definition

All implementation phases are closed, so final tests and scans must validate that LogicalFS/Cortex/sandbox/Blob boundaries remain intact.

## Proposed Solution

Run full or nearest-feasible suites for Cortex, sandbox-service, logicalfs, Blob Service, and common Blob contracts. Then run focused residue scans for local fallback, direct Blob live bypass, and stale Blob Workspace language.

## Acceptance Criteria

- Cortex full suite passes.
- Sandbox-service suite passes.
- LogicalFS suite passes.
- Blob Service and common Blob contract tests pass.
- Residue scans are recorded and classified.

## Verification Plan

- Execute pytest commands in each relevant package.
- Execute `rg` scans from repo root.

## Risks

- Full suites may expose unrelated pre-existing failures; classify if encountered instead of hiding them.

## Assumptions

- Tests run locally without external services.
