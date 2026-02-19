# Round 002 Report - Agent Runtime Team

## Mission Alignment
- 目标对齐 `team-agent-runtime.md`：推进重试与幂等从本地 workaround 走向可观测、可复现、跨进程可靠机制。
- 本次更新优先交付统一重试策略基线与幂等防重第一阶段，作为跨进程方案落地前置。

## Completed Work
- Task: Unified retry policy module
  - owner: Agent Runtime Team
  - due: 2026-02-26
  - status: DONE
  - dependencies: `common.config` retry 配置项可用
  - risk_level: medium
  - details: 新增统一策略 `RetryPolicy`/`RetryDecision`，统一异常分类、attempt 上限判断和指数退避计算。
  - evidence:
    - code: `novaic-backend/task_queue/retry_policy.py`
    - tests: `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- Task: Worker retry behavior convergence (Task + Saga)
  - owner: Agent Runtime Team
  - due: 2026-02-26
  - status: DONE
  - dependencies: `task_queue` workers 可正常导入统一策略模块
  - risk_level: medium
  - details: `task_worker_sync.py` 与 `saga_worker_sync.py` 均已接入统一重试策略，日志输出标准化 reason/attempt 信息。
  - evidence:
    - code: `novaic-backend/task_queue/workers/task_worker_sync.py`
    - code: `novaic-backend/task_queue/workers/saga_worker_sync.py`
    - tests: `pytest -q novaic-backend/tests/unit/task_queue/test_explicit_split_clients.py`
- Task: Idempotency guard phase-1 (in-process dedupe)
  - owner: Agent Runtime Team
  - due: 2026-02-26
  - status: DONE_WITH_GAPS
  - dependencies: queue 侧 idempotency_key 已存在并稳定
  - risk_level: high
  - details: 增加 worker 进程内 idempotency 缓存短路，降低重复执行副作用概率；跨进程/重启仍需补齐。
  - evidence:
    - code: `novaic-backend/task_queue/workers/task_worker_sync.py`
    - tests: `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- Task: Round report initialization under file-driven mechanism
  - owner: Agent Runtime Team
  - due: 2026-02-19
  - status: DONE
  - dependencies: round-002 文件结构可用
  - risk_level: low
  - details: 按 round-002 机制落地团队报告并附证据。
  - evidence:
    - doc: `ops-rounds/round-002/20-reports/team-agent-runtime-report.md`
- Task: Retry/idempotency runbook draft
  - owner: Agent Runtime Team
  - due: 2026-02-26
  - status: DONE_WITH_GAPS
  - dependencies: 当前实现代码可引用
  - risk_level: medium
  - details: 发布 runbook 草稿，覆盖策略、验证命令、运维检查项；待补跨进程方案落地后更新为最终版。
  - evidence:
    - doc: `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
- Task: Queue-level retry scheduling visibility (`next_retry_at`)
  - owner: Agent Runtime Team
  - due: 2026-02-26
  - status: DONE
  - dependencies: queue schema migration + worker fail API 参数兼容
  - risk_level: medium
  - details: 在任务表新增 `next_retry_at` 并接入 claim/fail/recover 流程；worker 失败上报携带 `retry_delay_seconds`，实现可观测、可控的重试调度窗口。
  - evidence:
    - code: `novaic-backend/queue_service/db/schema.py`
    - code: `novaic-backend/queue_service/queue_db.py`
    - code: `novaic-backend/queue_service/routes.py`
    - code: `novaic-backend/task_queue/client.py`
    - code: `novaic-backend/task_queue/workers/task_worker_sync.py`
    - tests: `pytest -q novaic-backend/tests/unit/task_queue/test_queue.py novaic-backend/tests/unit/task_queue/test_routes.py novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`

## Evidence
- tests:
  - `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py` (3 passed)
  - `pytest -q novaic-backend/tests/unit/task_queue/test_explicit_split_clients.py` (7 passed)
  - `pytest -q novaic-backend/tests/unit/task_queue/test_queue.py novaic-backend/tests/unit/task_queue/test_routes.py novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py` (26 passed)
- artifacts:
  - `novaic-backend/task_queue/retry_policy.py`
  - `novaic-backend/task_queue/workers/task_worker_sync.py`
  - `novaic-backend/task_queue/workers/saga_worker_sync.py`
  - `novaic-backend/queue_service/db/schema.py`
  - `novaic-backend/queue_service/queue_db.py`
  - `novaic-backend/queue_service/routes.py`
  - `novaic-backend/task_queue/client.py`
  - `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- docs:
  - `novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md`
  - `week1-team-workorders-report/agent-runtime-team-report.md`
  - `ops-rounds/round-002/20-reports/team-agent-runtime-report.md`

## Acceptance Criteria Mapping
- Duplicate side effects are prevented across process boundaries:
  - current: PARTIAL（仅进程内防重）
  - gap: 缺少跨进程/重启后持久化幂等屏障
- Retry behavior is observable and deterministic:
  - current: DONE（队列层 `next_retry_at` + worker 显式 retry_delay 已落地）
  - gap: 需补端到端运维观测看板与压测数据
- Cross-process idempotency tests pass:
  - current: NOT_DONE
  - gap: 尚未提交跨进程/重启场景集成测试

## Risks / Gaps
- Gate D 风险：dispatch 要求的“跨进程或持久化幂等策略”尚未闭环，当前仅 in-process 防重。
- 跨进程与重启场景测试缺失，无法证明副作用在多 worker 实例下被严格抑制。
- 进程内防重与 `next_retry_at` 已落地，但“持久化幂等屏障”仍未完成，Gate D 仍有风险。

## Next Steps
- 新增跨进程/重启重复任务测试并给出可复现命令。
- 发布 retry/idempotency runbook，明确与 API/Runtime/Tools 的契约边界与调用要求。
- 实现持久化幂等屏障（DB-level ledger/CAS）并完成跨进程验证。

## Self Status
- owner: Agent Runtime Team
- due: 2026-02-26
- status: IN_PROGRESS
