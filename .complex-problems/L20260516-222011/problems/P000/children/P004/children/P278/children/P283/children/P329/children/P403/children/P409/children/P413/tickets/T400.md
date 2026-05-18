# Finalize saga and session handler classification ticket

## Problem Definition

Finalize sagas and session handlers carry final session identity into Queue session mutation. They must fail closed for missing/invalid session generation and require finalize reason plus remaining stack.

## Proposed Solution

Inspect `wake_finalize.py`, `subagent_wake.py`, and `session_handlers.py`, classify all guard hits, patch any fallback, and run focused tests for finalize/session handler contracts.

## Acceptance Criteria

- `wake_finalize` payloads require explicit positive `session_generation`.
- `subagent_wake` requires explicit positive `session_generation`.
- `session_handlers` rejects missing scope, generation, finalize reason, and remaining stack.
- No finalize/session-ended handler path defaults session generation.
- Focused tests pass.

## Verification Plan

- Run targeted guards over the three files.
- Inspect source around generation/finalize/remaining_stack hits.
- Run `test_pr254_finalize_ownership.py`, `test_runtime_explicit_contracts.py`, and subagent/session-init focused tests.

## Risks

- Finalize reason/remaining stack defaults may be legitimate only if they are not replacing missing session identity.

## Assumptions

- Session generation is the authoritative stale-event guard and must not be synthesized by handlers.
