# Scheduler / Queue：定时唤醒去重

> 当前生产职责路径：`novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`

## 1. 现状

过去系统里曾有多个轮询者会调用 `BusinessClient.get_due_for_wake()`，然后进入 Queue Service 的 Session Coordinator：

```python
SagaClient.dispatch(..., trigger_type="scheduled_wake")
```

这会导致在误配置或双进程共存时，对同一个 `(agent_id, subagent_id, wake_at)` 重复创建唤醒 Saga。

## 2. 唤醒风暴 (Awakening Storm)
**痛点**：如果多个轮询者同时扫到同一条到期 `wake_at`，就会齐刷刷向队列投递 `scheduled_wake`，导致重复创建 Saga 或无意义的 buffered 请求。

**防重机制 (Dedup Filter)**：
Runtime 现在把去重压力明确落在 Queue Service：
- `SchedulerWorkerSync` 为每条 `scheduled_wake` 构造稳定 `idempotency_key`
- 形式为：`scheduled-wake:{agent_id}:{subagent_id}:{wake_at}`
- `queue_service` 的 `SessionRepository.dispatch()` 会优先按此 key 查重；若已存在 Saga，则返回 `{"action": "deduped"}` 并复用已有会话
- 若会话已激活，则仍走现有 `buffered` 语义，只保留最新一条 pending trigger

## 3. 按 `(agent, subagent)` 排队的单行道锁
对于同一 `(agent_id, subagent_id)`：
- `tq_active_sessions` 保证同一时刻只有一个活跃 session
- `tq_pending_triggers` 只保留该 session_key 的最新一条待处理 trigger
- `session_ended()` 会在旧 session 结束后再接力下一条 pending trigger

因此，当前模型是：
- **Scheduler** 负责发现到期唤醒
- **Queue Session Coordinator** 负责去重、缓冲和串行化
- 运行时只保留这一条定时唤醒链路
