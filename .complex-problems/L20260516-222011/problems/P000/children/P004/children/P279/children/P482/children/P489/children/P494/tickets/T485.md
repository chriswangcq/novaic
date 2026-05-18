# Wake finalize stack strictness ticket

## Problem Definition

P494 must make wake finalize remaining-stack handling explicit. Current `wake_finalize.py` fabricates a stack snapshot when `remaining_stack` is absent, and P493 found saga compensation can create `wake_finalize` without explicit stack diagnostics.

## Proposed Solution

Add a small explicit unknown-stack helper at the compensation producer boundary in `SagaRepository._build_wake_finalize_compensation_effect()` so compensation contexts always include `remaining_stack`. Then tighten `task_queue/sagas/wake_finalize.py` to require `remaining_stack` as a dict and stop synthesizing it from legacy fields. Update focused tests for valid pass-through, missing stack rejection, and compensation context.

## Acceptance Criteria

- Compensation wake-finalize context always carries explicit `remaining_stack`.
- `wake_finalize.py` rejects missing/non-dict `remaining_stack`.
- `stack_known_at_finalize` / `stack_depth_at_finalize` fallback is removed from finalizer logic.
- Focused tests pass.

## Verification Plan

Run tests covering `wake_finalize.py`, finalize ownership, saga compensation outbox, and legacy compatibility cleanup. Save test output under the ledger tmp directory.

## Risks

- Some tests may rely on missing stack fallback and need fixture updates.
- Strict finalizer behavior may expose producers not found by P493; if so, spawn a smaller blocker problem.

## Assumptions

- Explicit unknown stack at the producer boundary is acceptable for compensation, because compensation may not be able to call Cortex to inspect the live stack.
