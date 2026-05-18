# Unit Tool Output and Task Queue Focused Tests

## Problem

Run the focused selected unit tests under `tests/unit/task_queue` and other focused boundary tests that guard shell/tool output, retry/replay, saga worker boundary, and explicit dependencies.

## Success Criteria

- The selected unit/boundary pytest subset exits successfully.
- Exact command, file count, and pytest pass count are recorded.
- Failures are captured for follow-up instead of hidden.
