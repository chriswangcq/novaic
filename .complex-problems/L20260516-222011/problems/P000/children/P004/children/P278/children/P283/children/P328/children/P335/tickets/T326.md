# Repository finalize generation atomicity

## Problem Definition

`SessionRepository.session_ended(...)` is the mutation boundary that records finalize, clears active session state, and optionally starts a restart from pending input. It currently requires `generation is not None`, but the inventory found `generation=0` can still reach the FSM and be interpreted as "use current generation". That is an unsafe implicit fallback for finalize mutations.

## Proposed Solution

Make repository finalize strict and atomic:

1. Map active-state mutation points inside `session_ended(...)`, `SessionLedgerRepository.record_session_finalized(...)`, pending restart recording, and startup rebuild references.
2. Change repository/FSM behavior so finalize generation must be positive; missing/zero generation cannot fall back to current active generation.
3. Ensure scope/generation checks remain inside the same global transaction as active clearing and pending restart projection.
4. Add tests proving:
   - `generation=0` is rejected before active clear.
   - stale generation is rejected and active session remains unchanged.
   - stale scope is rejected and active session remains unchanged.
   - valid finalize still records reason/generation/remaining_stack and clears/restarts only the intended generation.
5. Run focused finalize/session tests and source guards for zero/current-generation fallback residue in repository/FSM finalize paths.

## Acceptance Criteria

- Repository finalize rejects `generation <= 0`.
- Pure finalize FSM rejects or refuses zero generation instead of falling back to current generation.
- Active clear and pending restart remain in a single transaction after successful generation/scope validation.
- Tests cover zero-generation, stale-generation, stale-scope, and valid finalize behavior.
- No finalize mutation path silently infers generation from current active state.

## Verification Plan

- Run focused tests:
  - `tests/test_pr254_finalize_ownership.py`
  - `tests/test_pr264_session_finalize_fsm_boundary.py`
  - pending restart tests that call `session_ended`.
- Run source guards for `finalize_generation or current_generation` and `generation is None`-only validation in finalize paths.
- Use `py_compile` for changed modules.

## Risks

- Some older tests may assume `generation=0` compatibility; delete/rewrite that compatibility rather than preserving it.
- Strict positive generation may expose upstream payload builders still sending zero; those should be fixed in P336/P337 if outside repository.

## Assumptions

- Backward compatibility for missing or zero finalize generation is not required.
- P336/P337 will handle non-repository payload boundaries, but repository should still fail closed.
