# Widened guard residue matrix result

## Summary

The final narrow guard is clean. The widened guard still has 47 textual hits, but they are now classified and none are unclassified live session-generation or event-generation authority. During the matrix pass, one additional live session event authority issue was found and fixed: `saga_repo._record_session_suspected_dead_event` no longer writes suspected-dead session events with generation `0` when session state is missing.

## Done

- Reran the narrow guard after the P399/P400 fixes: zero hits.
- Reran the widened guard: 47 hits after the suspected-dead patch.
- Patched `novaic-agent-runtime/queue_service/saga_repo.py` to reject missing session state before writing `session_suspected_dead`, and to validate the session generation with `require_positive_session_generation_value`.
- Added regression coverage proving orphan wake-finalize failure does not write a generation-0 suspected-dead event.
- Updated saga compensation test setup to seed explicit session state before expecting a suspected-dead event.
- Classified every remaining widened hit into a non-session-authority bucket.

## Verification

- Narrow guard: `p401-narrow-guard-final.txt` has `0` lines.
- Widened guard: `p401-widened-guard-final.txt` has `47` classified lines.
- Focused runtime suite passed: `147 passed in 0.79s`.
- Suspected-dead focused suite passed: `22 passed in 0.24s`.
- Subagent wake/session-init focused suite passed: `41 passed in 0.34s`.
- Cortex API counter/round tests passed with explicit dependencies: `21 passed in 0.38s`.

## Known Gaps

- The widened guard intentionally still matches legitimate generic counters and generic FSM generations. They are classified below rather than removed because they are not session-generation authority.
- Cortex tests require `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk`; without those service-module paths, collection fails on missing `logicalfs`/`sandbox_sdk`.

## Artifacts

- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/tests/test_pr245_suspected_dead_recovery.py`
- `novaic-agent-runtime/tests/test_pr311_saga_compensation_outbox_cutover.py`
- `.complex-problems/L20260516-222011/tmp/p401-narrow-guard-final.txt`
- `.complex-problems/L20260516-222011/tmp/p401-widened-guard-final.txt`

## Widened Guard Classification Matrix

| Bucket | Files / hits | Classification |
| --- | --- | --- |
| Archive round metadata | `queue_service/session_outbox.py:225`, `task_queue/handlers/cortex_handlers.py:117` | `round_num` archive metadata. Not session generation; session generation in the same paths is already validated with `require_positive_session_generation*`. |
| Cortex meta counters and rounds | `novaic-cortex/novaic_cortex/api.py:1523`, `api.py:1547`, `task_queue/utils/cortex_bridge.py:307`, `:318`, `novaic-cortex/novaic_cortex/shell_capabilities.py:616` | Runtime/Cortex metadata counters and round increments. Not session authority; guarded by API/client tests. |
| Generic task FSM generation | `queue_service/task_fsm.py:108`, `:302`, `queue_service/queue_db.py:1225`, `:1232`, `:1308` | Task FSM internal generation, not session generation. Covered by task/generic FSM tests. |
| Generic saga FSM generation | `queue_service/saga_fsm.py:120`, `:342`, `queue_service/saga_repo.py:913`, `:920`, `:980` | Saga FSM internal generation, not session generation. Covered by saga/generic FSM tests. |
| Generic lease FSM generation | `queue_service/lease_fsm.py:94`, `:193`, `queue_service/saga_repo.py:1048`, `:1083`, `queue_service/queue_db.py:1366`, `:1401` | Lease FSM internal generation, not session generation. Covered by lease/generic FSM tests. |
| Queue audit generation readers | `queue_service/queue_audit.py:80`, `:96`, `:121` | Audit/replay readers with named validators (`_optional_int`, `_required_non_negative_int`). Not silent live authority. |
| Task retry/version counters | `queue_service/task_fsm.py:132`, `queue_service/queue_db.py:1214`, `:1233`, `:1234`, `:1335`, `task_queue/workers/task_execution.py:149` | Retry/version counters and task retry policy. Not session authority. |
| Worker metrics/health counters | `task_queue/workers/task_worker.py:82-84`, `task_queue/workers/health_action_specs.py:40`, `:48`, `:49`, `queue_service/queue_db.py:1070` | Metrics/status/contention counters. Not control-plane generation. |
| React loop counters/stack depth | `task_queue/contracts/react_think.py:65`, `:66`, `:263`, `:376`, `task_queue/contracts/react_actions.py:70`, `:294`, `:381`, `:394` | Retry counters and stack depth snapshots for loop decisions. Not session generation; session generation in these contracts is separately required positive. |
