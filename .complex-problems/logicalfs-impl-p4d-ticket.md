# Verify Blob Boundary Cleanup End To End

## Problem Definition

P006 audited Blob/object usage, P007 added guardrails, and P008 cleaned stale language. We need one targeted verification pass proving accepted Blob uses still work and live `RO` / `RW` bypass protection is active.

## Proposed Solution

Run targeted Cortex Blob/Workspace/guardrail tests, Blob Service object/blob tests, common Blob contract tests if available, and residual scans. Record accepted exceptions explicitly.

## Acceptance Criteria

- Cortex tests relevant to Blob store/payload/workspace/shell pass.
- Blob-service tests relevant to object/blob APIs pass.
- Guardrails pass and cover synthetic bypass cases.
- Residue scans are recorded and classified.

## Verification Plan

- Run targeted pytest commands in `novaic-cortex`, `novaic-blob-service`, and `novaic-common`.
- Run focused residual `rg` scans.

## Risks

- Some sibling package tests may require PYTHONPATH setup; record exact commands and outcomes.

## Assumptions

- This ticket is verification-only unless a tiny obvious wording miss appears.
