# Session-ended delivery chain inventory

## Problem Definition

P336 needs an exact map of the session-ended/finalize delivery chain before implementation. The inventory must identify every live producer, validator, transport, route, repository mutation, and test boundary where session generation can be defaulted, omitted, or preserved.

## Proposed Solution

Perform a read-only audit of `novaic-agent-runtime`:

1. Search the task-queue, queue-service, and tests for `session.ended`, `session_ended`, `wake_finalize`, `finalize_reason`, `session_generation`, `generation`, and `remaining_stack`.
2. Inspect the live delivery path from `wake_finalize` payload construction through `handle_session_ended`, `TaskQueueClient.session_ended`, queue-service route schema, and `SessionRepository.session_ended`.
3. Classify each boundary as safe, unsafe, or delegated.
4. Record the exact files/functions that P341-P344 should modify or verify.

## Acceptance Criteria

- The result lists live delivery-chain files/functions with roles.
- The result identifies required payload fields at every boundary.
- The result flags generation fallback/defaulting residue and assigns it to child problems.
- The result distinguishes live code from tests and broader upstream react contracts.

## Verification Plan

- Use `rg` and targeted `sed`/`nl` reads only; do not modify code.
- Cite file/line evidence for every unsafe or delegated boundary.
- Cross-check against existing tests to avoid inventing nonexistent paths.

## Risks

- `rg` output is noisy and may mix unrelated attach/recovery generation paths; the result must keep only P336-relevant session-ended/finalize paths.

## Assumptions

- P340 is an inventory task only; implementation belongs to P341-P344.
