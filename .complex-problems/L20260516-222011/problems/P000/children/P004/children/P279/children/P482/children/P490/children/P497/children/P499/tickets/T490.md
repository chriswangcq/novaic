# Attach builder strictness implementation ticket

## Problem Definition

`build_attach_input_effect()` can currently be called with `expected_session_generation=None`, leaving a weaker builder-level contract than the outbox publisher and runtime handler. This makes the attach generation invariant depend on later layers instead of being explicit at the effect construction boundary.

## Proposed Solution

Update the builder in `novaic-agent-runtime/queue_service/session_effects.py` to require a positive explicit generation using the existing `require_positive_session_generation_value()` helper. Add focused tests in the session outbox/effect boundary test suite for invalid builder inputs and a valid payload shape.

## Acceptance Criteria

- The builder type and runtime behavior no longer accept missing generation as a valid attach effect input.
- Invalid values including `None`, `True`, `0`, and non-integer text are rejected with a clear `ValueError`.
- A valid generation produces an attach effect with unchanged effect type and payload fields.
- No duplicate generation validation helper is introduced.

## Verification Plan

Run focused tests around attach generation and effect boundaries, then run targeted guards:

- `python -m pytest tests/test_pr238_generation_checked_attach.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr267_session_outbox_effect_boundary.py`
- `rg "expected_session_generation: int \\| None|build_attach_input_effect|SESSION_ATTACH_INPUT" novaic-agent-runtime/queue_service novaic-agent-runtime/tests`

## Risks

- Tests may have fixture calls that relied on optional generation and need to be updated to the explicit contract.
- Importing the existing helper must avoid circular imports.

## Assumptions

- `task_queue.contracts.session_generation.require_positive_session_generation_value` is the canonical helper already used at the outbox boundary.
