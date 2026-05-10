# Physically remove Cortex runtime lifecycle methods

## Problem Definition

`Cortex.scope_create` and `Cortex.scope_end` remain as runtime façade methods. They directly call Workspace lifecycle writes and keep a non-event path available.

## Proposed Solution

- Remove the `scope_create` and `scope_end` method definitions from `novaic_cortex/runtime.py`.
- Update the runtime module docstring/comment so it no longer claims to provide internal scope lifecycle management.
- Add a focused guard test that instantiates or inspects `Cortex` and asserts those methods are absent.
- Do not migrate all old tests in this ticket; that belongs to the follow-up child problem.

## Acceptance Criteria

- `rg -n "async def scope_(create|end)" novaic_cortex/runtime.py` returns no matches.
- Guard test proves `Cortex` no longer exposes `scope_create` or `scope_end`.
- Focused guard test passes.

## Verification Plan

- Run static scan on `runtime.py`.
- Run the new/updated guard test.
- Optionally run the existing runtime import tests if touched.

## Risks

- Existing tests will fail until the sibling test-migration problem is solved. That is acceptable if recorded as a known gap for this child.

## Assumptions

- Runtime lifecycle removal is allowed even if old tests break temporarily because the parent ticket is split and subsequent child problems will migrate those tests.
