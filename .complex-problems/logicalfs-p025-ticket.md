# Add Cortex LogicalFS Authority Factory

## Problem Definition

Cortex tests and runtime need an explicit replacement for the old `Workspace(store, agent_id)` pattern. The replacement should produce a LogicalFS authority from an object store and agent id without importing or using `CortexLogicalFileAuthority`.

## Proposed Solution

Add a small Cortex-side factory module that validates agent ids, maps an agent to the explicit object-store owner prefix, and returns `StoreBackedLogicalFileAuthority` with `LogicalFileAuthorityLayout`. Add tests proving the helper is explicit and rejects invalid agent ids.

## Acceptance Criteria

- Factory creates `StoreBackedLogicalFileAuthority` with `owner_prefix="agents/{agent_id}"`.
- Agent id validation is explicit and matches Workspace constraints.
- No `CortexLogicalFileAuthority` import or usage is introduced.
- Tests cover valid prefix creation and invalid ids.

## Verification Plan

- Add targeted tests for the factory.
- Run the new tests.
- Run a source scan for `CortexLogicalFileAuthority` in the factory and tests.

## Risks

- The helper could become a new hidden compatibility layer if it is too broad.
- Validation duplication must stay minimal and intentional.

## Assumptions

- Object-store adapter typing remains generic until P026/P027 complete the constructor cutover.
