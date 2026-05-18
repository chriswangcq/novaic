# Update PR-252 attach state test for worker-owned outbox

## Problem

`test_active_session_state_routes_attach` in `test_pr252_session_state_ssot.py` still asserts old synchronous attach task publication. It should assert the current worker-owned contract: dispatch writes the session outbox row with expected generation, and explicit session outbox drain publishes the task.

## Success Criteria

- The test no longer expects `tq_tasks` attach task before outbox drain.
- The test still verifies active session state routes attach and preserves expected session generation.
- The test explicitly drains pending session outbox and then verifies the published task payload.
- The focused PR-252 test and rebuild/projection coverage set pass.
