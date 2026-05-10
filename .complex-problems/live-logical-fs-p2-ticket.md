# Ticket: Build LogicalFS / SandboxExec / Orchestrator Boundary

## Problem Definition

The current `Sandbox` class owns too many concerns: it decides whether RO is needed, copies workspace files, runs the process, diffs RW, persists changes, sanitizes paths, and logs. This makes it easy to add a new implementation without actually removing the old execution path.

## Proposed Solution

Refactor `novaic-cortex/novaic_cortex/sandbox.py` into explicit components while preserving the public `Sandbox.exec` API:

- `LocalMirrorLogicalFS`: owns current local mirror substrate, logical RO/RW sync, RW layout, env construction, changed-file flush, and stable path capabilities.
- `SandboxExec`: owns only subprocess execution and timeout/kill behavior.
- `ShellExecutionOrchestrator`: owns acquisition/run/release choreography and result assembly.
- `Sandbox`: becomes the public compatibility facade that delegates to the orchestrator.

## Acceptance Criteria

- New components are present and active.
- Process runner has no store or RO/RW sync authority.
- LogicalFS provider owns RW persistence and full logical view materialization.
- `Sandbox.exec` delegates to orchestrator.
- Explicit capability model represents the current local mirror provider and lack of true mounted `/cortex`.
- RW layout env vars exist.

## Verification Plan

- Code inspection after patch.
- Existing sandbox tests plus new tests in the cleanup/verification tickets.

## Risks

- Refactor could break shell capability scripts or token/API injection.
- Stable `/cortex` path output must remain sanitized even though the provider uses a local backing path.

## Assumptions

- Public `Sandbox.exec` signature remains stable for current callers.
