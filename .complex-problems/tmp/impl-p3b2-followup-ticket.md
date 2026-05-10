# Add Nested Lifecycle And Restart Projection Tests

## Problem Definition

P023 active-stack write implementation is present, but its success check found verification gaps: there is no focused API lifecycle test for nested skill pushes/pops, and no restart-like proof that the active-stack projection survives reopening the same SQLite operational store.

## Proposed Solution

Add focused verification without changing production behavior unless tests expose a real defect:

- Extend `test_context_event_api_skill_lifecycle.py` with a nested begin/end test that opens `skill-1`, opens `skill-2` under it, asserts SQLite top-first frames after both pushes, closes `skill-2`, and asserts the projection contains `skill-1` then `wake-1`.
- Add a restart-like operational-store test that writes an active stack, constructs a new `OperationalSqliteStore` or `build_operational_sqlite_store` instance with the same SQLite path, and asserts `get_active_stack` returns the persisted frames.
- Run targeted tests first, then full `novaic-cortex/tests`.

## Acceptance Criteria

- Nested API lifecycle projection test proves pushed and popped stack state across two child skills.
- Restart-like operational-store test proves persisted active-stack projection can be read through a fresh store instance.
- No production code is changed unless the tests reveal a bug.
- Targeted and full Cortex test suites pass.

## Verification Plan

- Run the focused lifecycle/helper/store tests.
- Run `python3 -m py_compile` on any touched test/helper modules if production code changes.
- Run full `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`.

## Risks

- Nested lifecycle behavior may expose that read-side still derives stacks from file-walk; if so, keep the follow-up scoped to write projection correctness and record remaining read cutover under P019/P020.
- Reopening the operational store must use explicit clock and id providers so the test stays deterministic.

## Assumptions

- The current P023 implementation should pass these stricter tests without requiring production code changes.
- This follow-up closes verification gaps only; it does not attempt the Phase 3 read cutover.
