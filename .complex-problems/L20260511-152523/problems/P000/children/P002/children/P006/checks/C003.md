# Wake finalize compensation check

## Summary

The compensation-context repair satisfies P006: failure compensation now keeps the explicit data needed for Cortex archive and session finalization instead of narrowing the context to scope/user ids.

## Evidence

- Durable outbox test confirms compensation effect context preserves `agent_root_scope_id`, `wake_scope_path`, `session_generation`, `round_num`, and `remaining_stack`.
- Published saga assertion confirms the created `wake_finalize` saga keeps the same fields.
- Payload-builder assertions confirm preserved context produces correct `cortex_scope_end` and `session_ended` payloads.
- Existing recovery tests still pass.

## Criteria Map

- Preserve root/path/session generation -> proven in `test_wake_saga_failure_commits_finalize_creation_effect_before_publish`.
- Do not invent fallback guesses -> implementation copies only keys present in failed saga context.
- Keep recovery behavior intact -> proven by suspected-dead and active-inbox tests.

## Execution Map

- `T005` / `R003` -> compensation context patch plus focused saga/recovery tests.

## Stress Test

- If compensation again drops root/path, the `cortex_scope_end` payload assertions fail.
- If compensation again drops session generation, the `session_ended` payload assertion fails.
- If the saga outbox publishes a narrowed context, the post-drain finalize saga assertions fail.

## Residual Risk

- If an upstream saga is created without root/path/session metadata, compensation will not fabricate it. That is deliberate; a separate upstream-contract test should catch such missing input if it appears.

## Result IDs

- R003

## Blocking Gaps

- none
