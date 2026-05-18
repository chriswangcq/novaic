# Close attach worker-only cutover gaps

## Problem

The attach worker-only cutover is partially implemented but not verified. Dispatch still crashes on a stale `task_id` log assumption, the wrapper boundary test still guards an older source shape, and focused compile/test verification must be rerun with correct paths. Close only these concrete gaps without expanding scope.

## Success Criteria

- Active attach dispatch no longer references `task_id` and returns a stable worker-only result with `delivery=outbox_pending` and `outbox_id`.
- Session outbox dispatcher no longer exposes or uses a repository-owned `publish_attach_input_effect` wrapper.
- Boundary/source tests assert the current generic outbox wrapper shape rather than stale single-effect assumptions.
- Correct focused py_compile and pytest commands pass from the `novaic-agent-runtime` working directory.
- No new eager attach publish path is introduced.
