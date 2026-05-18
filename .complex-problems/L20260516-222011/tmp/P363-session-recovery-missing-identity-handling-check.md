# P363 session recovery identity check

## Summary

Success. R344 solves P363. Recovery archive now requires positive generation at marker/effect/publisher boundaries and carries it into the direct `cortex.scope_end` task.

## Evidence

- `recovery_marker_from_suspected_dead_event` preserves positive event generation as marker `session_generation`.
- `build_recovery_archive_effect` returns `None` when failed scope or positive generation is missing.
- `_publish_recovery_archive` rejects missing, zero, malformed, or boolean generation before queue publish.
- Published recovery archive `TaskTopics.CORTEX_SCOPE_END` payload includes validated `session_generation`.
- Tests passed:
  - focused recovery set: `35 passed in 0.62s`;
  - broader recovery/compensation/finalize set: `39 passed in 0.36s`.

## Criteria Map

- Inspect recovery behavior for missing `session_generation`, `scope_id`, and wake scope path: satisfied by P361 source map and R344 implementation notes.
- Ensure incomplete identity is rejected or routed to non-mutating recovery path: satisfied by `build_recovery_archive_effect` returning `None` and publisher-level rejection before queue publish.
- Add tests for missing generation and stale generation recovery cases: missing/invalid generation is covered at effect-builder and publisher levels; positive generation propagation is covered through real recovery archive publish tests.
- Ensure the fix does not recreate old fallback behavior: satisfied by explicit positive generation validation and no default-to-zero path in the recovery archive flow.

## Execution Map

- Recovery marker/effect builder changes live in `queue_service/session_recovery.py`.
- Durable outbox publisher validation lives in `queue_service/session_outbox.py`.
- Boundary tests live in `tests/test_pr266_session_recovery_boundary.py`.
- End-to-end recovery archive outbox tests live in `tests/test_pr247_recovery_outbox_cutover.py`.

## Stress Test

The one-go result was stress-tested with malformed recovery archive generation values: missing, `0`, `"0"`, `"not-an-int"`, and `False`. The publisher rejects all of them and no recovery archive task is created.

## Residual Risk

- Non-blocking: malformed historical suspected-dead events without generation will not archive the failed scope. This is intentional because the user does not want backward-compatible ambiguous mutation.

## Result IDs

- R344
