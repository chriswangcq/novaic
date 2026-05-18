# Wake finalize stack strictness check

## Summary

Success. R480 satisfies P494: the finalizer no longer fabricates `remaining_stack`, producers provide explicit stack payloads, compensation has an explicit unknown-stack boundary, and focused tests/guards support the change.

## Evidence

- `task_queue/sagas/wake_finalize.py` raises `ValueError("remaining_stack is required for wake_finalize")` when no dict stack is present.
- `queue_service/saga_repo.py` uses `_compensation_remaining_stack()` so compensation contexts always include explicit stack state.
- React producers no longer emit `stack_depth_at_finalize` or `stack_known_at_finalize`.
- Test log: `.complex-problems/L20260516-222011/tmp/p494/wake-finalize-strictness-tests.log` with `53 passed`.
- Guard log: `.complex-problems/L20260516-222011/tmp/p494/wake-finalize-strictness-guards.txt`.

## Criteria Map

- Compensation context always carries explicit `remaining_stack`: satisfied by `_compensation_remaining_stack()` and the new compensation test.
- `wake_finalize.py` rejects missing/non-dict stack: satisfied by implementation and updated finalize ownership tests.
- Fallback synthesis removed from finalizer logic: satisfied by guard showing no legacy stack fields in covered finalizer/producers.
- Focused tests pass: satisfied by `53 passed`.

## Execution Map

- T485 ran as a bounded one-go implementation.
- It updated producer/finalizer code, updated tests, ran focused verification, and recorded R480.

## Stress Test

- Plausible failure mode: a failed `react_think` saga has no stack snapshot and compensation still creates a bad `wake_finalize` context. The new test `test_wake_saga_failure_without_stack_uses_explicit_unknown_stack` covers exactly this case and proves the finalizer receives a valid explicit unknown stack.

## Residual Risk

- Recovery archive fallback remains intentionally outside P494 and is tracked under P491. It does not block P494 because it is not a `wake_finalize` producer.

## Result IDs

- R480
