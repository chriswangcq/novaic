# Attach generation hardening verification

## Problem

After hardening the attach effect builder, P497 needs a separate verification pass to prove the change did not break attach-race buffering, runtime generation checks, outbox publication, or legacy cleanup guards.

## Success Criteria

- Focused attach/session tests pass after the hardening change.
- `rg` guard checks show the optional attach builder generation contract is gone.
- Existing attach-race buffering tests still pass.
- No active no-generation `SESSION_ATTACH_INPUT` path remains.

