# FSM idempotency repair check

## Summary

The duplicate transition replay bug is fixed at the generic FSM substrate layer.

## Evidence

- `FsmSqliteStore.append_event_result()` exposes `inserted=True/False`.
- `FsmTransitionRunner.record()` skips materialized state and outbox writes on `inserted=False`.
- Regression test exercises a session-style transition replay with a different scope/saga and verifies state remains on the first scope and only one outbox row exists.
- Targeted tests passed.

## Criteria Map

- Existing `append_event()` return contract preserved: met by wrapper returning `.id` and existing generic store tests passing.
- Duplicate replay detected: met by `FsmAppendResult.inserted`.
- State unchanged: met by regression assertion `active_scope_id == "scope-1"`.
- No replay outbox: met by regression assertion only `outbox-1` exists and replay result has empty `outbox_ids`.

## Execution Map

- Code changed in generic store/runner, not session-specific business branches.
- Test added to the generic transition runner test file.

## Stress Test

- The regression attempts exactly the production failure shape: same event idempotency key, new event ID, new scope, new saga, and a new outbox effect.

## Residual Risk

- Concurrent racing duplicates rely on the store insert result, so the race path is covered by the unique violation branch.

## Result IDs

- R001
