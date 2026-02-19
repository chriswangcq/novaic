# Round 004 Report - Agent Runtime Team

## Completed Work
- Task: Re-run cross-process idempotency integration tests
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - `/internal/tq` idempotency API routes available in test fixture
  - risk_level: low
  - evidence:
    - command: `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
    - result_summary: `3 passed`
    - artifact_path: `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`

- Task: Higher-concurrency duplicate-task stress variant
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - persistent idempotency ledger (`tq_idempotency_ledger`) already landed
  - risk_level: medium
  - evidence:
    - implementation_path: `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
    - command: `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
    - result_summary: 新增 12 并发 acquire 竞争场景，验证 exactly-one acquire + others in_progress + completed short-circuit

- Task: Runbook update for ledger contention troubleshooting
  - owner: Agent Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - dependencies:
    - runbook final doc exists from round-003
  - risk_level: low
  - evidence:
    - doc_path: `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
    - update_summary: 新增 `Ledger Contention Troubleshooting` 段落（症状、检查项、恢复选项、预防建议）

## Command Evidence
- `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
  - pass_summary: `3 passed`
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - pass_summary: `3 passed`

## Artifacts / Docs
- `novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
- `ops-rounds/round-004/10-dispatch/team-agent-runtime.md`
- `ops-rounds/round-004/20-reports/team-agent-runtime-report.md`

## Acceptance Mapping
- Mandatory Task-1 (re-run integration): DONE
- Mandatory Task-2 (higher-concurrency stress variant): DONE
- Mandatory Task-3 (runbook troubleshooting update): DONE
- Acceptance Commands:
  - `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`: PASS
  - `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`: PASS

## Risks / Blockers
- blocker: NONE
- risk: ledger contention currently可通过租约与重试机制平滑，但缺少专门可视化面板用于线上快速定位热点键。

## Decision Needed
- issue: 是否在下一轮引入幂等账本 contention 可视化与告警（按 idempotency_key 聚合）。
- options:
  - A) 维持现状，仅靠日志与手工 SQL 排障
  - B) 增加只读诊断 API + 基础阈值告警
  - C) 直接接入完整 dashboard（指标、Top keys、趋势）
- recommendation: 选择 B，改动成本低、收益高，可快速降低线上排障耗时。
- impact: 若不做，遇到高并发热点键时定位速度受限；做 B 可将排障从人工扫描日志降为结构化查询/告警。

## Self Status
- status: DONE
