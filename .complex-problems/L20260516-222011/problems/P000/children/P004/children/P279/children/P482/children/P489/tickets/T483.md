# Finalize ownership cleanup ticket

## Problem Definition

P489 must remove or tighten finalize ownership compatibility behavior. The P488 inventory identified `wake_finalize.py` synthesizing `remaining_stack` from optional legacy-ish context keys when no explicit `remaining_stack` is present. That weakens the explicit finalize contract because the saga can emit a formally valid `session_ended` payload while losing the real stack state.

## Proposed Solution

Inspect wake finalize inputs and producers. If every legitimate finalize path can provide an explicit `remaining_stack`, require it in `wake_finalize.py` and remove the fallback synthesis. If a producer is missing it, fix the producer rather than preserving fallback. Add or update focused tests proving wake finalize rejects missing/non-dict `remaining_stack` and still passes valid stack metadata through to Cortex scope end and session-ended payloads.

## Acceptance Criteria

- `wake_finalize.py` no longer fabricates a successful finalize `remaining_stack` when missing.
- Legitimate finalize producers/tests provide explicit `remaining_stack`.
- Focused finalize ownership tests cover valid pass-through and missing/invalid stack rejection.
- No unrelated recovery or attach behavior is changed in this ticket.

## Verification Plan

Run focused tests around `wake_finalize.py`, session-ended finalize contract, and legacy compatibility cleanup guards. Use `rg` to confirm the fallback synthesis is removed or made strict.

## Risks

- Compensation/recovery finalize contexts may rely on fallback fields today; if so, create a smaller child problem or fix the producer explicitly.
- Tightening finalize may expose existing tests that were relying on implicit empty stack.

## Assumptions

- User preference is no backward-compatible fallback unless it is a clearly justified runtime guard.
