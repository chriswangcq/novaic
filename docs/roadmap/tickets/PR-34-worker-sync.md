# PR-34 — Worker 同步化（infra-track RFC）

**类型**：infrastructure refactor（与 message-wake 主线 PR-01~PR-32 正交）
**状态**：草稿（RFC），待老板审阅后进入 T1
**前置**：PR-33（env 收窄）完成或并行，但独立 mergeable
**作者**：PR-17 Canary 收尾期的副产品
**读者**：junior / senior reviewer

---

## §A 背景

过去一个月（PR-10~PR-17），async 相关 bug **每一例都不是业务逻辑错误**，全是语义错位：

| # | Bug | 根因 | 出处 |
|---|---|---|---|
| 1 | `run_health()` 直接调 async 函数未 await → coroutine 泄漏 | `asyncio.run()` 忘包 | PR-12/13 regression，fix: `b2ab490` |
| 2 | `DispatchAssembler` 调用 `_client.post` 报 `TypeError` | `internal_client` alias 是 sync，async 上下文误用 | PR-10 T1 |
| 3 | `_claim_batch` 异常每 0.5s 刷屏 | async `asyncio.sleep` 退避逻辑丢失 | PR-16, fix: PR-17 Canary 尾声 |
| 4 | HealthWorker `recover/all` 401 每日 800+ | `internal_async_client` 只注 `X-Internal-Service`，调用方误以为 headers 已对齐 | PR-12 遗留，fix: PR-19 `27276d6` |
| 5 | `assembler_factory` 读不存在的 `BUSINESS_INTERNAL_URL` | async 改造期间 URL 配置漏迁 | PR-17 Phase 2 hot-patch |

**共同点**：async 污染面广，签名一改就七个上下游跟着改，而 CPython GIL 环境下对我们这种 10~100 qps 吞吐的服务 **性能收益近乎为零**。

---

## §B 当前 async 使用面盘点（repo 实测）

### B.1 核心 async 类与函数

| 组件 | 文件 | async 方法 | 当前状态 |
|---|---|---|---|
| `DispatchAssembler` | `novaic-common/common/wake/assembler.py:87,115,150` | `assemble`, `dispatch`, `assemble_and_dispatch` | async + httpx.AsyncClient |
| `AgentOwnershipResolver` | `novaic-common/common/agents/ownership.py:37` | `resolve` | async + httpx.AsyncClient |
| `HealthWorkerSync` | `novaic-agent-runtime/task_queue/workers/health_worker_sync.py:118` | `run`, `_scan_unhandled_messages`, `_get_client` | async 内核 + `asyncio.run()` 入口壳 |
| `SchedulerWorker` | `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py:87,167` | `run`, `_check_and_wake` | 同上 |
| `DispatchSubscriber` | `novaic-business/business/subscribers/dispatch_subscriber.py:55,90,129` | `run`, `_claim_batch`, `_deliver_one` | async，由 Business lifespan 的 `asyncio.create_task` 托管 |

### B.2 async 调用点（`await assembler.*`）

| 文件 | 行 | 调用方是 sync/async/FastAPI |
|---|---|---|
| `novaic-business/business/message_actions.py:56` | `_dispatch_trigger` | **FastAPI async handler 通过 send_action 调用** |
| `novaic-business/business/internal/subagent.py:409` | `_dispatch_trigger` | 同上 |
| `novaic-business/business/subscribers/dispatch_subscriber.py:146` | `_deliver_one` | **worker**（PR-34 改 sync） |
| `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py:167` | `_check_and_wake` | **worker**（PR-34 改 sync） |
| `novaic-agent-runtime/task_queue/workers/health_worker_sync.py:246` | `_scan_unhandled_messages` | **worker**（PR-34 改 sync） |

5 个调用点里有 **3 个是 worker**，占 60%。全部改 sync 之后，assembler 只剩 FastAPI 一个 async 调用场景。

### B.3 FastAPI 的约束

- FastAPI route handler **必须保持 async**（框架约定，换不了）。
- Async handler 调 sync blocking IO 会阻塞 event loop → 用 `asyncio.to_thread(...)` 或 `fastapi.concurrency.run_in_threadpool(...)` 桥接。
- 实测 Business service 同时处理 2~5 个并发 request，线程池开 10 个足够。

---

## §C 目标态（Post-PR-34）

### C.1 原则

**async 只出现在两个地方**：

1. FastAPI route handlers（框架强制）
2. 真正的并发 fan-out（目前 repo 里没有这种场景，未来若有明确需要时再开个例）

**Worker / business 模块 / common 模块一律同步**。调用 FastAPI → 内部工具 → HTTP client 的链路从头到尾同步，只在最外层（FastAPI handler）bridge。

### C.2 类层次（sync 化后）

