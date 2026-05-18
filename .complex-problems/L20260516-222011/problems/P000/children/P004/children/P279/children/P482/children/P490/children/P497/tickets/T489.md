# Attach generation contract hardening ticket

## Problem Definition

P497 must close the attach-generation boundary gap identified by P496. Runtime attach handling and outbox publishing already validate generation, but `build_attach_input_effect()` still accepts an optional generation and can construct an ambiguous effect payload if called incorrectly. Active input delivery should be generation-checked end to end at every boundary that constructs or publishes attach effects.

## Proposed Solution

Tighten `build_attach_input_effect()` so it requires an explicit positive `expected_session_generation` before returning a `SESSION_ATTACH_INPUT` effect. Reuse the existing session generation contract helper instead of introducing a parallel validator. Update focused tests to prove missing, bool, zero, and non-integer generations are rejected at the effect-builder boundary while valid generations still produce the existing attach effect shape.

## Acceptance Criteria

- `build_attach_input_effect()` rejects missing or invalid `expected_session_generation` before constructing the effect.
- Valid attach effects still include `expected_wake_scope_id` and a positive integer `expected_session_generation`.
- Existing attach-race buffering behavior remains intact.
- Existing runtime and outbox generation checks remain strict.
- No no-generation compatibility path is introduced.

## Verification Plan

Run focused attach/session tests after the code change:

- `novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py`
- `novaic-agent-runtime/tests/test_pr248_attach_outbox_cutover.py`
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
- `novaic-agent-runtime/tests/test_pr267_session_outbox_effect_boundary.py`

Also run targeted `rg` checks for `expected_session_generation: int | None`, `SESSION_ATTACH_INPUT`, and attach effect construction to confirm the old optional builder contract is gone.

## Risks

- The generation helper may need to live across package boundaries; use the existing helper rather than duplicating logic.
- Tests may need small fixture updates if they intentionally construct attach effects without generation.
- Attach-race buffering must not become an exception path; stale active-session races should still buffer.

## Assumptions

- P496 correctly found no active direct no-generation attach delivery path.
- The intended production caller already has the current active session generation available.
