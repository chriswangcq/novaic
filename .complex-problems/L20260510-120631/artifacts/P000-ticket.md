# Build LogicalFS snapshot/view/patch boundary and migrate Cortex shell path

## Problem Definition

`novaic_cortex/logical_fs.py` currently owns too many responsibilities: it reads Cortex workspace data, decides agent/subagent env layout, materializes files, creates mount plans, sanitizes paths, detects changes, and writes patches back into Workspace. This violates the desired substrate boundary where LogicalFS should serve sandboxd as a filesystem view provider while treating Cortex as an explicit snapshot/patch state source.

## Proposed Solution

Implement a phased extraction:

1. Create a business-agnostic `novaic-logicalfs` package with snapshot/view/patch DTOs and local materialization/diff core.
2. Update Cortex to build explicit workspace snapshots, env overlays, and writable layout inputs.
3. Update Cortex shell orchestration to call the LogicalFS provider for `ViewHandle` creation and patch observation, then call sandboxd through `sandbox_sdk`.
4. Remove materialization/diff/layout logic from `novaic_cortex/logical_fs.py`, leaving at most a thin Cortex adapter.
5. Update tests, scripts, deployment, and residue scans so the active path cannot silently use the old Cortex-owned implementation.

## Acceptance Criteria

- `novaic-logicalfs` contains snapshot/view/patch contracts and materialization/diff logic.
- `novaic-logicalfs` imports no Cortex, agent runtime, agentctl, subagent, sandbox core process runner, or product business modules.
- Cortex constructs explicit snapshot/env/layout inputs and applies returned patches.
- Cortex does not directly implement filesystem materialization/diff logic.
- Sandbox execution path remains `Cortex -> logicalfs view -> sandbox_sdk -> sandboxd -> sandbox_core`.
- Deployment/start/test scripts include LogicalFS explicitly if it is a package/service dependency.
- Source scans show old Cortex LogicalFS substrate residue is gone.

## Verification Plan

- Run logicalfs package tests.
- Run Cortex shell/LogicalFS boundary tests.
- Run sandbox SDK/core/service tests.
- Run full `scripts/run_all_tests.sh`.
- Run residue scans for Cortex-owned materialization/diff helpers and forbidden imports.
- Run local sandboxd/logicalfs smoke if the service boundary is implemented in this ticket.

## Risks

- This is larger than the SDK split; old tests may depend on direct `Sandbox(ws)` local execution behavior.
- If implemented as a full daemon immediately, deployment/process supervision must be updated carefully.

## Assumptions

- The first durable final form can be a standalone package boundary; if the code shape shows a daemon is required for correctness, split into child tickets and implement the daemon wiring explicitly.
