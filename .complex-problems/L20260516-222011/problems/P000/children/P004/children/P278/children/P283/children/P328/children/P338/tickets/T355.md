# Ticket: Remaining Stack and Finalize Reason Archive Boundary

## Problem Definition

Finalize/session-ended records must bind `finalize_reason`, `remaining_stack`, and `ended_at` to the same explicit scope/generation identity that authorized the finalize. Any stale active lookup after generation change can produce misleading diagnostics or recovery state.

## Proposed Solution

Split the work into source mapping, targeted implementation/tests, and aggregate verification. This is not a safe one-go because it crosses Cortex archive metadata, queue session finalized events, wake-finalize payloads, and tests.

## Acceptance Criteria

- Every live place that records `finalize_reason`, `remaining_stack`, or `ended_at` is mapped.
- Mutating records are tied to explicit scope/generation.
- Stale finalize cannot archive or record remaining stack for a newer wake.
- Valid finalize records reason and stack for the intended generation.
- Aggregate residue search confirms no stale active lookup remains in this boundary.

## Verification Plan

- Inspect `task_queue/sagas/wake_finalize.py`, `task_queue/handlers/session_handlers.py`, `task_queue/handlers/cortex_handlers.py`, `queue_service/session_repo.py`, `queue_service/session_ledger.py`, recovery/compensation helpers, and relevant tests.
- Add focused tests for stale scope/generation rejection and valid reason/stack persistence.
- Run focused finalize/session/recovery test suites and residue searches.