```
┌──────────────────────────────┐
│  FastAPI async handler       │  ← async, handled by framework
│  (message_actions.send_action, subagent.* routes)
└─────────────┬────────────────┘
              │ await run_in_threadpool(
              │     sync_dispatch_trigger, ...)
              ▼
┌──────────────────────────────┐
│  _dispatch_trigger(sync)     │  ← sync shim (PR-34 改造)
└─────────────┬────────────────┘
              │ (direct call)
              ▼
┌──────────────────────────────┐
│  DispatchAssembler(sync)     │  ← sync, uses httpx.Client
│    .assemble_and_dispatch()  │
└─────────────┬────────────────┘
              │ (direct call)
              ▼
┌──────────────────────────────┐
│  AgentOwnershipResolver(sync)│  ← sync, uses httpx.Client
│    .resolve()                │
└──────────────────────────────┘

Workers（独立进程）：
┌──────────────────────────────┐
│  HealthWorker(sync)          │
│  SchedulerWorker(sync)       │  ← 直接 while True + time.sleep
│  DispatchSubscriber(sync)    │     直接调 assembler（零 asyncio）
└──────────────────────────────┘
```

### C.3 HTTP client 选择

- **Sync 路径**：`httpx.Client`（`common/http/clients.py::internal_sync_client`，已存在，是 `internal_client` alias 指向的那个）
- **Async 路径**（仅 FastAPI handler 直接调外部 API 时用）：`httpx.AsyncClient`（`internal_async_client`，保留但调用点急剧减少）
- 连接池：sync Client 每个 worker 一个（复用），同 async 版本的 lifecycle 管理方式（`__enter__ / __exit__` 显式 close）。

### C.4 Worker 主循环写法

PR-13 / PR-16 时把 worker 主循环从 `time.sleep` 改成了 `asyncio.sleep`，**本次 PR-34 全部回退**：

```python
# Before (PR-13~PR-17)
async def run(self):
    while self._running:
        await self._do_work()
        await asyncio.sleep(self.interval)

# After (PR-34)
def run(self):
    while self._running:
        self._do_work()
        time.sleep(self.interval)
```

Worker 进程入口从 `asyncio.run(worker.run())` 改为 `worker.run()`，`main_novaic.py:run_health()` 的 `asyncio.run(...)` 壳彻底删掉。

---

## §D 实施拆分

### Phase 1 — `AgentOwnershipResolver` 同步化（pure leaf, zero blast radius）

- `novaic-common/common/agents/ownership.py`: `httpx.AsyncClient` → `httpx.Client`，`async def resolve` → `def resolve`。
- 调用点只有 `DispatchAssembler.assemble`（Phase 2 同步迁）和一个 test mock。
- **测试**：`novaic-common/tests/test_ownership.py`（如有）—— 去掉 `asyncio.run()` 包装。
- **验证**：单独重跑 resolver 的单元测试，全绿再 merge。

### Phase 2 — `DispatchAssembler` 同步化

- `novaic-common/common/wake/assembler.py`: 三个方法 `assemble`, `dispatch`, `assemble_and_dispatch` 全变 sync。
- `httpx.AsyncClient` → `httpx.Client`，`await self._client.post(...)` → `self._client.post(...)`。
- `_close()` / `aclose()` 对应改 `close()`。
- **影响调用点**（Phase 3/4 改）：
  - `business/message_actions.py::_dispatch_trigger`
  - `business/internal/subagent.py::_dispatch_trigger`
  - `business/subscribers/dispatch_subscriber.py::_deliver_one`
  - `agent-runtime/scheduler_worker_sync.py::_check_and_wake`
  - `agent-runtime/health_worker_sync.py::_scan_unhandled_messages`
- **测试**：`novaic-common/tests/test_assembler.py` 全 9 例从 `@pytest.mark.asyncio` + `await` 改为同步调用。估计 ~100 行 test diff。

### Phase 3 — 3 个 Worker 同步化

对每个 worker：

1. 主循环：`async def run` → `def run`，`asyncio.sleep` → `time.sleep`。
2. 业务方法：`async def _xxx` → `def _xxx`，所有 `await` 去掉。
3. HTTP 客户端：`internal_async_client` → `internal_sync_client`（= `internal_client` alias，已有）。
4. Worker 启动入口（`main_novaic.py::run_health` / `run_scheduler` / Business lifespan 里的 subscriber task）：
   - HealthWorker: `asyncio.run(worker.run())` → `worker.run()`（直接跑在 Python subprocess）
   - SchedulerWorker: 同上
   - DispatchSubscriber: Business lifespan 里原 `asyncio.create_task(subscriber.run())` → `threading.Thread(target=subscriber.run, daemon=True).start()`
5. 测试：`test_health_dispatch.py`, `test_dispatch_subscriber.py` 去掉 `@pytest.mark.asyncio`，mock 从 `AsyncMock` 改 `MagicMock`。估计 ~300 行 test diff。

### Phase 4 — FastAPI handler 桥

