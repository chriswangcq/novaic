# Attach effect builder strict generation boundary

## Problem

`build_attach_input_effect()` still accepts an optional `expected_session_generation`, which makes the attach effect construction boundary weaker than the runtime handler and outbox publisher boundaries. The builder should reject missing or invalid generation values before constructing a `SESSION_ATTACH_INPUT` effect.

## Success Criteria

- `build_attach_input_effect()` requires and validates a positive explicit `expected_session_generation`.
- The builder reuses the existing session generation contract helper instead of duplicating validation.
- Focused tests prove missing, bool, zero, and invalid generation values are rejected at the builder boundary.
- Valid attach effects keep the existing payload shape with `expected_wake_scope_id` and positive integer `expected_session_generation`.

