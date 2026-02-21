# Round 002 Agent Runtime Replay Comparison Method

## Goal

Provide pre/post split comparison method for throughput, retry, and idempotency checks with replayable commands.

## Baseline execution commands (pre-split)

1. `novaic-backend/scripts/run_idempotency_replay_ci.sh`
2. `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

## Required expected markers

- from command (1): `[idempotency-ci] PASS`
- from command (2):
  - `HIGH_LOAD_REPLAY_METRICS`
  - `4 passed`

## Round 002 baseline snapshot

- command (1) result: PASS
- command (2) metrics line:
  - `HIGH_LOAD_REPLAY_METRICS concurrency=80 elapsed_sec=0.067 throughput_ops_per_sec=1199.23 exactly_once_winner=0`

## Post-split comparison procedure

1. Run the same two commands in the extracted candidate with equivalent data/config.
2. Confirm markers still present:
   - `[idempotency-ci] PASS`
   - `HIGH_LOAD_REPLAY_METRICS`
   - `4 passed`
3. Compare throughput:
   - baseline: `1199.23 ops/s`
   - regression threshold: >20% drop => mark `DONE_WITH_GAPS` and file decision-needed with owner/target_round.
4. Confirm exactly-once signal:
   - expected `exactly_once_winner=0` for this replay profile.

## Artifact references

- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `novaic-control-plane/rounds/round-002/split-exec/agent-runtime-package-boundary.md`
