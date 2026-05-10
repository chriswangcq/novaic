# Cut Cortex Active Runtime To LogicalFS Authority

## Problem Definition

Cortex still constructs live workspace files through `Workspace(store, agent_id)` and `CortexLogicalFileAuthority`. Even after adding LogicalFS authority and moving Blob adapter ownership, the active runtime is not fully cut over while Workspace/runtime/tests can still use a direct store-shaped path.

## Proposed Solution

Refactor Cortex in smaller slices so active runtime depends on a LogicalFS authority/port. Create explicit Cortex-side factories or test helpers for constructing an authority with a memory object store, update Workspace to receive a LogicalFS authority, update registry/runtime construction, migrate tests away from `Workspace(MemoryStore(), ...)` and `Cortex(MemoryStore(), ...)`, and verify shell/sandbox behavior still persists RW patches.

## Acceptance Criteria

- `Workspace` constructor no longer accepts direct `CortexStore` / Blob object persistence as its live file dependency.
- Active registry/runtime/API paths pass explicit owner/layout inputs into LogicalFS authority construction.
- Tests use explicit authority-backed helpers instead of the old direct store constructor.
- Sandbox shell RO/RW materialization and patch persistence still pass after cutover.
- Source scans show no direct store access in `workspace.py`, `runtime.py`, or `api.py`.

## Verification Plan

- Split the cutover into child problems for Workspace constructor/factory, runtime/registry wiring, and tests/residue scans.
- Run targeted Cortex tests after each implementation slice.
- Run full Cortex tests and relevant sandbox/LogicalFS tests before checking P023.

## Risks

- Many tests rely on the old convenience constructor; migrating them mechanically can accidentally preserve old behavior through hidden helpers.
- Keeping a compatibility constructor in `Cortex` or `Workspace` would undercut the boundary.
- Type-only cleanup can look done while runtime still reaches the old path.

## Assumptions

- `StoreBackedLogicalFileAuthority` from LogicalFS is now the intended live file dependency.
- `CortexStore`/`MemoryStore` may temporarily remain as test object-store adapters until the final cleanup ticket decides whether they should move or be deleted.
