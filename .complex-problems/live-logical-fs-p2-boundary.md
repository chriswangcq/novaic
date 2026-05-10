# Implement LogicalFS And SandboxExec Boundary

## Problem

Create the production code boundary that separates filesystem semantics from process execution. The active code should have named components for LogicalFS view acquisition/release, generic process running, and shell orchestration.

## Success Criteria

- Introduce a LogicalFS provider abstraction for the current local mirror substrate.
- Introduce a SandboxExec/process runner that does not know Cortex store, RO/RW sync, or changed files.
- Introduce a ShellExecutionOrchestrator that composes LogicalFS and SandboxExec.
- Preserve capability scripts, token/API injection, timeout handling, path sanitization, and `ShellResult` shape.
- Add explicit RW convention environment variables for public/self/tmp/artifacts/scratch.