`business/message_actions.py::_dispatch_trigger` 和 `business/internal/subagent.py::_dispatch_trigger` 改为 sync 版（Phase 2 已让 assembler 是 sync）。调用方仍是 async FastAPI handler：

```python
# Before
async def send_action(...):
    ...
    await _dispatch_trigger(agent_id, user_id, msg_id)  # _dispatch_trigger was async

# After
from fastapi.concurrency import run_in_threadpool

async def send_action(...):
    ...
    await run_in_threadpool(_dispatch_trigger, agent_id, user_id, msg_id)
```

**验证**：关键 e2e — 发一条 chat_reply 消息，走完 message_actions → assembler → queue_service → saga 全链路，200 OK + DB 状态正确。

### Phase 5 — 清死代码与命名

- `scheduler_worker_sync.py` → `scheduler_worker.py`（technical-debt.md 第 42 行早就说要改，借本 PR 搂走）。
- `health_worker_sync.py` → `health_worker.py`。
- `common.http.clients` 的 `internal_client` alias：**保留**（因为调用方现在都期望 sync，alias 是正确的）。technical-debt.md 第 37 行那条"命名陷阱"顺便降级为 ✓ 已解决（async 场景消失，alias 不再产生歧义）。
- `main_novaic.py` 里所有 `asyncio.run(worker.run())` 删掉，直接 `worker.run()`。

### Phase 6 — 文档

- `docs/architecture/agent-pipeline.md`: 添加一节 "Sync-by-default, async-only-at-framework-edge"，把原则和桥接模式写清楚。
- `docs/roadmap/technical-debt.md`:
  - 关闭第 37 行 `internal_client 命名陷阱`
  - 关闭第 42 行 `scheduler_worker_sync.py 命名已过时`
  - 关闭第 44 行 `HealthWorker 空 user_id` 对应的 fallback scan 相关条目（其实 PR-19 已经关，本 PR 再确认一次）

---

## §E 验收 metrics

| 指标 | 手段 | 期望 |
|---|---:|---|
| repo 内 `async def` 数量 | `rg "async def" --type py -g '!tests/**' \| wc -l` | ≤ 原值的 **40%**（仅 FastAPI routes + middlewares 保留） |
| repo 内 `internal_async_client` 调用点 | `rg "internal_async_client" --type py` | ≤ 5 处（只剩 FastAPI handler 直调外部 API 的极少数场景） |
| repo 内 `asyncio.run(` 数量 | `rg "asyncio\.run\(" --type py` | **0**（全删） |
| 全量测试 | `pytest` runtime + business + common | 全绿（现 70 例基础上可能 ±10 例数量变化，看合并后 test case 数） |
| 生产 canary 短压测 | 复跑 PR-17 Phase 3 的 `traffic.py send --count 100 --tps 10` | 延迟 p99 不劣化 > 10%；无 coroutine-related ERROR |

---

## §F 回滚路径

- Phase 1~4 每个都是独立 commit + 独立 revert 可行。
- **Phase 2（assembler 同步化）是关键节点**：它之前，workers 仍用 async assembler（旧状态）；它之后，workers 还没转 sync 但 assembler 已经是 sync → **这个中间态是破的**（worker 的 `await` 会报错）。
- **风控**：Phase 2 + Phase 3 / Phase 4 必须在同一 PR 里 merge，不可拆分。RFC 里把这条写死。
- 整 PR 回滚路径：revert merge commit，所有调用点回到 async 状态，业务无缝。

---

## §G 不在本 PR 做的事（严格排除）

- ❌ 删除 `internal_async_client` 函数本身（FastAPI handler 场景还会用到几处）
- ❌ FastAPI 外部的 async（比如 WebSocket handler、Entangled 的 WS push）：这些**真的**需要 async，不碰
- ❌ Cortex 的 async（cortex 是独立服务，本 PR 范围不含）
- ❌ Entangled 的 WS handlers（Rust/Python 侧，框架约束）
- ❌ 引入新的线程池管理/concurrency 库（如 `anyio`, `trio`）—— 用 FastAPI 自带的 `run_in_threadpool` 就够

---

## §H 老板决策需要在 T1 前确认

- ✅ §C.1 原则"async 只在 framework edge"是否接受？
- ✅ §D Phase 3 的 Subscriber 用 `threading.Thread` 取代 `asyncio.create_task`，是否 OK？（我倾向是，worker 就应该是独立线程，而不是共享 event loop）
- ✅ Phase 2+3+4 必须原子 merge（不可拆）—— 这条工程纪律接受吗？
- ⏳ Subscriber 由 Business 进程内线程托管 vs 独立子进程：倾向**线程**（零外部依赖，`daemon=True` 随进程退出），但独立子进程也可行（PR-14 outbox 的设计本来就允许多实例）。T1 前决定。

审通过后进入 T1，预估 **5 人·日** 完成所有 6 个 Phase + 测试重写 + 生产压测。
