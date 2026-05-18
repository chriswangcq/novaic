# Session outbox dispatcher boundary hardening

## Boundary Decision

`queue_service/session_outbox.py` remains the required production boundary where durable session outbox effects become external side effects:

- `CREATE_WAKE_SAGA` -> `self.saga_orchestrator.create(...)`
- `RECOVERY_ARCHIVE_SCOPE` -> `self.queue.publish(TaskTopics.CORTEX_SCOPE_END, ...)`
- `PUBLISH_ATTACH_INPUT` -> `self.queue.publish(TaskTopics.CORTEX_APPEND_MESSAGES, ...)`

## Hardening Added

- Added `test_session_owned_queue_publish_effects_stay_in_session_outbox_dispatcher` to `novaic-agent-runtime/tests/test_pr277_session_outbox_required_saga_orchestrator.py`.
- The guard asserts:
  - `session_outbox.py` has exactly two `self.queue.publish(` calls.
  - `session_repo.py` does not call `queue.publish(`.
  - `session_wake_plan.py` does not call `queue.publish(`.
  - `session_repo.py` and `session_wake_plan.py` do not call `.saga_orchestrator.create(`.

## Verification

- `python -m pytest tests/test_pr277_session_outbox_required_saga_orchestrator.py tests/test_pr274_session_repository_orchestrator_residue_removal.py tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr251_wake_creation_outbox_cutover.py`
- Result: `31 passed in 0.23s`

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p486/session-outbox-boundary-tests.log`
- `.complex-problems/L20260516-222011/tmp/p486/session-outbox-boundary-tests.exit`
