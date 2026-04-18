# PR-16 Preflight Review — Dispatch Subscriber 全量实现

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准**。补完 §A/§B/§C（blocker）+ §D/§E/§F/§G/§H（细节）后直接 T1 |
| 亮点 | §1 方案 A 选对了（守住跨进程 HTTP 边界）；§4 错误分类跟 ticket 对齐；scope 比 PR-15 preflight 克制了 |

---

## §A（BLOCKER）DLQ 语义——ticket 里就有 bug，你 preflight 指对了方向但没写死

### 问题

ticket 实施代码第 93-97 行对 permanent 失败写的是：
```python
SET attempts = ?, last_error = ?, locked_by = NULL, locked_until = NULL
```

**`locked_until = NULL` + `delivered_at = NULL` 意味着下次 tick 的 claim query**：
```sql
WHERE delivered_at IS NULL AND (locked_until IS NULL OR locked_until <= now)
```
**会把这行再捞起来！** 然后再派发 → 再失败（同样的 `no_owner`）→ 再写回 → **死循环 + CPU 空转 + 日志刷屏**。

你 preflight §3 察觉了要"长久游离"，提出两个方案但没定死：

> 直接将 `locked_until` 设为一个**超长时间戳**（如 `INT_MAX`）或者直接在数据库打上特殊标记

"或者直接在数据库打上特殊标记"是 handwave，不 specific 就是没决策。

### 要求

**二选一写死**，preflight §3 给出具体 SQL：

**方案 P1（推荐）**：claim query 加 `AND attempts < MAX_ATTEMPTS`：
```sql
UPDATE message_outbox
   SET locked_by = :worker_id, locked_until = :now + :ttl
 WHERE id IN (
     SELECT id FROM message_outbox
      WHERE delivered_at IS NULL
        AND (locked_until IS NULL OR locked_until <= :now)
        AND attempts < :max_attempts      -- ← 新增
      ORDER BY id LIMIT :batch_size
 )
 RETURNING ...;
```
mark_failed 对 permanent 直接 `attempts = MAX_ATTEMPTS`（或更高），该行从 claim 过滤条件里消失。`locked_until = NULL` 保留 ticket 原样。

**方案 P2**：`locked_until = 9999999999999`（远未来时间戳）+ 不改 claim query。更简单但有"永久锁"的语义不洁。

**优先选 P1**，理由：`attempts` 本来就是计数器，读 `attempts >= MAX_ATTEMPTS` 语义明确，PR-26 orphan emitter 也能直接 `WHERE delivered_at IS NULL AND attempts >= MAX_ATTEMPTS`。INT_MAX 是 hack，会让人以后看代码困惑"为什么这行永远锁着"。

**决议写进 preflight §3**，同时 **在 ticket 的实施代码块底下贴一条"PR-16 preflight 勘误"**（或者你 T1 执行时直接按修正版写，不照搬 ticket 原样）。

## §B（BLOCKER）3 个 Entangled 端点的 wire format 完全没定义

### 现状

你 §1 列了 3 个端点名字：
- `POST /v1/outbox/claim(worker_id, batch_size, claim_ttl_ms)` → list
- `POST /v1/outbox/mark_delivered(ids)`
- `POST /v1/outbox/mark_failed(id, error, retry_delay_ms, attempts_increment)`

但：
- **没给 Pydantic 模型**（请求/响应体都要明确字段类型）
- **认证方式没说**（按 PR-05/PR-06，`internal_async_client` 会带 `X-Internal-Key` + `X-Internal-Service`；Entangled 这边用 `verify_service_or_user` 依赖？需确认）
- **`retry_delay_ms` 由 client 还是 server 计算**——你的 API 签名把它列成入参意味着 client 算，但指数退避逻辑放在 client 还是 server？
- **错误响应**：400/404/500 分别什么时候返回
- **`mark_failed` 的 `attempts_increment` 为何需要参数化**——永远是 +1 吧？参数化反而打开歧义面

### 要求

preflight §1 补一张表或三段 Pydantic 定义：

```python
# Entangled 侧（新建 entangled/app/outbox.py router）

class ClaimRequest(BaseModel):
    worker_id: str
    batch_size: int = 50
    claim_ttl_ms: int = 30_000
    max_attempts: int = 5          # ← 跟 §A 方案 P1 对应

class ClaimedRow(BaseModel):
    id: int
    message_id: str
    agent_id: str
    trigger_type: str
    payload_json: str              # 保持原 TEXT 不 loads，client 自己 parse
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
    permanent: bool                # ← client 算好传给 server，server 只负责写
    retry_delay_ms: int | None     # permanent=true 时为 None

class MarkAckResponse(BaseModel):
    updated: int
```

**server 就负责写 DB，不做业务判断**。client（subscriber）根据 `DispatchError.kind` 做分类，把 permanent/retry_delay 算好一起传。这样 server 纯数据层，未来如果死信策略改变，只动 Business 一侧。

**认证**：三个端点都加 `Depends(verify_service_or_user)`（跟 `/v1/schema/register` 同模式，PR-05 和 PR-06 的 `internal_async_client` 已经自动注入 header）。

