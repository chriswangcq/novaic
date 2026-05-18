# P501 recovery/session-ended contract classification

## Raw Evidence

- Raw guard output: `.complex-problems/L20260516-222011/tmp/p501/recovery-session-contract-raw-guards.txt` (`457` lines)
- Production-focused output: `.complex-problems/L20260516-222011/tmp/p501/recovery-session-production-hits.txt` (`87` lines)
- File list: `.complex-problems/L20260516-222011/tmp/p501/recovery-session-contract-files.txt`

## Strict Session-Ended Contract

- `novaic-agent-runtime/task_queue/handlers/session_handlers.py`
  - Requires `agent_id`, `subagent_id`, `scope_id`, `finalize_reason`, positive `generation`, and object `remaining_stack`.
  - Rejects missing or invalid `remaining_stack` before calling the coordinator.
- `novaic-agent-runtime/queue_service/session_repo.py`
  - `session_ended()` requires `finalize_reason`, positive `generation`, and non-`None` `remaining_stack`.
  - Records `session_finalized` with explicit `remaining_stack`.
  - Rejects stale finalizes via the session FSM instead of mutating active session state.

## Recovery/Suspected-Dead Strict Pieces

- `novaic-agent-runtime/queue_service/saga_repo.py`
  - Wake finalize failure records a durable `SESSION_SUSPECTED_DEAD` ledger event through saga outbox.
  - The event generation is read from the current session ledger state via `require_positive_session_generation_value()`.
  - The outbox effect includes the full `saga_context` in the payload before recording.
- `novaic-agent-runtime/queue_service/session_repo.py`
  - Dispatch detects a suspected-dead event for the active scope, records `SESSION_SUSPECTED_DEAD_OBSERVED`, clears active saga from runtime state, and builds a recovered wake plan from pending inbox.
  - This path does not treat the broken wake as a healthy active session.

## Cleanup Candidates for P502

- `novaic-agent-runtime/queue_service/saga_repo.py`
  - `_record_session_suspected_dead_event()` receives full `saga_context` but only writes selected fields into the suspected-dead event payload.
  - It does not preserve `remaining_stack`, `stack_known_at_finalize`, or `stack_depth_at_finalize` into the event payload.
- `novaic-agent-runtime/queue_service/session_recovery.py`
  - `build_recovery_archive_effect()` falls back from missing `remaining_stack` to a synthesized stack using `stack_known_at_finalize` / `stack_depth_at_finalize`.
  - Because upstream currently drops those diagnostics, missing metadata can become `{"known": True, "depth": 0, "frames": []}`, which is a silent known-empty stack.
- Recovery tests currently expect known-empty fallback in failed-finalize simulations that do not provide stack diagnostics. These tests should be tightened once the production payload preserves explicit stack metadata or explicitly marks it unknown.

## Existing Guard Tests

- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
  - Guards explicit finalize ownership and required `remaining_stack`.
- `novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py`
  - Covers recovery marker/archive helper shapes and current stack fallback behavior.
- `novaic-agent-runtime/tests/test_pr247_recovery_outbox_cutover.py`
  - Covers recovery archive outbox publication/retry and required archive publisher payload fields.
- `novaic-agent-runtime/tests/test_pr245_suspected_dead_recovery.py`
  - Covers suspected-dead recovery flow and pending inbox preservation.
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
  - Guards required session-ended contract fields.

## Conclusion

The session-ended contract is strict, but suspected-dead recovery still has a stack-diagnostics gap. P502 should preserve explicit stack diagnostics in suspected-dead events and make unknown-stack recovery explicit instead of silently synthesizing a known empty stack.
