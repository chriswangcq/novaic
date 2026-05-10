# Ticket: Clean LogicalFS Residue And Wire Scripts

## Problem Definition

The LogicalFS package and Cortex adapter are implemented, but final closure requires proving the repo's operational surfaces know about `novaic-logicalfs` and that old/ambiguous paths are physically cleaned.

## Proposed Solution

Update and verify:

- `scripts/run_all_tests.sh` includes `novaic-logicalfs` and puts it on Cortex `PYTHONPATH`.
- `scripts/start.sh` includes `novaic-logicalfs` for Cortex runtime imports.
- `deploy` syncs/includes `novaic-logicalfs` where package source is deployed.
- Fresh-smoke/lint deploy checks know the new package when applicable.
- Residue scans prove:
  - `novaic-logicalfs` has no forbidden product/service imports.
  - `novaic-cortex` imports `logicalfs` and `sandbox_sdk`, not `sandbox_core`.
  - Old Cortex materialization/diff/fallback helper names are gone from active code.

Run the normal test suite and deploy.

## Acceptance Criteria

- Repo scripts wire `novaic-logicalfs` explicitly.
- Full test suite passes.
- Deploy succeeds and fresh smoke passes.
- No stale local fallback, Cortex generic filesystem helper, or sandbox core import remains in active Cortex code.
- If LogicalFS remains package-only, the result records that no LogicalFS daemon is intentionally deployed yet.

## Verification Plan

- Inspect and patch `deploy`, `scripts/start.sh`, `scripts/run_all_tests.sh`, and related lint/smoke scripts.
- Run targeted scans.
- Run `./scripts/run_all_tests.sh`.
- Run deploy command used by this repo.

## Risks

- Existing repo contains many prior uncommitted changes; avoid reverting unrelated files.
- Deploy may depend on local service availability and should be reported precisely if blocked.

## Assumptions

- LogicalFS is a package/substrate in this phase, not a standalone daemon.
- sandboxd remains the deployed process-execution service.