## §C（BLOCKER）Subscriber 依赖注入：PR-15 只给了 `assembler`，PR-16 要新增一个 outbox client

PR-15 骨架的 `__init__`：
```python
def __init__(self, assembler: DispatchAssembler, *, poll_interval, batch_size, worker_id):
```

PR-16 选了方案 A（HTTP），subscriber 要调 Entangled 的 3 个新端点。所以需要注入**第二个 http client**。两种做法：

**C.1 构造器注入**（推荐）：
```python
def __init__(
    self,
    assembler: DispatchAssembler,
    outbox_client: httpx.AsyncClient,      # ← new
    *,
    poll_interval: float = 0.5,
    batch_size: int = 50,
    max_attempts: int = 5,
    claim_ttl_ms: int = 30_000,
    worker_id: Optional[str] = None,
):
```
lifespan 里构造：
```python
sub = DispatchSubscriber(
    assembler=get_assembler(),
    outbox_client=internal_async_client(service_name="business-subscriber", base_url=ServiceConfig.ENTANGLED_URL),
)
```
testable（test 里直接塞 `httpx.MockTransport`，跟 PR-10 Assembler 集成测那套路一致）。

**C.2 内部 lazy 创建**：
```python
def __init__(...):
    self._outbox_client = None

def _get_outbox_client(self):
    if self._outbox_client is None:
        self._outbox_client = internal_async_client(service_name="...", base_url=os.getenv("ENTANGLED_URL"))
    return self._outbox_client
```
测试要 monkey-patch factory，比 C.1 难。

**选 C.1**，跟 PR-10 `DispatchAssembler(resolver, ...)` 和 PR-13 `get_assembler()` 的依赖注入风格统一。

preflight 补一个明确的 `__init__` 签名定稿，以及 lifespan 里 wiring 的片段。

---

## 细节 §D — Metrics 策略要显式决定（ticket 列了 6 条）

ticket §可观测性 Checklist 列了：
- `subscriber_delivered_total{trigger}` counter
- `subscriber_failed_total{kind}` counter
- `subscriber_retry_total{kind}` counter
- `outbox_lag_seconds` gauge
- `outbox_claim_batch_size` histogram
- 结构化 log `subscriber_tick claimed=N delivered=M failed=K`

你 preflight 没说怎么办。按 PR-14/PR-10 的一贯策略：

**推荐方案**：log 全实现（结构化 `event=... trigger=... kind=...`），5 个 metric 全部 defer 到 `PR-32-metrics-prometheus-integration.md` backlog，在 PR-32 ticket 里追加 5 条 bullet。

preflight 新增一节"§可观测性策略"写明这点。

## 细节 §E — §5 自适应 poll_interval 是过度设计，砍掉

你 §5 最后一段：
> 可通过配置将没数据时的 `poll_interval` 动态退避到 2-3 秒，有数据时恢复 0.5s

**不要做**。理由：
- 增加状态机复杂度（idle 计数器、恢复条件、边界情况）
- 0.5s 固定轮询对 SQLite 是零压力（Entangled 的 claim query 空结果 <1ms）
- v1 怀疑的性能问题不存在；真发生了再优化

preflight §5 保留"静默巡航"结论（`_tick()` 返回 0 时不打 INFO 日志，打 DEBUG 或直接不打），**删掉自适应 interval 那一段**。这是 PR-15 scope 漂移的残余，第二次犯要警觉。

## 细节 §F — Canary 观测用 Queue 已有的 `action=deduped` 回包

你 §6 说"Queue Service 需要能够区分 201 Created 和 200 OK (Deduped)"——担心要改 Queue 侧。**其实不用**。

Queue 已经返回了：
```bash
$ rg 'action.*deduped' novaic-agent-runtime/queue_service/session_repo.py
132:    "[SessionCoordinator] dispatch deduped: %s saga=%s key=%s",
138:    "action": "deduped",
196:    "action": "deduped",
```

Queue `/api/queue/dispatch` 响应体里已有 `action` 字段，可能值 `"deduped"`（命中 idempotency ledger）或其他（新起 session）。`DispatchResult.raw` 就是这个响应体（PR-10 定义）。

所以 subscriber 成功路径直接：
```python
result = await self.assembler.dispatch(req)
action = result.raw.get("action", "unknown")
logger.info("event=subscriber_delivered id=%s trigger=%s action=%s",
            row["id"], row["trigger_type"], action)
```
action=`deduped` → inline 先发过了；`created` / 其他 → subscriber 是首发。grep 日志就能算双发命中率。

preflight §6 改写成："读 `DispatchResult.raw["action"]`（PR-10/PR-13 已引入），不需要改 Queue 侧"，省一个 scope expansion 风险。

## 细节 §G — Graceful shutdown 要定义清楚

ticket 实装 Checklist："Graceful shutdown：signal 到来时当前 tick 结束才退"。**"当前 tick 结束"具体到什么粒度？**

- G.1 **完成整个 claim batch**（最多 `batch_size` 条，最坏情况 batch_size × per-request latency ≈ 25s+）→ 退出慢
- G.2 **完成当前 `_deliver_one`**，剩余已 claim 但未处理的行放弃 → TTL 过期后下个 worker 接管 → 退出快（最多 1 条 latency ≈ 0.5s）

