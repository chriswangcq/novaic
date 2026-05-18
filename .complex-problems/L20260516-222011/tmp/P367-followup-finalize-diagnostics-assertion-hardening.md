# Finalize Diagnostics Assertion Hardening

## Problem

`SessionRepository.session_ended` appears to bind finalize diagnostics correctly, but the tests do not yet prove the binding sharply enough. Harden the queue session finalize tests so stale finalize diagnostics cannot be accidentally recorded as valid close metadata and valid finalize metadata cannot diverge between finalized and closed events.

## Success Criteria

- Valid finalize test asserts `session_finalized` generation and payload include the intended `finalize_reason`, `finalize_generation`, `ended_scope_id`, and `remaining_stack`.
- Valid finalize test asserts `session_closed` event generation and metadata exactly match the explicit finalize metadata.
- Generation mismatch rejection test asserts active session remains unchanged, no `session_finalized` event is emitted, and `session_finalize_rejected` payload records the stale finalize's own reason, generation, scope, and remaining stack.
- Scope mismatch rejection test asserts active session remains unchanged, no `session_finalized` event is emitted, and `session_finalize_rejected` payload records the stale scope finalize metadata.
- Focused session finalize and pending restart tests pass.
- Residue search shows no direct ambiguous `remaining_stack` or `finalize_reason` writes outside the explicit finalize metadata path.
