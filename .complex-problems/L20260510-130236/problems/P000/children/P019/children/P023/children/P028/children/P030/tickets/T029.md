# Ticket: Migrate Direct Cortex Constructor Tests

## Problem Definition

Tests still construct runtime with the obsolete `Cortex(store, agent_id=...)` or positional `Cortex(store, agent_id)` form. That bypasses the new explicit Workspace/LogicalFS authority boundary and creates pressure to restore a compatibility constructor.

## Proposed Solution

Replace all live test usages of old direct Cortex constructors with `make_cortex_with_store(...)`, which builds a LogicalFS-backed `Workspace` first and then calls `Cortex(workspace=...)`. Preserve hooks, metrics, sandbox runner, blob payload, and existing MemoryStore access where tests assert persisted state.

## Acceptance Criteria

- No test calls `Cortex(MemoryStore...)`, `Cortex(store...)`, or positional store constructor forms outside the helper.
- Tests that need store inspection receive the helper-returned `store`.
- Hook/metrics/sandbox runner tests keep their explicit dependencies.
- Targeted runtime/tool/hook/engine tests pass.

## Verification Plan

- Run a direct-constructor residue scan under `novaic-cortex/tests`.
- Run targeted pytest for the files reported by the residue scan.
- Re-run the broader P028 targeted test set if helper changes affect earlier migrated tests.

## Risks

- Tests may rely on Workspace hooks that used to be passed through the runtime constructor; helper must pass hooks into both Workspace and Cortex.
- Tests may inspect raw store keys; helper must return the same backing MemoryStore.

## Assumptions

- Runtime compatibility constructor should not be restored.
- Test-only helpers are the accepted boundary for constructing Cortex with an in-memory object store.
