# P400 check: success

## Summary

R383 solves the subagent wake session-generation boundary. The live saga payload builder now requires explicit positive session generation through the shared contract helper, rejects malformed inputs, and no old inline coercion remains.

## Evidence

- `subagent_wake.py` now imports and calls `require_positive_session_generation(ctx, "subagent_wake")`.
- The old optional branch and raw `int(ctx["session_generation"])` are gone.
- Missing, zero, bool, and malformed session generation are covered by tests.
- Related wake/session-init tests pass.

## Criteria Map

- Inspect contract: satisfied; subagent wake is a live session-init payload boundary.
- Replace inline coercion: satisfied by shared contract helper.
- Focused regression tests: satisfied by `test_saga_payload_requires_positive_session_generation`.
- Targeted saga tests: satisfied by 41-test related suite.
- Classification documented: satisfied in R383.

## Execution Map

- R383 patched `novaic-agent-runtime/task_queue/sagas/subagent_wake.py`.
- R383 updated direct builder/session-init tests with explicit generation inputs.

## Stress Test

- The test covers missing, `0`, `True`, and non-numeric string generation values, which are the main cases hidden by the old inline coercion/optional forwarding.

## Residual Risk

- Non-blocking: broader widened matrix remains under P401.

## Result IDs

- R383
