# Ticket: Replace Temp Projection With LogicalFS Execution Boundary

## Problem Definition

The Cortex shell active path still teaches and uses a disposable temp-projection model. That creates two risks the user explicitly called out: new code can exist without being fully connected, and old logic can remain available for future agents to accidentally reuse.

The implementation must replace the active path with a clear LogicalFS execution boundary while preserving user-visible shell behavior and explicitly surfacing any host-level mount limitation.

## Proposed Solution

Split the work into closure tickets and execute them in order:

1. Map the current active path and physical constraints so implementation does not rely on assumptions.
2. Build the LogicalFS/SandboxExec/ShellExecutionOrchestrator boundary in `novaic-cortex`.
3. Route `Sandbox.exec`/`Cortex.tool_shell` through the new boundary.
4. Remove the old command-gated RO materialization path and old tests that encode it.
5. Add tests for active routing, no command-string RO gating, RW conventions, stable path behavior, and provider capability limitations.
6. Run focused and package-level tests, then record residual risk honestly.

## Acceptance Criteria

- Active shell path no longer calls command-string RO decision code.
- Logical filesystem ownership is named and represented in code.
- Process execution no longer owns workspace materialization or RW persistence semantics.
- Old lazy-RO tests are replaced by tests proving full logical view behavior.
- The local provider’s stable path limitation is explicit rather than pretending hidden literal `/cortex` works without a mount substrate.
- Focused tests and broad relevant tests pass.
- Residue audit shows no misleading current-path docs/comments left in touched code.

## Verification Plan

- `rg` audit for old names and semantic branches.
- Focused `pytest` on sandbox/logical-fs tests.
- Existing shell capability/runtime tests.
- Package test subset covering sandbox, runtime API, tool schema, and output projection.

## Risks

- True kernel/FUSE `/cortex` mount may not be implementable on this host because there is no `/cortex`, FUSE library, proot, unshare, or root privilege.
- Large existing dirty worktree means changes must be scoped carefully and must not revert unrelated work.
- Moving ownership while preserving current behavior can reveal old tests that intentionally codified the performance shortcut.

## Assumptions

- The current repo state contains previous user-approved work and must be preserved.
- It is acceptable to represent unavailable true mount semantics as an explicit provider capability and blocker, rather than silently claiming it is solved.
