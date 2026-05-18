# Harden compensation wake_finalize identity preservation

## Problem Definition

`SagaOrchestrator._build_wake_finalize_compensation_effect` currently copies `session_generation` when present but still creates `wake_finalize` compensation work when generation is missing or invalid. That creates an ambiguous mutating finalize task from a failure path.

## Proposed Solution

Make compensation finalize creation require a positive `session_generation` and explicit scope identity before emitting the `create_wake_finalize_saga` outbox effect. Preserve the existing positive generation and wake/root scope identity on the happy path. Add focused tests for happy-path preservation and missing/invalid-generation suppression.

## Acceptance Criteria

- Compensation-created `wake_finalize` contexts include `scope_id`, `agent_id`, `subagent_id`, `user_id`, wake/root scope identity when present, and positive `session_generation`.
- Missing, zero, boolean, or malformed `session_generation` does not create a `create_wake_finalize_saga` outbox effect.
- Existing successful compensation outbox behavior remains intact for valid generated contexts.
- Tests cover both valid generation preservation and invalid-generation suppression.
- No new default-to-zero or compatibility fallback is introduced.

## Verification Plan

Run focused compensation tests in `tests/test_pr311_saga_compensation_outbox_cutover.py`, compile `queue_service/saga_repo.py`, and search the compensation builder for generation defaulting residue.

## Risks

- Suppressing compensation finalize for malformed old contexts may reveal tests that assumed old fallback behavior; those should be updated because compatibility is not required.
- If no finalize effect is emitted for missing generation, a failed non-finalize saga may remain failed without compensation cleanup; this is acceptable only if it avoids ambiguous mutation and is covered by tests.

## Assumptions

- Failed saga contexts produced by current normal runtime carry positive `session_generation`; invalid/missing generation is a malformed legacy or corrupted path.
- P363 owns the separate recovery archive direct `cortex.scope_end` path.
