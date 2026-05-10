# Move Workspace live file operations behind a LogicalFS authority port

## Problem Definition

P001 found that shell execution already uses LogicalFS and sandboxd, but
Workspace still directly manipulates `CortexStore` for live `RO` / `RW` file
operations. That leaves semantic code coupled to Blob/object key mapping and
makes it easy for active paths to bypass the LogicalFS boundary.

## Proposed Solution

Introduce an explicit live workspace file authority module and route Workspace,
Runtime, and API code through it:

- Add a `CortexLogicalFileAuthority` that owns logical path normalization,
  store-key mapping, read/write/list/delete/move-tree, and default layout
  initialization.
- Refactor `Workspace` methods to use that authority instead of `_store`.
- Refactor runtime and API code that reached into `store`/`ws._store` to use
  Workspace system write/read methods.
- Remove the legacy empty skill-name behavior uncovered during tests.

## Acceptance Criteria

- `Workspace` no longer directly calls `_store` for live file operations.
- API no longer reaches into `ws._store`.
- Runtime tool schema and skill writes go through Workspace system paths.
- Targeted Cortex tests pass.
- Any remaining direct store/blob use is isolated to the authority or
  transitional storage adapter and recorded for later guardrails.

## Verification Plan

Run focused residue scans for `_store` and `self.store`, plus targeted Cortex
tests covering workspace, runtime, skill lifecycle, skill install, shell wiring,
and sandbox fallback behavior.

## Risks

- Tests may encode old compatibility behavior; fix tests only when the old
  behavior is intentionally removed.

## Assumptions

- This is the in-process authority cutover. Separate network-service hardening
  can be handled later if P004/P005 expose a remaining blocker.
