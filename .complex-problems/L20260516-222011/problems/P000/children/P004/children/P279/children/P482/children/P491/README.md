# Recovery and session-ended compatibility cleanup

## Problem

Recovery and session-ended paths must not mutate active-session state outside the FSM contract or preserve old fallback behavior for dead sessions. Watchdog and recovery should produce explicit recovery/session-ended semantics without silently treating a broken wake as normally resumable. This belongs under P482 because recovery is where stale compatibility tends to survive after dispatch migration.

## Success Criteria

- Recovery and session-ended production paths are inspected against the P482 inventory.
- Direct active-session mutation outside the accepted repository/FSM boundary is removed or justified with a guard test.
- Dead/suspected-dead recovery behavior is explicit and generation-aware.
- Focused recovery/session-ended tests pass.
