# P362 compensation generation preservation check

## Summary

Success. R343 solves P362. The compensation path now preserves positive generation and refuses to synthesize ambiguous `wake_finalize` compensation work when generation is missing or invalid.

## Evidence

- `queue_service/saga_repo.py` now validates compensation source generation with `_positive_session_generation_from_context`.
- `_build_wake_finalize_compensation_effect` returns no effect unless `scope_id`, `agent_id`, and positive `session_generation` are present.
- Valid compensation contexts still produce `create_wake_finalize_saga` and preserve generation.
- Tests cover missing, zero, string-zero, malformed, and boolean generation values.
- Focused tests passed: `9 passed in 0.15s`.
- Broader related tests passed: `23 passed in 0.33s`.

## Criteria Map

- Preserve `scope_id`, wake/root scope identity, subagent identity, and positive session generation: satisfied for valid contexts; test asserts context fields and `session_generation == 7`.
- Remove compatibility fallback that defaults or omits generation: satisfied by rejecting missing/invalid generation and no longer copying `session_generation` through optional fallback.
- Add focused tests proving valid generation preservation: satisfied by updated compensation outbox test.
- Add focused tests proving missing/invalid generation does not create ambiguous mutating finalize task: satisfied by parameterized negative test.

## Execution Map

- Production change is limited to the compensation effect builder in `queue_service/saga_repo.py`.
- Test change is limited to `tests/test_pr311_saga_compensation_outbox_cutover.py`.
- No unrelated runtime paths were intentionally changed.

## Stress Test

Stress case: a failed `subagent_wake` saga with `scope_id` and `agent_id` but no positive generation. Before this fix it could still emit `wake_finalize`; after the fix the test proves no pending outbox effect is recorded and no `wake-finalize-*-comp` saga is created.

## Residual Risk

- Non-blocking: suppressing finalize compensation for malformed old contexts means no cleanup saga is created from that corrupted record. This is preferable to ambiguous mutation and matches the user's no-backward-compatibility principle.
- P363 still owns recovery archive propagation.

## Result IDs

- R343
