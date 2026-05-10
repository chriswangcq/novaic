# Move sandbox substrate from common to independent sandbox-core

## Problem Definition

The sandbox substrate is generic infrastructure and should not live in broad `novaic-common`. Keeping it there makes dependency ownership ambiguous and invites future business/common coupling.

## Proposed Solution

Create `novaic-sandbox-core/sandbox_core`, move the current sandbox primitives and tests into it, rewrite Cortex and sandboxd imports, update PYTHONPATH/deploy/test scripts, delete `novaic-common/common/sandbox`, and verify with targeted tests and residue scans.

## Acceptance Criteria

- `novaic-sandbox-core` contains the sandbox substrate and tests.
- No active code imports `common.sandbox`.
- `novaic-common/common/sandbox` no longer exists.
- `scripts/start.sh`, `deploy`, and `scripts/run_all_tests.sh` explicitly include/sync/test sandbox-core.
- Targeted tests pass for sandbox-core, sandboxd, and Cortex wiring.

## Verification Plan

- Run sandbox-core tests.
- Run sandboxd service tests with `novaic-sandbox-core` on PYTHONPATH.
- Run Cortex sandboxd wiring tests with `novaic-sandbox-core` on PYTHONPATH.
- Run shell syntax checks and residue scans.

## Risks

- Some existing tests or scripts may still assume `common.sandbox`; source scans must catch these.

## Assumptions

- `novaic-common` still owns service config, including `sandboxd` URL. This ticket only extracts sandbox execution substrate.
