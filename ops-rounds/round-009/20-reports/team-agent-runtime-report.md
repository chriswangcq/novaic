# Round 009 Report - Agent Runtime Team

## Implemented Work
- Task: Run diagnostics policy checks in main CI flow (not replay-only)
  - owner: Agent Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - dependencies:
    - existing policy check script in backend scripts
  - risk_level: low
  - evidence:
    - artifact_path: `.github/workflows/ci.yml`
    - summary: Python CI job新增 `Agent runtime diagnostics policy gate`，执行 `python scripts/check_idempotency_diagnostics_policy.py`

- Task: Replay idempotency suites and attach final metrics snapshot
  - owner: Agent Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - dependencies:
    - replay scripts and tests are executable
  - risk_level: medium
  - evidence:
    - command: `novaic-backend/scripts/run_idempotency_replay_ci.sh`
    - pass_summary: `PASS`
    - command: `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
    - pass_summary: `3 passed`
    - command: `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
    - pass_summary: `4 passed`
    - metrics_summary: `HIGH_LOAD_REPLAY_METRICS concurrency=80 throughput_ops_per_sec=1121.94 exactly_once_winner=0`
    - artifact_path: `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

- Task: Publish 3-step hot-key contention triage runbook section
  - owner: Agent Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - dependencies:
    - diagnostics policy defaults and diagnostics endpoint available
  - risk_level: low
  - evidence:
    - artifact_path: `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
    - summary: 新增 `3-Step Hot-Key Contention Triage`（识别热点键 -> 校验 owner/lease -> 执行恢复与审计记录）

## Exact Command Evidence
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
  - pass_summary: `PASS`
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - pass_summary: `3 passed`
- `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
  - pass_summary: `4 passed`
  - replay_summary: `HIGH_LOAD_REPLAY_METRICS concurrency=80 throughput_ops_per_sec=1121.94 exactly_once_winner=0`

## Artifact / Doc Paths
- `.github/workflows/ci.yml`
- `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
- `novaic-backend/scripts/check_idempotency_diagnostics_policy.py`
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `ops-rounds/round-009/10-dispatch/team-agent-runtime.md`
- `ops-rounds/round-009/20-reports/team-agent-runtime-report.md`

## Acceptance Mapping
- Mandatory Task-1 (main CI flow diagnostics gate): DONE
- Mandatory Task-2 (unit/integration replay + metrics): DONE
- Mandatory Task-3 (3-step triage section): DONE
- Acceptance Commands:
  - `novaic-backend/scripts/run_idempotency_replay_ci.sh`: PASS
  - `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`: PASS
  - `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`: PASS

## Risks / Blockers
- blocker: NONE
- risk: NONE

## Self Status
- status: DONE
