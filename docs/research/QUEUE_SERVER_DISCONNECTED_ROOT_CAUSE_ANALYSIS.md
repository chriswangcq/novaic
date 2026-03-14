# Server disconnected without sending a response - 根因全面排查报告

## 一、问题现象

- **错误**：`HTTP error: Server disconnected without sending a response`
- **发生位置**：saga.decision task 执行时
- **影响**：message_process saga 在 decide_action 步骤失败，导致 rt-8e0446acee22 创建后未触发 runtime_start，runtime 卡在 need_think
- **时间**：2026-03-04 07:58 UTC（15:58 北京时间）附近，4 个 message_process saga 连续失败

---

## 二、失败调用链（精确定位）

### 2.1 执行流程

```
Task Worker 主循环
  → _claim_task()                    [TaskQueueClient]  ✅
  → _should_release_saga_task()       [SagaClient.get]   可能失败①
  → _execute_task_with_heartbeat()
    → _execute_task()
      → acquire_idempotency_execution [TaskQueueClient]  ✅
      → _call_handler()
        → _call_saga_handler()
          → saga_client.get(saga_id)  [SagaClient]       ← 最可能失败②
          → _handle_saga_decision()   [纯内存]
      → complete_idempotency_execution
      → complete
```

### 2.2 失败点结论

- **最可能**：`_call_saga_handler` 第 368 行 `saga_client.get(saga_id)`
- **次可能**：`_should_release_saga_task` 第 162 行 `saga_client.get(saga_id)`（失败会被 catch，继续执行，但可能影响后续）
- **HTTP 调用**：`GET http://127.0.0.1:19997/api/queue/sagas/{saga_id}`

---

## 三、根因分析（多维度）

### 3.1 客户端：httpx 连接复用

| 项目 | 配置 |
|------|------|
| **SagaClient** | 持久化 `_session`，无 base_url，仅传 `timeout` |
| **internal_client** | `httpx.Client(timeout=..., trust_env=...)`，无 limits |
| **httpx 默认** | `keepalive_expiry=5s`, `max_keepalive_connections=20` |
| **Session 刷新** | 无；连接错误时不会重建 `_session` |
| **重试** | 使用同一 session，不会换连接 |

**结论**：客户端会复用连接；若服务端已关闭连接，复用时会触发 `RemoteProtocolError`。

### 3.2 服务端：Queue Service

| 项目 | 配置 |
|------|------|
| **uvicorn** | 仅 host/port/log_level，无 timeout/keepalive |
| **timeout_keep_alive** | 默认 5s |
| **orchestrator.get()** | `db.transaction(lock_type="saga")`，无 lock timeout |
| **FIFOLock** | 无 timeout 时 `event.wait()` 无限阻塞 |
| **SQLite** | `busy_timeout=10000`（10s）或 schema 中 5000（5s） |

**结论**：高并发时 DB 锁竞争会导致 handler 长时间阻塞，可能触发超时或连接关闭。

### 3.3 日志证据：锁竞争

```
2026-03-04 21:38:00 [WARNING] [FIFO Lock] Long wait: unknown waited 2.21s, queue_size=12
2026-03-04 21:38:00 [WARNING] [FIFO Lock] Long wait: unknown waited 2.21s, queue_size=11
... (最多 12 个请求排队)
```

- 单次等待约 2.2s
- 07:58 时 queue.db 约 8.7GB，scheduled_wake 并发高，锁竞争更严重
- 若排队更长或单次事务更慢，等待可接近或超过 SQLite busy_timeout，导致 handler 异常、连接关闭

### 3.4 异常类型与重试

| 异常 | 是否可重试 |
|------|------------|
| **httpx.RemoteProtocolError** | 非 NetworkError 子类，不在 RETRYABLE_EXCEPTIONS |
| **TaskQueueError** | 客户端包装后，原始类型丢失 |
| **RETRYABLE_KEYWORDS** | "connection" 等，对 "Server disconnected" 可能不匹配 |

**结论**：`RemoteProtocolError` 被包装为 `TaskQueueError` 后，可能未被识别为可重试，导致不重试或重试策略不符合预期。

---

## 四、根因归纳

| 根因 | 可能性 | 说明 |
|------|--------|------|
| **1. 连接复用** | 高 | httpx 复用连接，服务端已关闭时复用触发 RemoteProtocolError |
| **2. DB 锁竞争** | 高 | 07:58 高并发 + 8.7GB queue.db，FIFO 排队、SQLite 等待，handler 阻塞 |
| **3. 两者叠加** | 高 | 锁竞争导致 handler 慢/超时，服务端关闭连接；客户端复用坏连接，报错 |
| **4. 重试失效** | 中 | 异常被包装后可能不被识别为可重试 |

---

## 五、配置与代码引用

### 5.1 关键代码路径

| 文件 | 行号 | 说明 |
|------|------|------|
| `task_worker_sync.py` | 368 | `saga_client.get(saga_id)` 失败点 |
| `task_queue/client.py` | 316-319 | SagaClient `_get_session`，无 limits |
| `task_queue/client.py` | 364-366 | `httpx.HTTPError` → `TaskQueueError` 包装 |
| `queue_service/saga_repo.py` | 131-138 | `orchestrator.get()` 使用 saga 锁 |
| `shared_runtime_common/common/db/locks.py` | 98-115 | FIFOLock 无 timeout 时无限 wait |
| `shared_runtime_common/common/db/database.py` | 86 | SQLite `busy_timeout=10000` |
| `queue_service/main.py` | 167-174 | uvicorn 默认配置 |
| `shared_runtime_common/task_queue/exceptions.py` | 48-57 | RETRYABLE_EXCEPTIONS 不含 RemoteProtocolError |

### 5.2 配置值

```json
// config/services.json
"timeouts": {
  "http_timeout": 30.0,
  "task_timeout": 120,
  "db_transaction_timeout": 10.0
},
"worker": {
  "num_workers": 5,
  "heartbeat_interval": 10.0
}
```

---

## 六、建议（不改代码，仅排查）

1. **日志**：在 07:58 UTC 对应时段的 queue-service、task-worker 日志中搜索 error、lock、timeout、OperationalError
2. **复现**：在 queue.db 较大、scheduled_wake 集中时观察 saga.decision 失败率
3. **监控**：关注 `[FIFO Lock] Long wait` 的频率和 queue_size

---

## 七、总结

| 问题 | 结论 |
|------|------|
| **失败位置** | `saga_client.get(saga_id)`（`_call_saga_handler` 首行） |
| **直接原因** | HTTP 连接被关闭（服务端关闭或复用已关闭连接） |
| **根因 1** | 客户端连接复用，无 session 刷新，易复用到已关闭连接 |
| **根因 2** | 服务端 DB 锁竞争，handler 阻塞，可能超时或异常导致连接关闭 |
| **为何连续** | 07:58 高并发 + 8.7GB queue.db，多 worker 同时受影响 |
| **为何非全局故障** | 仅部分请求失败，claim/route 等成功，属偶发连接/锁问题 |
