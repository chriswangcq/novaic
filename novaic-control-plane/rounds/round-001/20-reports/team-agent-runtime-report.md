# Round 001 Report - Agent Runtime Team (Minimal)

- task: Create `split-plan/agent-runtime-extraction-paths.md` for worker/handler modules moving out.
- evidence:
  - command: `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - summary: `PASS (3 passed)`; extraction scope aligns with current retry/idempotency worker execution paths.
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/agent-runtime-extraction-paths.md`

- task: Create `split-plan/agent-runtime-reliability-baseline.md` with retry/idempotency critical checks and expected outcomes.
- evidence:
  - command: `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
  - summary: `PASS (4 passed)` with baseline metrics `HIGH_LOAD_REPLAY_METRICS concurrency=80 elapsed_sec=0.066 throughput_ops_per_sec=1210.23 exactly_once_winner=0`.
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/agent-runtime-reliability-baseline.md`

- task: Run worker replay checks and capture baseline throughput/retry evidence for post-split comparison.
- evidence:
  - command: `novaic-backend/scripts/run_idempotency_replay_ci.sh`
  - summary: `PASS` (unit replay + integration replay + diagnostics policy marker checks).
  - artifact_path: `novaic-backend/scripts/run_idempotency_replay_ci.sh`

- status: DONE
- blocker: NONE
