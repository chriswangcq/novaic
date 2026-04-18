# PR-16 Preflight 分析：Dispatch Subscriber 全量实现

本预案主要针对 PR-16 的核心消费逻辑展开架构与实现细节的深度决策分析，尤其聚焦跨进程边界、并发原语、容错重试以及灰度可观测性。

## 1. 读路径拓扑：坚守跨进程 HTTP 边界 (方案 A)

**结论**：坚守服务隔离原则，采用 **方案 A（新增 Entangled HTTP 端点）**，Business 侧的 Subscriber 通过 `httpx.AsyncClient`（即 `internal_async_client`）调用 Entangled。

**决策依据与取舍**：
- **方案 A (HTTP)**：
  - *优点*：完全遵循现有的微服务网络边界，Business 不碰 Entangled 数据库，无资源泄露风险，职责清晰。
  - *缺点*：需要新增 3 个端点，且 claim 和 mark 动作产生网络开销。
- **方案 B (搬入 Entangled)**：
  - *缺点*：虽然零 HTTP 开销，但这会导致 Entangled 进程必须引入 `novaic-business` 的核心依赖（如 `DispatchAssembler`、业务规则、队列调用等），这是极为严重的**反向依赖污染**。Entangled 的定位是纯粹的 Entity Store，不应含有业务调度代码。

**PR-16 具体行动**：
在 `Entangled/packages/server-python/entangled/app/crud.py` (或专门的 `outbox.py` router) 新增：
1. `POST /v1/outbox/claim` (入参: `worker_id`, `batch_size`, `claim_ttl_ms`) -> 返回 list of rows。
2. `POST /v1/outbox/mark_delivered` (入参: `ids`)
3. `POST /v1/outbox/mark_failed` (入参: `id`, `error`, `retry_delay_ms`, `attempts_increment`)

## 2. Claim 原子性与 Batch Fencing

**机制保障**：
- SQLite 3.35+ 完全支持 `UPDATE ... RETURNING`。
- Entangled 端的 `POST /v1/outbox/claim` 将在一个单独的 DB 事务中执行完整的原子抢占：
  ```sql
  UPDATE message_outbox
     SET locked_by = :worker_id, locked_until = :now + :ttl
   WHERE id IN (
       SELECT id FROM message_outbox
        WHERE delivered_at IS NULL
          AND (locked_until IS NULL OR locked_until <= :now)
        ORDER BY id LIMIT :batch_size
   )
   RETURNING *;
  ```
- 返回的 JSON 列表即构成了绝对排他的 fencing token。只要 worker 在 `ttl` 内完成消费并调用 `mark_delivered`，就不会被别人窃取。

## 3. 失败重试、死信与 Backoff

**策略设计**：
- **指数退避**：对于瞬态失败（Transient），计算 `next_retry = now + (2^attempts * 1000) ms`，调用 `mark_failed` 将其写回 `locked_until`。这会将该消息暂时踢出轮询队列，实现自动退避。
- **永久失败 (Poison Message / 死信)**：
  - 如果 `attempts >= MAX_ATTEMPTS`（如 5 次）。
  - 处理方式：调用 `mark_failed` 时，除了更新 `last_error`，直接将 `locked_until` 设为一个**超长时间戳**（如 `INT_MAX`）或者直接在数据库打上特殊标记。
  - 不建议设为 `delivered_at = <now>`，因为这在语义上是“假成功”；保留 `delivered_at = NULL` 配合高 `attempts` 完美对接 PR-26 的 orphan metrics 告警。

## 4. `assemble_and_dispatch` 的错误分类处理

**毒丸拦截**：
在 `_deliver_one` 中捕获 `DispatchError` / `httpx.HTTPError` 时，必须进行分类：
- **Permanent (永久性失败)**：
  - 例如 `no_owner` (找不到绑定的 Agent)，或 `queue_400` (如 payload 格式致命错误、未定义路由)。
  - **行为**：无需浪费重试次数，直接判定为 Poison Message（`attempts` 记为 MAX_ATTEMPTS 或特殊死信状态）。
- **Transient (瞬态失败)**：
  - 例如 Queue Service 503、502 网络抖动、504 超时。
  - **行为**：进入指数退避（attempts + 1）。

## 5. 空转的 CPU 与日志成本防御

**静默巡航 (Silent Idle)**：
- 默认轮询间隔 `0.5s` 一天将产生 17 万次循环。
- `_tick()` 必须具备严格的 DEBUG gating：
  ```python
  if n == 0:
      # 不记录任何 INFO 日志，甚至避免高频 DEBUG 刷屏
      pass
  else:
      logger.info(f"Processed {n} outbox messages")
  ```
- 网络开销防御：若出队持续为 0，Entangled `/v1/outbox/claim` 同样只返回空数组 `[]`，不写底层 DB（避免 WAL 暴涨），且可通过配置将没数据时的 `poll_interval` 动态退避到 2-3 秒，有数据时恢复 0.5s。

## 6. Canary 灰度双发的可观测性 (PR-17 切流前奏)

在 PR-15/16/17 双发共存期间，如何量化证明“Subscriber 完全可以替代 Inline”是切流（PR-17）的信心基石。
- **双发态势**：Inline trigger 和 Subscriber 同发 `idempotency_key="msg:{id}"`。
- **量化策略**：
  1. **Subscriber 发送端打标**：Subscriber 发起请求时，在 metrics 中带有 `source=outbox_subscriber` 标签。
  2. **Queue 侧去重统计**：Queue Service 的 `/dispatch` 端点 (在 `novaic-agent-runtime/task_queue/client.py` 或服务端) 需要能够区分 201 Created 和 200 OK (Deduped)。这可以通过在 Queue 侧暴露一个简易的监控或日志打印 `dedup_hit` 来实现。
  3. **评估**：当 Subscriber 的落后时间（`outbox_lag`）稳定，且 Queue 的处理未出现异常尖峰，说明 Subscriber 的消费已经稳稳兜住了底，即可安全执行 PR-17 的删代码切流。

---

等待确认上述拓扑决策与容错机制后，即可开启 T1 实施阶段。
