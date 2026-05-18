# PR-302 — Session Outbox Worker Production Wiring

Status: Closed

## Goal

Close the durable wake creation gap: `dispatch()` and `session_ended()` now
return durable queued acknowledgements only after writing `tq_session_outbox`,
so production must run a visible worker that drains those effects.

## Problem

`SessionOutboxWorker` existed as a tested substrate, but no production entrypoint
or startup script launched it. That left `create_wake_saga` rows pending and
could strand sessions in `starting` even though callers saw `wake_start_queued`.

## Scope

- Add a `main_novaic.py session-outbox-worker` subprocess mode.
- Wire `scripts/start.sh` to launch the worker.
- Expose session outbox and `starting` backlog diagnostics in Queue `/ready`.
- Remove the stale shared `saga_started` / `saga_start_pending` dispatch
  compatibility surface so callers only treat `wake_start_queued` as the
  current wake-start contract.
- Add regression tests proving the worker mode, startup script, and readiness
  diagnostics stay wired.

## Acceptance Criteria

- Production startup launches a visible `session-outbox-worker` process.
- The worker owns no business decision; it only drains committed durable effects.
- Queue `/ready` exposes pending/dead-letter outbox counts and starting session
  count so a missing worker is diagnosable.
- Scheduler, subscriber, and shared assembler tests use the queued wake
  contract; the old synchronous start return is no longer a normal branch.
- Tests fail if the production wiring disappears.

## Verification

- `pytest tests/test_pr302_session_outbox_worker_production_wiring.py`
- Targeted runtime/common tests around outbox worker and dispatch contract.
- Full runtime suite: `367 passed`.
- Common suite with runtime contract path: `140 passed`.
- Business subscriber/aggregation tests: `41 passed`.
- Smoke-started `session-outbox-worker`, confirmed it initialized `queue.db`
  and shut down cleanly on SIGTERM.

## Closure Notes

- Added `run_session_outbox_worker()` in `novaic-agent-runtime/main_novaic.py`.
- `scripts/start.sh` now starts the worker as a standalone subprocess and writes
  logs to `session-outbox-worker.log`.
- Queue `/ready` now includes `session_outbox.pending_count`,
  `session_outbox.dead_letter_count`, and `session_state.starting_count`.
- Cleaned a stale subscriber comment that still referred to retired
  `pending_triggers`.
- Removed `saga_started` / `saga_start_pending` from the shared dispatch
  contract and scheduler normal branch. Session harness event vocabulary now
  records queued wake intent as `dispatch_wake_start_queued`.
