# Design Complete Live LogicalFS Substrate

## Problem Definition

The desired final form is a live filesystem substrate: shell writes should be filesystem operations owned by LogicalFS, not temp-tree changes collected and committed after process exit. SandboxExec should be a pure process runner; ShellOrchestrator should coordinate lifecycle without owning filesystem semantics.

## Proposed Solution

Produce a complete design for live LogicalFS, including architecture, component boundaries, filesystem operation semantics, journal/cache/blob sync, RW directory conventions, crash recovery, tests, implementation phases, and non-goals.

## Acceptance Criteria

- The design eliminates `commit` as a Sandbox/ShellOrchestrator concept.
- LogicalFS owns file semantics and live synchronization.
- SandboxExec owns only process execution.
- The architecture supports full logical `/cortex/ro` and `/cortex/rw` views.
- The design includes staged implementation and fallback strategy.

## Verification Plan

- Check against current sandbox code and the prior corrected RO/RW design.
- Ensure every root success criterion is mapped in the final check.

## Risks

- A true live filesystem is significantly more complex than temp projection.
- FUSE or watcher-based systems can introduce operational and crash-recovery complexity.

## Assumptions

- This pass is design only.
- The user prefers the complete target architecture over a minimal incremental optimization.
