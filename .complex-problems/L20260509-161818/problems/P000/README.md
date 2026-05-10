# Runtime current-round projection boundary

## Problem

The Runtime `prepare_llm_call()` contract should pass the current round ID into Cortex step-ref expansion. Without this explicit input, expansion can treat historical tool results as current and allow display/image content from old rounds to re-enter the prompt. This is a core context-bloat guardrail for the shell/display migration.

## Success Criteria

- `prepare_llm_call()` passes `current_round_id=source.round_id` to `expand_messages_for_llm`.
- Unit tests assert the injected dependency receives the current round ID.
- Nearby Runtime contract tests still pass.
- The change is small and deterministic, with no hidden dependencies.
