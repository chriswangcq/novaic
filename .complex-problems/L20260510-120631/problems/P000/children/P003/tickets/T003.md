# Ticket: Verify Shell Execution Runs Through LogicalFS And Sandboxd

## Problem Definition

After migrating the Cortex adapter, the active shell path must be proven as one explicit sequence:

1. Cortex projects Workspace state into a `LogicalFSSnapshot`.
2. `novaic-logicalfs` materializes a stable `/cortex` view.
3. Cortex passes the view root to sandboxd using `SandboxExecSpec.mount`.
4. sandboxd/core owns process execution.
5. `novaic-logicalfs` observes RW patch.
6. Cortex applies the patch back to Workspace.

The risk is a half-migration where tests pass but `Sandbox.exec` still has direct filesystem fallback or stale helper branches.

## Proposed Solution

Add or strengthen focused tests around the active `Sandbox.exec` path using a fake `SandboxExecutor` that inspects the mounted view while it is still alive.

Verify:

- The runner receives the raw command and a `SandboxExecSpec` with `/cortex` mount.
- The mounted source contains materialized RO/RW files from Workspace.
- Capability scripts are present in `/bin`.
- The fake runner can mutate the RW backing view and `Sandbox.exec` persists that mutation back through Workspace.
- Without a configured sandboxd executor, shell execution fails explicitly rather than falling back locally.

## Acceptance Criteria

- Focused tests prove materialized RO/RW content is visible to the runner through the mount source.
- Focused tests prove RW mutations made by the runner are observed and written back to Workspace.
- No local subprocess fallback is used in `Sandbox.exec`.
- `sandboxd` remains the only process execution boundary.

## Verification Plan

- Run focused Cortex sandbox tests.
- Run full Cortex non-real-shell suite.
- Scan `novaic_cortex.sandbox` for local subprocess/process fallback imports or calls.

## Risks

- Tests must inspect the mount while the temporary view is alive, inside the fake runner.
- The fake runner should not depend on host mount namespaces; it should inspect the source root that Cortex passes to sandboxd.

## Assumptions

- Real sandboxd live smoke belongs to the deploy/verification ticket.
- This ticket verifies the active Python boundary and Workspace patch behavior, not OS-level bind mount correctness.
