# Ticket: Full Cutover Verification And Residue Scan

## Problem Definition

The test migrations and runtime wiring must be proven as a connected cutover. A passing narrow test is insufficient if old constructors, compatibility modules, or sandbox RO/RW paths still exist in active source or tests.

## Proposed Solution

Run the full Cortex test suite plus LogicalFS and sandbox-service targeted suites. Run residue scans for old constructor calls, old file authority classes, BlobCortexStore, deleted module imports, and direct live persistence ownership. Classify any remaining old code into P024 cleanup rather than hiding it in this verification result.

## Acceptance Criteria

- Full Cortex tests pass or every failure is captured as a follow-up.
- LogicalFS tests pass.
- Sandbox/service wiring tests relevant to RO/RW pass.
- Direct `Workspace(store...)` and `Cortex(store...)` patterns are gone from tests.
- `CortexLogicalFileAuthority`, `BlobCortexStore`, and deleted module imports are absent from active live code.
- Remaining old store/module residue is explicitly listed for P024 cleanup.

## Verification Plan

- Run `python3 -m pytest -q` in `novaic-cortex`.
- Run `python3 -m pytest -q` in `novaic-logicalfs`.
- Run targeted sandbox-service tests if present.
- Run `rg` residue scans across source, tests, and docs.

## Risks

- Full test suite may expose unrelated failures caused by prior dirty worktree changes; classify evidence carefully and do not hide them.
- Some old modules may still be test-only but should be explicitly carried to P024 rather than normalized.

## Assumptions

- P024 owns deletion of old authority paths and documentation cleanup after verification identifies what remains.
