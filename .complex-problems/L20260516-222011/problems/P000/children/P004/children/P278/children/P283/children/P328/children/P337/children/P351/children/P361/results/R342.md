# Recovery compensation finalize source map result

## Summary

Completed a read-only source map for P361. There are three production sources relevant to synthesized finalize/recovery behavior: normal React-triggered `wake_finalize`, saga failure compensation that creates a new `wake_finalize`, and failed-`wake_finalize` recovery archive that publishes `cortex.scope_end` directly. The source map found two ambiguous areas already covered by downstream P351 child problems: compensation can create `wake_finalize` without rejecting missing generation, and recovery archive currently does not propagate `session_generation` into the direct `cortex.scope_end` payload.

## Done

- Searched production and tests for `wake_finalize`, `finalize`, `compensat*`, `recovery`, `session_generation`, `create_wake_finalize_saga`, and `session_ended`.
- Inspected source files:
  - `queue_service/saga_repo.py` lines 1119-1320 and 1333-1365.
  - `queue_service/session_recovery.py` lines 19-129.
  - `queue_service/session_outbox.py` lines 196-215.
  - `queue_service/session_repo.py` lines 386-418 and 462-630.
  - `queue_service/session_wake_plan.py` lines 34-127.
  - `task_queue/contracts/react_think.py` lines 372-395.
  - `task_queue/contracts/react_actions.py` lines 402-425.
- Inspected representative tests:
  - `tests/test_pr311_saga_compensation_outbox_cutover.py` lines 56-158.
  - `tests/test_pr245_suspected_dead_recovery.py` lines 75-224.

## Verification

- Source map:

| Path | Production source | Output | Identity source | Risk |
| --- | --- | --- | --- | --- |
| Normal React finalization | `react_think.build_trigger_finalize` / `react_actions.build_trigger_finalize_payload` | `wake_finalize` saga context | `ReactThinkInput` / `ReactActionsInput` carry `scope_id`, `agent_root_scope_id`, `wake_scope_path`, `subagent_id`, and positive `session_generation` | Safe under P350/P355 |
| Saga failure compensation | `SagaOrchestrator.mark_failed` for `_WAKE_SAGA_TYPES` → `_build_wake_finalize_compensation_effect` | Saga outbox effect `create_wake_finalize_saga` | Copies `scope_id`, `agent_id`, `subagent_id`, and optional `agent_root_scope_id`, `wake_scope_path`, `session_generation`, stack fields from failed saga context | Ambiguous if failed saga context lacks `session_generation`; currently returns an effect when only `scope_id` and `agent_id` exist |
| Failed wake-finalize recovery | `SagaOrchestrator.mark_failed` when saga type is `wake_finalize` → `record_session_suspected_dead` | Session suspected-dead event | Copies `scope_id`, `wake_scope_path`, `agent_root_scope_id`, `round_num`, `user_id` into suspected-dead payload; event generation comes from session ledger state | Non-mutating session path is safe, but recovery archive payload later lacks `session_generation` |
| Recovery dispatch | `SessionRepository.dispatch` with recovery marker → `build_dispatch_wake_plan` | New recovered `subagent_wake` saga | Uses a new `session_generation` from session ledger and creates a new `scope_id` | Safe for new wake creation |
| Recovery archive | `build_recovery_archive_effect` → `SessionOutboxDispatcher._publish_recovery_archive` | Direct `TaskTopics.CORTEX_SCOPE_END` task | Uses `failed_scope_id`, `agent_root_scope_id`, `wake_scope_path`, `agent_id`, `user_id`, `round_num`; no session generation propagated | Ambiguous/broken after P350 because `cortex.scope_end` now requires positive `session_generation` |

- Test coverage map:
  - Compensation happy path with generation is covered in `test_wake_saga_failure_commits_finalize_creation_effect_before_publish`.
  - Wake-finalize failure becomes suspected-dead event is covered in `test_wake_finalize_failure_commits_suspected_dead_effect_before_publish` and `test_wake_finalize_failure_only_records_suspected_dead_event`.
  - Recovery dispatch with pending inbox is covered in `test_next_dispatch_recovers_from_suspected_dead_event_and_preserves_inbox`.
  - Recovery archive publication is covered in PR-247 tests, but the current source map indicates those tests do not yet require `session_generation` in the archive task payload.

## Known Gaps

- Compensation path gap for P362: `_build_wake_finalize_compensation_effect` creates a `wake_finalize` compensation effect when only `scope_id` and `agent_id` exist, copying `session_generation` only if present.
- Recovery archive gap for P363: `build_recovery_archive_effect` / `_publish_recovery_archive` publish `cortex.scope_end` without `session_generation`, which conflicts with the P350 `cortex.scope_end` identity contract.
- Aggregate verification remains for P364 after P362/P363 are solved.

## Artifacts

- This source map result: `.complex-problems/L20260516-222011/tmp/T349-recovery-compensation-finalize-source-map-result.md`
