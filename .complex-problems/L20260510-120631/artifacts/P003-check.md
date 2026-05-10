# Check: P003 Shell Execution Path

## Verdict

Success.

## Evidence

- The fake sandboxd runner now inspects the mounted LogicalFS source root during `Sandbox.exec`.
- Test evidence proves:
  - Workspace `/ro` data appears in the runner source root.
  - Workspace `/rw` data appears in the runner source root.
  - Capability scripts are injected into `bin`.
  - RW mutations made by the runner are persisted back through Workspace.
  - Runner receives raw command plus `SandboxExecSpec.mount` at `/cortex`.
- Focused sandbox tests passed: 4 tests.
- Full Cortex non-real-shell suite passed: 345 passed, 40 skipped.
- Active sandbox/logical_fs code has no local subprocess fallback calls.

## Criteria Map

- Explicit shell sequence through LogicalFS and sandboxd: satisfied.
- Sandboxd receives SDK spec and core substrate remains behind sandboxd: satisfied by `SandboxExecSpec` assertions.
- Tests prove LogicalFS view input reaches sandboxd boundary: satisfied by mount source inspection.
- Local fallback remains absent: satisfied by explicit no-executor failure test and fallback scan.

## Execution Map

`Sandbox.exec` obtains a LogicalFS view from `MountNamespaceLogicalFS`, passes `SandboxExecSpec` to the configured executor, then releases the view and persists observed RW patch paths back to Workspace.

## Stress Test

The added test mutates the RW mirror from inside the fake runner and validates both `files_changed` and durable Workspace contents. This catches a direct-execution or no-patch half-migration.

## Residual Risk

OS-level sandboxd live execution and deploy script coverage remain for P004.
