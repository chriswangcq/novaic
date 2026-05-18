# Child Problem: runtime finalizer legacy-negative fixtures

## Problem

Finalizer tests use `im_reply` to prove old direct reply calls do not trigger shell-first finalization behavior. These are valid negative fixtures, but the naming and comments should consistently say legacy direct reply.

## Success Criteria

- All finalizer `im_reply` fixtures are explicitly legacy-negative cases.
- Current successful reply-finalize tests use shell `agentctl im reply`.
- Focused finalizer test passes.
