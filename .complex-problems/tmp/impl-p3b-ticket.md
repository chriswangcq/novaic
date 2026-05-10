# Add SQLite Active Stack Write Projection

## Problem Definition

Operational SQLite has an `active_stack_projection` table, but runtime lifecycle APIs do not write it. Before runtime reads can cut over, `skill_begin`, `skill_end`, and finalize must maintain a deterministic top-first frame projection with explicit generation semantics.

## Proposed Solution

Implement in small parts:

- Define a tiny active-stack projection helper that converts scope path/meta into top-first frame dictionaries and writes via `OperationalSqliteStore.set_active_stack`.
- Wire successful `skill_begin` to push/write the new active stack after child scope creation.
- Wire successful `skill_end` to pop/write the active stack after child close.
- Wire structural finalize/root archive to record a `WakeFinalized`/archive event with explicit reason and remaining stack, then clear or update the active-stack projection.
- Add tests for nested begin/end, projection state after store re-open/reuse, and finalize remaining-stack semantics.

## Acceptance Criteria

- Active-stack write helper has explicit inputs and does not read global state.
- `skill_begin` updates operational SQLite active stack after a successful child open.
- `skill_end` updates operational SQLite active stack after a successful child close.
- Finalize/root archive records explicit reason and remaining stack in durable operational state.
- Tests prove nested stack projection and restart-like store reuse.

## Verification Plan

- Run new/updated active-stack projection tests.
- Run existing skill lifecycle, scope-state, operational-store, and context-status tests affected by begin/end.
- Run `py_compile` on modified Cortex modules.
- Use static search to verify runtime write sites call the new helper.

## Risks

- If helper reconstructs frames from file walking, the write path may merely mirror old authority. It should consume explicit operation facts where possible and only use trace files as projection inputs during this phase.
- Finalize semantics need care: remaining stack should reflect live operational frames before clearing.

## Assumptions

- Phase 3C will switch runtime reads to this projection after write coverage is in place.
- Scope tree files remain materialized trace artifacts during this phase.
