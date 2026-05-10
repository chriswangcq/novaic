# Implement Active Stack Finalize Helper

## Problem Definition

The active-stack projection has push/pop writes, but no durable finalize helper that records the remaining stack and clears the projection in a reusable, deterministic way. Without this helper, archive wiring would either duplicate logic or keep hard-coded empty-stack semantics.

## Proposed Solution

Extend `novaic-cortex/novaic_cortex/active_stack_projection.py` with a finalize helper:

- Normalize the provided remaining stack frames with the same frame contract as active-stack writes.
- Append an operational SQLite event with event type such as `active_stack_finalized`.
- Include `remaining_stack`, `top_scope_id`, and `reason` in the event payload.
- Clear active-stack projection by writing an empty frame list with the same generation.
- Require explicit operational store, root scope id, frames, generation, reason, and idempotency key.
- Add focused tests for empty stack, non-empty stack, and idempotent retry.

## Acceptance Criteria

- Helper exists and is exported from `active_stack_projection.py`.
- Empty-stack finalize writes an event and leaves projection empty.
- Non-empty finalize writes event payload with normalized remaining stack and clears projection.
- Retrying with the same idempotency key returns the same event and leaves projection empty.
- Helper rejects missing explicit inputs.

## Verification Plan

- Extend `test_active_stack_projection.py`.
- Run helper and operational-store tests.
- Run `py_compile` on the helper module.

## Risks

- Projection clearing and event append are two operational-store calls; if this needs atomicity, a later check should surface it before wiring.
- Event naming must remain operational/control-plane specific and not be confused with semantic context events.

## Assumptions

- Existing operational store idempotent event API is sufficient for retry semantics.
- The helper can temporarily use projection clearing after event append; P028/P029 will validate live archive behavior.
