# Round 001 Agent Runtime Reliability Baseline

## Scope

- retry behavior for task/saga worker loops
- idempotency guard behavior under contention and restart
- replayable baseline commands for post-split comparison

## Critical checks and expected outcomes

| check_id | command | expected_outcome | baseline_result_round001 |
|---|---|---|---|
| AR-R1 | `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py` | retry policy and idempotency unit assertions pass | `3 passed` |
| AR-R2 | `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py` | contention guard correctness + restart takeover + high-load replay pass | `4 passed` |
| AR-R3 | `novaic-backend/scripts/run_idempotency_replay_ci.sh` | unit+integration replay and diagnostics marker checks pass | `PASS` |

## Replay metrics baseline (Round 001)

- Source command: `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- Captured line:
  - `HIGH_LOAD_REPLAY_METRICS concurrency=80 elapsed_sec=0.066 throughput_ops_per_sec=1210.23 exactly_once_winner=0`
- Baseline interpretation:
  - contention scenario at concurrency `80` preserved exactly-once winner semantics (`exactly_once_winner=0`)
  - replay throughput baseline for future split comparison: `1210.23 ops/s`

## Guardrails for post-split acceptance

1. Keep the same replay command interface in target repo so non-authors can rerun checks.
2. Fail split validation if any of AR-R1/AR-R2/AR-R3 is not passing.
3. Treat throughput regression >20% from `1210.23 ops/s` as `DONE_WITH_GAPS` until explained.
4. Keep diagnostics defaults aligned with `contracts/AGENT_RUNTIME_DIAGNOSTICS_POLICY.md`.

## Artifact paths used for this baseline

- `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