**选 G.2**（bounded shutdown time）。实现大意：

```python
async def run(self):
    while not self._stop.is_set():
        claimed = await self._claim_batch()
        for row in claimed:
            if self._stop.is_set():
                break        # 放弃剩余行，TTL 过期后自动回收
            await self._deliver_one(row)
        if not claimed:
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.poll_interval)
            except asyncio.TimeoutError:
                pass
```

preflight §执行计划补一节"§Graceful Shutdown"说明这个语义。

## 细节 §H — Crash recovery 测试设计

ticket 测试 #5：`subscriber crash 模拟（不 free lock）→ 30s 后另一实例接管`。30s 对单测太长。

**推荐测试设计**：

```python
async def test_expired_lock_reclaimed(outbox_client_mock):
    # Worker A claims with very short TTL
    sub_a = DispatchSubscriber(..., claim_ttl_ms=100)
    rows_a = await sub_a._claim_batch()
    assert len(rows_a) == 1
    # A "crashes" without calling mark_* 
    # Simulate by waiting past TTL
    await asyncio.sleep(0.15)
    
    # Worker B starts, claims — should pick up the same row
    sub_b = DispatchSubscriber(..., claim_ttl_ms=100)
    rows_b = await sub_b._claim_batch()
    assert len(rows_b) == 1
    assert rows_b[0]["id"] == rows_a[0]["id"]  # same row
    assert rows_b[0]["locked_by"] != rows_a[0]["locked_by"]  # different worker
```

关键：通过 `claim_ttl_ms` 参数化（而不是代码里 hardcode 30_000），测试就能把 TTL 调小到 100ms，快速验证。preflight §测试计划补这个具体骨架。

## 细节 §I — 边界：`payload_json` 损坏怎么处理

防御：`json.loads(row["payload_json"])` 可能抛 `JSONDecodeError`。应该怎么办？

**推荐**：视为 permanent 失败（`kind="bad_argument"`），一次性废掉该行（`attempts = MAX_ATTEMPTS`），记 `last_error`：
```python
try:
    payload = json.loads(row["payload_json"])
except json.JSONDecodeError as e:
    await self._mark_failed(row["id"], kind="bad_argument",
                            error=f"malformed payload_json: {e}",
                            permanent=True, retry_delay_ms=None)
    return
```

preflight §4 列一个"§4.3 边界：payload_json 损坏 → permanent fail"。

---

## 返工 Checklist

- [ ] §A 决定 DLQ 语义，推荐方案 P1（claim query 加 `attempts < MAX_ATTEMPTS`），写进 preflight §3 + 给出具体 SQL
- [ ] §B 定义 3 个端点的 Pydantic 请求/响应模型；server 纯 DB 操作，permanent 判定在 client
- [ ] §B 认证用 `Depends(verify_service_or_user)`（跟 `/v1/schema/register` 对齐）
- [ ] §C `DispatchSubscriber.__init__` 加 `outbox_client` 参数（方案 C.1）；给出 lifespan wiring 片段
- [ ] §D metrics 全部 defer 到 PR-32，log 实现；PR-32 ticket 追加 5 条 bullet
- [ ] §E 删掉自适应 poll_interval；保留"空 tick 不 INFO 日志"
- [ ] §F 改写 §6，用 `DispatchResult.raw["action"]`（Queue 已有），不需改 Queue 侧
- [ ] §G Graceful shutdown 选 G.2（完成当前 `_deliver_one` 即退）
- [ ] §H crash 测试用 `claim_ttl_ms=100` 参数化，不用 sleep(30)
- [ ] §I payload_json `JSONDecodeError` → permanent fail

修完直接 T1，不用再 review 一轮。

### T1 commit 拆分建议（5~6 段）

PR-16 跨 Business / Entangled 两个 submodule，一定要严格拆：

1. `feat(entangled): add /v1/outbox/claim|mark_delivered|mark_failed endpoints (PR-16)`
2. `test(entangled): outbox endpoints contract + concurrency (PR-16)`
3. `feat(business): dispatch_subscriber full poll/claim/deliver/retry (PR-16)`
4. `test(business): subscriber claim/retry/crash-recovery (PR-16)`
5. `chore: outbox-compact.sh + docs/runbook (PR-16)`
6. 主仓：`chore: bump submodules for PR-16` + `docs: PR-16 checked off + metrics defer to PR-32`

**拒绝 PR-15 那种 `44dca1c` 把 submodule bump 和 docs 塞同一个 commit 的复发**。

### 一条元提醒

这次 preflight 克制度可以，没再漂到 PR-17/PR-26。但暴露了另一个问题：**多个决策点都做到了"方向对 + 细节 handwave"**（§3 "或打上特殊标记"、§1 端点但无 schema、§6 "需要暴露监控"）。

下次写 preflight 时，每个决策点后面自问一句："**如果我现在去开 T1，这段话给不给得出具体的 SQL / Pydantic 模型 / 代码片段？**"给不出就没做完。
