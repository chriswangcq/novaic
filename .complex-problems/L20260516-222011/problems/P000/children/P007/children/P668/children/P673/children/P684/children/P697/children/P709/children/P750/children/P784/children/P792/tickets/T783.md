# Sandbox Unused Filesystem Helper Cleanup Ticket

## Problem Definition

Sandbox service may still expose an unused filesystem helper surface that exists only through exports/tests and can mislead future work.

## Proposed Solution

Search for the helper implementation, imports, exports, and tests. If no active path uses it, delete the helper surface plus tests/exports that only keep it alive. If an active path exists, record a spawned subproblem instead of deleting.

## Acceptance Criteria

- Usage scan proves active or inactive status.
- Inactive helper files/exports/tests are deleted.
- Active Sandbox service behavior remains tested.
- Focused Sandbox tests pass.

## Verification Plan

Use `rg` over `novaic-sandbox-service` and related packages. Run focused Sandbox tests after cleanup.
