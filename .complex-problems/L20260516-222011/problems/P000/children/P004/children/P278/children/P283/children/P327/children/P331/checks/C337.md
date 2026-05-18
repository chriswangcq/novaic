# Check: Attach session outbox delivery audit

## Summary

Success. The one-go audit maps outbox attach delivery, adds the missing direct behavior test, and verifies both malformed-effect rejection and preserved downstream task payload fields.

## Evidence

- R316 maps `build_attach_input_effect(...)` and `_publish_attach_input(...)`.
- `_publish_attach_input(...)` raises when `expected_session_generation` is missing before queue publish.
- `test_attach_outbox_delivery_requires_expected_generation` directly asserts missing generation is rejected.
- Existing attach outbox tests assert the published `session.attach_input` payload contains `expected_wake_scope_id` and `expected_session_generation`.
- Focused attach boundary run passed: `26 passed`.

## Criteria Map

- Attach outbox payload parsing and downstream task fields mapped: satisfied by R316.
- Missing `expected_session_generation` rejected before task publish: satisfied by new direct test.
- Published payload includes expected scope/generation: satisfied by `test_pr248_attach_outbox_cutover.py`.
- Verification includes focused outbox/effect tests: satisfied by the two pytest commands in R316.

## Execution Map

- T321 executed one bounded outbox-delivery audit and coverage improvement.
- Changed only test coverage for this slice.

## Stress Test

- Bad outbox effect with message ids and scope but no expected generation now raises before queue publish.
- Happy path still publishes through outbox drain and preserves expected generation.

## Residual Risk

- Non-blocking: runtime-side enforcement and broader stale/missing aggregate coverage remain in P332/P333.

## Result IDs

- R316
