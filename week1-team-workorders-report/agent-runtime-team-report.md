# Week 1 Work Report - Agent Runtime Team

## Team
Agent Runtime Team

## Date
2026-02-19

## Mission Alignment
本周围绕工单目标推进了 workers runtime 稳定性改造，重点落在三件事：
- 提升吞吐稳定性（失败场景避免重试风暴）
- 统一重试策略（可重试分类、最大尝试次数、退避）
- 补齐幂等防重（避免重复任务产生重复副作用）

## Completed Work

### 1) Unified Retry Policy (D3)
- 新增统一策略模块：`novaic-backend/task_queue/retry_policy.py`
- 抽象 `RetryPolicy` + `RetryDecision`，统一管理：
  - 可重试错误判定（基础设施错误 vs 业务错误）
  - 最大尝试次数判断（max attempts exhausted）
  - 指数退避计算（`backoff_base` 到 `backoff_max`）
- 配置来源统一接入 `ServiceConfig`（`DEFAULT_MAX_RETRIES`、`RETRY_BACKOFF_BASE`、`RETRY_BACKOFF_MAX`）

### 2) Task Worker Retry/Idempotency Hardening (D3 + D4)
- 改造 `novaic-backend/task_queue/workers/task_worker_sync.py`
  - 失败重试判定改为统一使用 `RetryPolicy.evaluate(...)`
  - 失败日志补充标准化 reason + attempt/max_attempts，便于排障
  - 引入 worker 进程内 idempotency 防重缓存（LRU 风格上限 5000）
  - 对重复 `idempotency_key` 的任务直接 `complete`，跳过 handler 副作用执行
- 目标：避免短时间重复投递/重复 claim 导致的重复 side effect

### 3) Saga Worker Retry Convergence (D3)
- 改造 `novaic-backend/task_queue/workers/saga_worker_sync.py`
  - 删除本地分散的 retryable 判定和固定重试常量
  - 统一接入 `RetryPolicy`
  - 可重试场景在 release 前执行 backoff，降低错误高峰时的重试抖动
  - 重试耗尽/不可重试场景统一 reason 打点

## Tests and Verification
- 新增测试：`novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - `BusinessError` 不重试
  - 指数退避 + 最大尝试数行为正确
  - TaskWorker 对重复 idempotency key 执行防重
- 本地执行结果：
  - `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py` -> 3 passed
  - `pytest -q novaic-backend/tests/unit/task_queue/test_explicit_split_clients.py` -> 7 passed
- 代码静态检查：修改文件无新增 lints

## Impact Assessment
- **稳定性**：统一重试决策后，worker 行为一致，降低策略漂移风险
- **吞吐**：失败流量在 backoff 下被平滑，减轻系统抖动与资源争抢
- **幂等性**：重复任务在 worker 内被快速短路，减少重复副作用概率

## Risks / Gaps
- 当前幂等防重为进程内缓存，跨进程/重启后仍依赖队列侧幂等键与业务端幂等保障
- 当前 backoff 主要在 worker 层实现，队列层尚未引入可观测的延迟重试时间窗字段

## Next Steps
- 推进队列层延迟重试机制（如 `next_retry_at`）并让 claim 显式感知
- 增加跨 worker/重启场景的幂等集成测试
- 输出 retry policy spec + runbook（对齐 API/Runtime/Tools 团队契约）
