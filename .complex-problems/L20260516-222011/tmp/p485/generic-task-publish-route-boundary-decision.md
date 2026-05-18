# Generic task publish route boundary decision

## Decision

Retain `/tasks/publish` as a generic internal task queue adapter boundary, with explicit regression guards.

## Rationale

- The route delegates directly to `TaskQueue.publish` and does not create sagas.
- It is generic queue infrastructure, not a session-owned wake/scope side-effect path.
- The nearby generic saga creation route already rejects session-owned saga types; this ticket adds equivalent clarity for the generic task publish route by guarding that it does not touch session-owned effect logic.

## Code Change

- Added `_FakeQueue` and two focused tests in `novaic-agent-runtime/tests/test_saga_creation_policy_boundary.py`.
- `test_generic_task_publish_route_is_only_queue_adapter_boundary` proves the route forwards the task payload to `queue.publish` and does not invoke the orchestrator.
- `test_generic_task_publish_route_contains_no_session_owned_effect_logic` proves the publish route section does not contain `subagent_wake`, `SessionOutboxDispatcher`, `build_create_wake_saga_effect`, `orchestrator`, or `saga_type`.

## Verification

- `python -m pytest tests/test_saga_creation_policy_boundary.py`
- Result: `6 passed in 0.22s`

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p485/saga-creation-policy-boundary-tests.log`
- `.complex-problems/L20260516-222011/tmp/p485/saga-creation-policy-boundary-tests.exit`
