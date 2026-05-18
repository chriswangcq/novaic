# Subagent finalize status identity guard

## Problem

`task_queue/handlers/subagent_handlers.py::handle_subagent_set_sleeping` and `handle_subagent_set_completed` mutate Business subagent status from finalize-related tasks using only coarse agent/subagent identity. A stale finalize task may incorrectly move a currently active subagent to sleeping/completed unless the handler checks wake/session identity or the mutation is proven harmless.

This child belongs under P350 because Business status mutation was identified as a live stale-finalize risk in P348.

## Success Criteria

- Inspect subagent status payload builders in `wake_finalize` and the Business handlers that mutate status.
- Add explicit expected wake/session identity checks before status mutation, or document why the status transition is structurally independent from wake finalization.
- Add tests for missing identity and stale identity.
- Remove any compatibility path that lets missing identity mutate status.
