# Task Saga Worker FSM Focused Tests

## Problem

Run the focused selected tests covering generic FSM substrate, task queue FSM, saga FSM, worker lease, generic worker, queue control plane, and busy/recovery behavior.

## Success Criteria

- The selected task/saga/worker pytest subset exits successfully.
- Exact command, file count, and pytest pass count are recorded.
- Failures are captured for follow-up instead of hidden.
