# Queue FSM Focused Test Execution

## Problem

Run the focused queue/session/FSM/outbox/finalize tests identified by the inventory.

## Success Criteria

- Focused test command exits successfully, or failures are captured with enough detail for follow-up.
- Exact command, pytest counts, and log path are recorded.
- Test scope covers dispatch, session state, outbox, finalize, recovery, saga compensation, and FSM decisions.
