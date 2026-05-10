# Verify common extraction and residue cleanup

## Problem Definition

After moving stable primitives into common, we need to prove no local duplicate implementation or stale path remains.

## Proposed Solution

Run common and Cortex tests, compile checks, and residue scans over both repos. Record exact remaining risks.

## Acceptance Criteria

- `novaic-common` full tests pass.
- `novaic-cortex` full tests pass.
- Residue scans show no old local generic implementations in Cortex.
- Ledger is valid and complete.

## Verification Plan

- `PYTHONPATH=. pytest -q` in `novaic-common`.
- `pytest -q` in `novaic-cortex`.
- `rg` scans for old modules/classes/helpers.

## Risks

- Existing unrelated dirty files may remain; report without reverting.

## Assumptions

- Local mount namespace tests may skip when host lacks root/unshare/mount.
