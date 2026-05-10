# Live LogicalFS Implementation Closure

## Problem

Implement the completed Live LogicalFS design in the active Cortex shell path, not as a side implementation. The current shell execution path still contains temp-projection concepts: command-string RO decisions, sandbox-owned workspace materialization, sandbox-owned RW diff/persist, and misleading docs that describe disposable temp projection as the architecture.

The target is a clean production boundary:

- LogicalFS owns `/cortex/ro` and `/cortex/rw` logical filesystem semantics, cache/mirror state, dirty tracking, and store synchronization.
- SandboxExec owns only generic process execution: command, cwd, env, timeout, stdout/stderr, exit code.
- ShellExecutionOrchestrator owns acquisition/release choreography and result assembly.
- Active `Cortex.tool_shell` execution must route through that boundary.
- Old temp-projection semantic branches must be removed from the active path and tests must prove they stay removed.

If the local host cannot support true `/cortex` kernel/FUSE mount semantics, that limitation must be represented explicitly in the provider capability model and tests. It must not be hidden behind command-string heuristics.

## Success Criteria

- Active shell execution is routed through `LogicalFS -> SandboxExec -> ShellExecutionOrchestrator`, not directly through temp projection logic.
- Command-string RO gating is deleted from the active path; RO/RW logical view behavior is not decided by inspecting shell text.
- Sandbox-owned workspace materialization and RW commit/diff authority are deleted or moved behind LogicalFS ownership.
- Stable path support is explicit: current provider behavior and true mount limitations are tested and documented in code.
- RW layout exposes explicit subagent/public/tmp conventions through environment variables.
- Existing shell behavior, CLI capability scripts, token/API injection, timeout handling, and RW persistence still pass tests.
- New tests fail if old lazy-RO/command-gating behavior is reintroduced.
- Legacy comments/tests/docs that teach the old disposable projection architecture are updated or removed.
