# Direct session-ended delivery residue guard

## Problem

The direct P336 delivery boundary must be free of generation-zero compatibility code after P341/P342. Verify and remove any remaining fallback/defaulting in `wake_finalize`, `session_handlers`, `SagaClient.session_ended`, and `SessionEndedRequest`.

## Success Criteria

- Source search proves the direct delivery boundary has no `session_generation or 0`, `if generation is None`-only validation, or plain non-positive route schema.
- Any remaining direct-boundary residue is removed.
- Focused finalize tests still pass.
