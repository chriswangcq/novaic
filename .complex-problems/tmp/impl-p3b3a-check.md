# Phase 3B3A Success Check

## Summary

P027 is solved. R017 adds the active-stack finalize helper with explicit inputs, idempotent operational event recording, projection clearing, and focused tests for empty, non-empty, retry, and input validation cases.

## Evidence

- `finalize_active_stack_projection` exports from `active_stack_projection.py`.
- Empty-stack test proves finalize writes an `active_stack_finalized` event, leaves projection empty, and retry returns the same event.
- Non-empty test proves finalize payload records normalized `remaining_stack`, top scope id, and reason, then clears projection.
- Explicit input validation test rejects missing store/root/generation/reason/idempotency key.
- Full Cortex test suite passed with 443 tests.

## Criteria Map

- Add focused helper with explicit operational store, root scope id, frames, generation, reason, and idempotency key: satisfied.
- Helper writes durable operational SQLite event containing `remaining_stack`, `top_scope_id`, and `reason`: satisfied.
- Helper clears active-stack projection deterministically after recording event: satisfied.
- Retry with same idempotency key returns same event without conflicting duplicate writes: satisfied by empty-stack idempotency test.
- Unit tests cover empty and non-empty remaining stack cases: satisfied.

## Execution Map

- T021 executed as one bounded helper implementation.
- R017 records the implementation and verification commands.

## Stress Test

- The non-empty test includes string depth coercion and extra field dropping, proving finalize uses the same normalized frame contract as projections.
- The full suite checks the new exported helper does not affect existing Cortex behavior before live wiring.

## Residual Risk

- Live archive wiring is intentionally not solved here; P028 owns it.
- Atomic event+projection transaction remains a design question for live wiring. It is not required by P027, but P028/P029 should revisit it before final parent closure.

## Result IDs

- R017
