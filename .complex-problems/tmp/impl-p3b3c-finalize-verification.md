# Phase 3B3C Finalize Verification And Residue Check

## Problem

After helper and wiring work, P024 needs strict verification that finalize semantics are really active and not just implemented beside the live path. The checks must cover empty stacks, non-empty child stacks, retry/idempotency, projection clearing, and old hard-coded empty-stack residue.

## Success Criteria

- API or lifecycle tests cover finalize/archive with an empty stack.
- API or lifecycle tests cover finalize/archive while child stack remains non-empty and assert the operational finalize event contains that remaining stack.
- Retry/idempotency tests prove finalize does not duplicate conflicting events.
- Projection is cleared after finalize in tests.
- Static search confirms no live archive path still hard-codes `remaining_stack=[]` as the authority.
- Targeted and full Cortex tests pass.
