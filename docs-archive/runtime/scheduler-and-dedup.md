# Scheduler / Queue：定时唤醒去重

> 当前生产职责路径：`novaic-agent-runtime/task_queue/workers/scheduler_worker.py`

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
- `SchedulerWorker` 为每条 `scheduled_wake` 构造稳定 `idempotency_key`
- 形式为：`scheduled-wake:{agent_id}:{subagent_id}:{wake_at}`
- `queue_service` 的 `SessionRepository.dispatch()` 先写 append-only
  session input event，再由 session FSM 决策 start / attach / buffer
- start/restart 不再同步创建 saga，而是提交 `create_wake_saga`
  session outbox effect，返回 `wake_start_queued` / `restart_pending`
- `session-outbox-worker` 负责 drain durable outbox，把 queued wake intent
  转成真实 wake saga
- 若会话已激活，可附加的 IM 输入走 `publish_attach_input` outbox；不可附加
  输入留在 append-only session inbox，等待 session finalize 后 restart

## 3. 按 `(agent, subagent)` 排队的单行道锁
对于同一 `(agent_id, subagent_id)`：
- `tq_session_state` 是唯一在线 session state authority
- `tq_session_events` 是 append-only input/event ledger
- `tq_session_outbox` 是 session side-effect ledger
- `session_ended()` 根据未消费 input projection 决定是否写入 restart outbox

因此，当前模型是：
- **Scheduler** 负责发现到期唤醒
- **Queue Session Coordinator** 负责去重、缓冲和串行化
- **Session Outbox Worker** 负责把 durable session effects 投递出去
- 运行时只保留这一条定时唤醒链路
