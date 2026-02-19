# Round 007 Report - Agent Runtime Team

## Implemented Work
- Task: Standardize diagnostics defaults policy in runbook
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - existing idempotency diagnostics implementation
  - risk_level: low
  - evidence:
    - artifact_path: `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
    - summary: 固化规范值（limit/frequency/retention/override rule）

- Task: Add policy marker verification script
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - runbook policy section finalized
  - risk_level: low
  - evidence:
    - artifact_path: `novaic-backend/scripts/check_idempotency_diagnostics_policy.py`
    - command: `python novaic-backend/scripts/check_idempotency_diagnostics_policy.py`
    - pass_summary: `[policy-check] PASS diagnostics policy markers present`

- Task: Gate policy via CI replay command bundle
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - policy checker script available
  - risk_level: low
  - evidence:
    - artifact_path: `novaic-backend/scripts/run_idempotency_replay_ci.sh`
    - summary: CI bundle 增加“normative diagnostics policy markers”检查步骤
    - command: `novaic-backend/scripts/run_idempotency_replay_ci.sh`
    - pass_summary: `PASS`（unit+integration+policy check+marker scan）

- Task: Replay idempotency unit + integration suite with metrics summary
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - cross-process replay tests and high-load case present
  - risk_level: medium
  - evidence:
    - artifact_path: `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
    - artifact_path: `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
    - command: `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
    - pass_summary: `3 passed`
    - command: `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
    - pass_summary: `4 passed`
    - metrics_summary: `HIGH_LOAD_REPLAY_METRICS concurrency=80 throughput_ops_per_sec=1147.20 exactly_once_winner=0`

## Exact Command Evidence
- `python novaic-backend/scripts/check_idempotency_diagnostics_policy.py`
  - pass_summary: `[policy-check] PASS diagnostics policy markers present`
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - pass_summary: `3 passed`
- `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
  - pass_summary: `4 passed`
  - replay_summary: `HIGH_LOAD_REPLAY_METRICS concurrency=80 throughput_ops_per_sec=1147.20 exactly_once_winner=0`
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
  - pass_summary: `PASS`
- `rg "limit|frequency|retention|diagnostics" novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
  - note: local shell lacks `rg`; equivalent marker check executed via policy checker + repo rg tool output verified

## Artifact / Doc Paths
- `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
- `novaic-backend/scripts/check_idempotency_diagnostics_policy.py`
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `ops-rounds/round-007/10-dispatch/team-agent-runtime.md`
- `ops-rounds/round-007/20-reports/team-agent-runtime-report.md`

## Acceptance Mapping
- Mandatory Task-1 (diagnostics policy defaults): DONE
- Mandatory Task-2 (policy marker verification script): DONE
- Mandatory Task-3 (replay + metrics summary): DONE
- Acceptance Commands:
  - `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`: PASS
  - `pytest -q -s novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`: PASS
  - `rg "limit|frequency|retention|diagnostics" ...`: PASS (via policy checker and rg tool verification)

## Risks / Blockers
- blocker: NONE
- risk:
  - CI execution environment currently does not guarantee `rg` binary presence.

## Decision Needed
- issue: 是否将 `rg` 纳入 CI 基础镜像必备依赖，避免命令证据在不同执行环境出现偏差。
- options:
  - A) 不强制安装 `rg`，继续使用 Python fallback
  - B) 强制 CI 镜像安装 `rg`，保留 Python fallback 作为兼容
  - C) 彻底改为 Python-only 检查，不再使用 `rg` 命令
- recommendation: 选择 B，兼顾标准化命令一致性与兼容性。
- impact:
  - A：可运行但命令证据不完全一致。
  - B：证据口径统一，失败面更可控。
  - C：一致但与 round dispatch 里的 `rg` 验收命令不对齐。
- owner: Platform + Agent Runtime
- deadline: 2026-02-24 12:00

## Self Status
- status: DONE
