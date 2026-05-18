# P355 success check

## Summary

Success. R339 solves wake-finalize mutation payload propagation: all four mutating payload builders are covered together, all carry required identity, and all reject missing/non-positive generation.

## Evidence

- `tests/test_pr254_finalize_ownership.py` now imports all four wake-finalize payload builders.
- `test_wake_finalize_payload_carries_finalize_contract` asserts:
  - session-ended payload carries generation/finalize/stack contract.
  - Cortex scope-end payload carries `session_generation`, root scope, and wake scope path.
  - sleeping payload carries `scope_id`, `session_generation`, `agent_id`, and `subagent_id`.
  - completed payload carries the same identity and preserves `result: None`.
- `test_wake_finalize_payload_rejects_missing_or_zero_generation` now covers session-ended, Cortex scope-end, sleeping, and completed builders for missing and zero generation.
- Verification from R339: 30-test focused suite passed, 109-test aggregate suite passed, and source guards found no generation defaulting or last-scope residue in `wake_finalize.py`.

## Criteria Map

- Inspect all wake_finalize payload builders: met by source inspection and test coverage.
- Ensure required positive generation and relevant wake/root scope identity are included: met by expanded finalize payload contract test.
- Add tests proving emitted mutation payloads include identity: met.
- Source guards show no missing/zero generation payload generation: met by missing/zero test cases and `rg` guard.

## Execution Map

- Code changed: test-only update in `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`.
- Commands run:
  - `python3 -m py_compile task_queue/sagas/wake_finalize.py`
  - focused 30-test suite
  - aggregate 109-test suite
  - source guard over `wake_finalize.py`

## Stress Test

- Plausible failure mode: a later payload builder is forgotten while Cortex/session payloads are fixed. The expanded test now uses one finalize context to assert all four mutating payload builders, so an omitted sleeping/completed identity field fails in the same contract test.

## Residual Risk

- None for payload propagation. Recovery/compensation identity remains separate under P351, not this payload propagation child.

## Result IDs

- R339
