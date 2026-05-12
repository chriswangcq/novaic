# FSM idempotency repair result

## Summary

Implemented the generic FSM substrate fix so duplicate transition event idempotency is side-effect free.

## Done

- Added `FsmAppendResult` and `FsmSqliteStore.append_event_result()` to report whether an event append inserted a new row or reused an existing idempotent row.
- Preserved the existing `FsmSqliteStore.append_event()` string return contract.
- Updated `FsmTransitionRunner.record()` to return immediately on duplicate event replay before state or outbox writes.
- Added a regression test proving duplicate transition replay does not rematerialize state or append outbox effects.

## Verification

- Ran `PYTHONPATH=. pytest -q tests/test_pr342_generic_fsm_transition_runner.py tests/test_pr259_generic_fsm_store_outbox.py`.
- Result: `10 passed in 0.08s`.

## Known Gaps

- None for the duplicate transition state/outbox corruption path.

## Artifacts

- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
- `novaic-agent-runtime/queue_service/fsm/runner.py`
- `novaic-agent-runtime/tests/test_pr342_generic_fsm_transition_runner.py`
