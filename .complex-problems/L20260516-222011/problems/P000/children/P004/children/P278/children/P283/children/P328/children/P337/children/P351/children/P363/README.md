# Session recovery missing identity handling

## Problem

Session recovery paths may reconstruct finalize or dead-session handling from incomplete persisted state. Missing generation or wake scope identity must not be allowed to mutate a newer active session. This belongs under P351 because recovery is the other source of synthesized finalize contexts.

## Success Criteria

- Inspect session recovery behavior for missing `session_generation`, `scope_id`, and wake scope path.
- Ensure incomplete identity is rejected or routed to a clearly non-mutating dead-session/recovery path.
- Add tests for missing generation and stale generation recovery cases.
- Ensure the fix does not recreate old fallback behavior under a different name.
