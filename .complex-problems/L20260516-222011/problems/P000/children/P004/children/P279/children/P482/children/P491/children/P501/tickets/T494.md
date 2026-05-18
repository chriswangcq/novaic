# Recovery/session-ended contract inventory ticket

## Problem Definition

P501 must inspect recovery and session-ended code paths before implementation. The goal is to identify whether suspected-dead, recovery archive, and session-ended paths preserve explicit generation and stack diagnostics or still contain silent fallback behavior.

## Proposed Solution

Run targeted `rg` searches and source inspection over recovery/session/finalize runtime files and focused tests. Save raw guard output and a classification artifact separating strict production behavior, adapter boundaries, test fixtures, and cleanup candidates.

## Acceptance Criteria

- Raw guard output is saved.
- Classification artifact lists exact file references.
- Silent fallback or ambiguous recovery stack behavior is routed to P502.
- No source changes are made.

## Verification Plan

Inspect `saga_repo.py`, `session_recovery.py`, `session_repo.py`, `session_fsm.py`, `session_handlers.py`, `wake_finalize.py`, and recovery/finalize tests with `rg`/`sed`.

## Risks

- Defensive unknown-stack behavior can look like compatibility fallback; classification must distinguish explicit unknown from silent fabricated known-empty stack.

## Assumptions

- P489 already made wake finalize require explicit `remaining_stack`.
