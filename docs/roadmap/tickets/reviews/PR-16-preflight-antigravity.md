# PR-16 Preflight 分析：Dispatch Subscriber 全量实现

本预案主要针对 PR-16 的核心消费逻辑展开架构与实现细节的深度决策分析，尤其聚焦跨进程边界、并发原语、容错重试以及灰度可观测性。

## 1. 读路径拓扑：坚守跨进程 HTTP 边界 (方案 A)

**结论**：坚守服务隔离原则，采用 **方案 A（新增 Entangled HTTP 端点）**，Business 侧的 Subscriber 通过注入的 `outbox_client` (即 `internal_async_client`) 调用 Entangled。

在 `Entangled/packages/server-python/entangled/app/outbox.py` 新增 3 个受 `Depends(verify_service_or_user)` 保护的路由，并配以明确的 Pydantic 模型。Server 纯做数据层写操作，permanent 判定交由 client 进行。

```python
from pydantic import BaseModel
from typing import Optional

class ClaimRequest(BaseModel):
    worker_id: str
    batch_size: int = 50
    claim_ttl_ms: int = 30_000
    max_attempts: int = 5

class ClaimedRow(BaseModel):
    id: int
    message_id: str
    agent_id: str
    trigger_type: str
    payload_json: str  # 保持原 TEXT 不 loads，client 自己 parse
    attempts: int
    created_at: int

class ClaimResponse(BaseModel):
    rows: list[ClaimedRow]
    count: int

class MarkDeliveredRequest(BaseModel):
    ids: list[int]

class MarkFailedRequest(BaseModel):
    id: int
    kind: str                      # "queue_5xx"|"network"|"no_owner"|"queue_400"|"bad_argument"
    error: str                     # 人读的 detail
    permanent: bool                # client 算好传给 server
    retry_delay_ms: Optional[int]  # permanent=True 时为 None

class MarkAckResponse(BaseModel):
    updated: int
```

## 2. Claim 原子性与 DLQ 死信语义 (方案 P1)

**机制保障**：
采用 **方案 P1**。Entangled 端的 `/v1/outbox/claim` 将原子抢占 `attempts < max_attempts` 的行，避免 permanent error 被无限循环捞起导致死循环（DLQ 语义防漏）：

```sql
UPDATE message_outbox
   SET locked_by = :worker_id, locked_until = :now + :claim_ttl_ms
 WHERE id IN (
     SELECT id FROM message_outbox
      WHERE delivered_at IS NULL
        AND (locked_until IS NULL OR locked_until <= :now)
        AND attempts < :max_attempts
      ORDER BY id LIMIT :batch_size
 )
 RETURNING id, message_id, agent_id, trigger_type, payload_json, attempts, created_at;
```
这样一来，如果某消息达到了 `max_attempts`（无论是通过正常退避累加还是因 permanent error 被直接置顶），它将永远从 claim query 中过滤，停留在 `delivered_at = NULL` 供后续 PR-26 (orphan metric) 抓取。

## 3. Subscriber 依赖注入与挂载

PR-16 采用 **方案 C.1 构造器注入**，将 HTTP Client 注入给 Subscriber。

```python
# business/subscribers/dispatch_subscriber.py
def __init__(
    self,
    assembler: DispatchAssembler,
    outbox_client: httpx.AsyncClient,
    *,
    poll_interval: float = 0.5,
    batch_size: int = 50,
    max_attempts: int = 5,
    claim_ttl_ms: int = 30_000,
    worker_id: Optional[str] = None,
):
    ...
```

**Lifespan 挂载**：
```python
# main_business.py
if SUBSCRIBER_ENABLED:
    from business.wake.assembler_factory import get_assembler
    from business.subscribers.dispatch_subscriber import DispatchSubscriber
    from common.client import internal_async_client
    
    outbox_client = internal_async_client(
        service_name="business-subscriber", 
        base_url=ServiceConfig.ENTANGLED_URL
    )
    sub = DispatchSubscriber(
        assembler=get_assembler(),
        outbox_client=outbox_client
    )
```

## 4. `assemble_and_dispatch` 的错误分类处理

在 `_deliver_one` 中捕获异常分类：
1. **Transient (瞬态失败)**：`kind` 取决于网络报错等。`permanent=False`，进行指数退避（延迟计算由 Business Client 计算）。
2. **Permanent (毒丸/永久性失败)**：`DispatchError.kind in ("no_owner", "queue_400", "bad_argument")`。传递 `permanent=True`。
3. **边界情况 (Payload 解析错误)**：`json.loads(row["payload_json"])` 抛出 `JSONDecodeError` 时，同样视为 **Permanent** (`kind="bad_argument"`)，调用 `mark_failed` 一次性作废，避免重试。

## 5. 空转性能与 Graceful Shutdown

- **静默巡航**：`_tick()` == 0 时，绝对不打印 INFO 日志（仅记录 DEBUG 或保持静默），无需设计自适应 poll_interval，0.5s 固定轮询对 SQLite 无压力。
- **Graceful Shutdown (语义 G.2)**：完成**当前** `_deliver_one` 后即检查 `self._stop.is_set()`，若置起则放弃已获取但尚未处理的 batch 剩余行，迅速退出。被遗弃的行在 TTL 到期后会被下个 Worker 安全接管。

## 6. Canary 灰度观测 (利用 Queue 已有回包)

不改动 Queue 侧代码。直接利用 PR-10 引入的 `DispatchResult.raw["action"]` 字段来量化 Subscriber 的灰度接管率：
```python
result = await self.assembler.dispatch(req)
action = result.raw.get("action", "unknown")  # e.g., "deduped" 或 "created"
logger.info(
    "event=subscriber_delivered id=%s trigger=%s action=%s",
    row.id, row.trigger_type, action
)
```

## 7. 可观测性策略 (Metrics Defer)
除了上述详尽的结构化日志（如 `subscriber_tick claimed=N...`）之外，Ticket 所涉及的 5 个 Prometheus Metric 全部 **Defer 到 PR-32**。PR-32 工单已追加相关监控要求。

## 8. 崩溃恢复测试设计 (Crash Recovery Test)
为了避免耗时过长的等待，集成测试将引入一个参数化的骨架，调小 `claim_ttl_ms` 加速测试：
```python
async def test_expired_lock_reclaimed(outbox_client_mock):
    # Worker A 极短的租约
    sub_a = DispatchSubscriber(..., claim_ttl_ms=100)
    rows_a = await sub_a._claim_batch()
    # A crash，租约过期
    await asyncio.sleep(0.15)
    # Worker B 接管
    sub_b = DispatchSubscriber(..., claim_ttl_ms=100)
    rows_b = await sub_b._claim_batch()
    assert rows_b[0].id == rows_a[0].id
    assert rows_b[0].locked_by != rows_a[0].locked_by
```

---

预案分析通过，将严格按 5-6 阶段拆分 Commit 推进 T1 实施。
