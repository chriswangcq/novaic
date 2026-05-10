# Add Explicit Finalize Remaining Stack Event

## Problem Definition

Root finalize / scope archive currently emits a wake archived context event with `remaining_stack=[]`, losing the actual operational control stack at archive time. Phase 3 needs durable finalize semantics that records the reason, generation, and remaining stack before deterministically clearing or updating the active-stack projection.

## Proposed Solution

Implement finalize semantics as an operational SQLite event plus projection update:

- Add a small active-stack finalize helper that reads/normalizes the current stack, appends an idempotent finalize event with `reason` and `remaining_stack`, then clears the active-stack projection.
- Wire `scope_end` / wake archive paths so archive/finalize records actual remaining stack for root/wake finalization instead of hard-coded empty state.
- Use explicit generation and idempotency keys so retries return the same event rather than duplicating or conflicting.
- Keep context event behavior compatible, but feed it the same remaining stack snapshot where relevant.
- Add tests for finalize with empty stack and non-empty child stack, including retry/idempotency.

## Acceptance Criteria

- Finalize/root archive records explicit reason and actual remaining stack in operational SQLite.
- Active-stack projection is cleared or deterministically updated after finalize.
- Idempotent finalize/retry does not duplicate conflicting stack events.
- Tests cover empty-stack and non-empty child-stack archive/finalize cases.
- Existing Cortex tests continue to pass.

## Verification Plan

- Add focused operational helper tests for finalize event idempotency and projection clearing.
- Add API lifecycle/scope archive tests for empty and non-empty stacks.
- Run targeted Cortex tests around scope lifecycle, context events, active stack projection, and operational store.
- Run full `novaic-cortex/tests`.

## Risks

- Scope archive has multiple call sites; a partial wire-up could leave one path still clearing without durable finalize semantics.
- Context events and operational events must remain separate: context events describe LLM semantic history; operational events describe control-state finalization.
- P019/P020 still own read cutover and file-walk quarantine; this ticket must not accidentally widen scope into read authority changes.

## Assumptions

- Operational SQLite is available on production Workspace instances.
- Existing file-walk stack collection can still be used only as the temporary source snapshot for finalize until P019/P020 remove runtime read authority.
