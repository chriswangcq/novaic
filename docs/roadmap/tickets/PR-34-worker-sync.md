# PR-34 — Worker 同步化（infra-track RFC, v2）

**类型**：infrastructure refactor（与 message-wake 主线 PR-01~PR-32 正交）
**状态**：**v2 — 决策已锁定**（见 §H），结构从"原子大 PR"**改为 5 步分 PR**（§D）
**前置**：PR-33（env 收窄）完成或并行，但独立 mergeable
**作者**：PR-17 Canary 收尾期的副产品
**读者**：junior / senior reviewer
**架构原则**（v2 基座，贯穿全篇决策）：
1. **系统简单** — async 是病毒式 coloring，只在 FastAPI edge 保留；worker = 独立进程（心智模型统一）；每步迁移 ≤ 400 行 diff，可独立审可独立回滚。
2. **无静默失败** — `asyncio.create_task` + 未 handled 的异常、`await` 忘写、`AsyncMock` vs `MagicMock` 混用—— 这类 async bug **全部是静默失败**。把 async 面收缩到 framework edge 是工程上最可行的围堵。

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

### C.1 原则（附 CI 强制）

**async 只出现在两个地方**：

1. FastAPI route handler 所在文件（框架强制）、FastAPI middleware / WebSocket handler
2. 明确标注 `# ASYNC-EDGE: reason=...` 的少数合法特例（如 Cortex LLM fan-out，未来真需要时才加）

**Worker / business 模块 / common 模块一律同步**。调用 FastAPI → 内部工具 → HTTP client 的链路从头到尾同步，只在最外层（FastAPI handler）bridge。

### C.1.1 CI 守卫（必须，反静默失败）

新增 `scripts/ci/check_no_internal_async.py` 脚本（或等价 ruff 规则），CI 必跑：

- 扫描所有 `async def`，白名单：
  - 所在文件有 `@router.` / `@app.` / `FastAPI(` / `WebSocket` 装饰器或导入
  - 文件头注释含 `# ASYNC-EDGE: reason=...`
  - `tests/` 目录下的 `@pytest.mark.asyncio` 测试
- 违反即 fail CI，打印具体行号。
- 这是唯一的长期护栏——否则半年后 async 会重新感染。

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

Workers（全部独立进程，由 start.sh 拉起；统一心智模型）：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  HealthWorker (sync proc)    │  │  SchedulerWorker (sync proc) │
│  while True:                 │  │  while True:                 │
│      do_work(); time.sleep() │  │      do_work(); time.sleep() │
└──────────────────────────────┘  └──────────────────────────────┘
┌──────────────────────────────────────────────────────────────┐
│  DispatchSubscriber (sync proc) ← §C.3, 与 Business API 分离 │
│  while True:                                                 │
│      claim_batch(); deliver_all(); time.sleep()              │
└──────────────────────────────────────────────────────────────┘
```

### C.3 DispatchSubscriber 改为独立子进程（v2 关键升级，反静默失败）

v1 RFC 写的是 `threading.Thread(daemon=True)`。v2 升级为 **独立子进程**，由 `start.sh` 拉起，和 HealthWorker / SchedulerWorker 同构。

**选 subprocess 而不是 thread 的两条硬理由**：

| 方案 | 简单性 | 静默失败暴露 |
|---|---|---|
| `asyncio.create_task` | 最差（要 lifespan + done_callback + 取消协调） | **静默**（task 默默死掉） |
| `threading.Thread(daemon=True)` | 一般（1 行启，但 run() 里必须 try/except 包死） | **半静默**（死了 Business 本身不掉，日志里有 traceback 但外部监控看不到） |
| **独立子进程**（v2 选择） | 最好（和 HealthWorker/SchedulerWorker 同心智模型） | **最好**（进程 exit code 可观测，`ps` 能看到，挂了 start.sh 重启时会报错） |

**额外收益**：
- Subscriber 崩溃不影响 Business API 响应（天然隔离）。
- 日志分离：`/opt/novaic/data/logs/subscriber.log`（过去是和 Business 混在一起）。
- 部署翻 canary 只需 restart subscriber 进程，不碰 Business API（PR-33 的 subscriber_enabled 开关仍生效）。

**实现约束**：
- 新增 `novaic-business/main_subscriber.py` 入口（复用 `main_novaic.py` 的 `argparse + logging` pattern）。
- `scripts/start.sh` 加一段 subscriber 拉起逻辑，仿照 health/scheduler 启动块。
- `scripts/start.sh --stop` 必须能 graceful kill subscriber（SIGTERM → 等 claim 超时 → SIGKILL）。

### C.4 HTTP client 选择

- **Sync 路径**：`httpx.Client`（`common/http/clients.py::internal_sync_client`，已存在，是 `internal_client` alias 指向的那个）
- **Async 路径**（仅 FastAPI handler 直接调外部 API 时用）：`httpx.AsyncClient`（`internal_async_client`，保留但调用点急剧减少）
- 连接池：sync Client 每个 worker 一个（复用），同 async 版本的 lifecycle 管理方式（`__enter__ / __exit__` 显式 close）。

### C.5 Worker 主循环写法

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

## §D 实施拆分：v2 改为 5 步分 PR（每步独立 mergeable + 独立 rollback）

v1 草稿写的"Phase 2+3+4 原子 merge"是错误决定——大 PR 审 review 时信息密度爆炸，diff 太大 reviewer 肉眼扫不完，反而成为新静默失败的温床。v2 改用 **dual-method 中间态**让每步 ≤ 400 行 diff、每步能独立回滚、每步都能在生产稳跑 48h 后再推下一步。

### 全景

| sub-PR | 代号 | 内容 | 最重要的不变量 | diff 规模 | 状态 |
|---|---|---|---|---:|---|
| 34a | **双 API** | `DispatchAssembler` / `AgentOwnershipResolver` **保留 async 方法，并列新增 sync 方法**（`assemble_and_dispatch_sync`, `resolve_sync`） | 现有 async 调用点 0 行改动，线上行为零变化 | ~250 | ✅ merged → novaic-common `4e1d191`，主仓 submodule bumped |
| 34b | **HealthWorker 先切** | HealthWorker 改用 sync 方法；`health_worker_sync.py` 内部改 sync 主循环；启动入口删 `asyncio.run` | 其他 worker / Business FastAPI 仍走 async，零耦合 | ~300（实测 199 insert + 125 del） | 🟡 PR 已开（agent-runtime#2, commit `7491837`），等 gate：PR-17 Phase 4 bake 绿 |
| 34c | **SchedulerWorker 切** | 同 34b pattern | DispatchSubscriber + FastAPI 仍 async | ~200 | ⏳ 等 34b 生产 48h bake 稳定 |
| 34d | **Subscriber 切 + 提取独立子进程** | Subscriber 改 sync + 新增 `main_subscriber.py` + `start.sh` 拉起 + Business lifespan 不再管 subscriber task | Business FastAPI handler 仍走 async 路径（`_dispatch_trigger` 仍 async，未动） | ~400 | ⏳ 等 34b/34c |
| 34e | **清理收尾** | FastAPI handler 侧 `_dispatch_trigger` 改 sync + `run_in_threadpool` bridge；删 async 方法 `assemble_and_dispatch`；加 CI 守卫；改名 `*_sync.py` → `*.py` | async 面降至最小 | ~250 | ⏳ |

### 34a — 双 API（零风险铺垫）

- `novaic-common/common/wake/assembler.py`：在 `DispatchAssembler` 类里新增 `assemble_sync`, `dispatch_sync`, `assemble_and_dispatch_sync`。三个方法完全镜像现有 async 版本，但用 `httpx.Client`。
- `novaic-common/common/agents/ownership.py`：新增 `resolve_sync`。
- **初始共享内部 state**（httpx 客户端实例）？不要共享，避免 async/sync 混用时的 connection pool 竞态。新建 `self._sync_client = httpx.Client(...)` 独立生命周期。
- **共享业务逻辑**：assemble/dispatch 的业务验证、请求构造、响应解析这些纯函数部分**必须提取成静态辅助方法**供两个版本共用，否则未来一边改一边忘就是静默 bug 温床。
- **测试**：新增 `test_assembler_sync.py` 完整 9 例用例（镜像 async 套件），CI 同时跑两套。
- **验证**：线上 0 行调用点变化，assembler 的 async behavior 完全不动。
- **可独立回滚**：revert → sync 方法消失，没人调用过，零影响。

### 34b — HealthWorker 切 sync（首只小白鼠）

**状态（2026-04-19）**：PR `chriswangcq/novaic-agent-runtime#2`，commit `7491837`，分支 `feat/pr-34b-health-worker-sync`（off `origin/main`，不依赖 PR-35 hotfix）。等 PR-17 Phase 4 bake 绿 → merge → 单独 bake 48h → 34c 开工。

**已实施内容**：

- `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`：
  - `async def run` → `def run`，`asyncio.sleep` → `time.sleep`。
  - `async def _scan_unhandled_messages` → sync 版，`await get_assembler().assemble_and_dispatch(...)` → `get_assembler().assemble_and_dispatch_sync(...)`。
  - `async def _get_client` → `def _get_client`，`httpx.AsyncClient` → `httpx.Client`。
  - `internal_async_client` import → `internal_sync_client`；`await client.post/get` → `client.post/get`；`aclose()` → `close()`。
- `novaic-agent-runtime/main_novaic.py::run_health`：删 `asyncio.run(worker.run())` 外壳，直接 `worker.run()`。`run_scheduler` 保持 async（34c 处理）。
- **测试**：`tests/test_health_dispatch.py` 整套从 `@pytest.mark.asyncio` + `AsyncMock` 迁到 sync + `MagicMock`（PR-19 新加的 4 例全在内）。新增 2 个 34b invariant locks：
  - `test_run_is_synchronous_callable` — `inspect.iscoroutinefunction` 拒绝未来把 async 偷偷塞回来的 regression。
  - `test_module_does_not_import_asyncio` — 模块级 `asyncio` 导入即 fail。
  这是对 §C.1.1 仓级 CI guardrail 的 per-file 补充，提前兜底（CI guardrail 要 34e 才上）。
- **本地验证**：`pytest tests/test_health_dispatch.py` 8/8 绿；agent-runtime 全量 32 passed 0 regressions。

**生产观察 gate（merge 后）**：单独 bake 48h，监控指标：

- `grep -c "coroutine.*never awaited" /opt/novaic/data/logs/health-*.log` → **0**（任何一个都是 regression）
- `grep -c "event=health_fallback" /opt/novaic/data/logs/health-*.log` → 正常增长（证明 sync dispatch 路径在生产流量下工作）
- `grep -c "recover_401" /opt/novaic/data/logs/health-*.log` → 保持 0（PR-19 X-Internal-Key 契约在 34b 迁移中必须无漏）

**独立回滚**：`git revert 7491837` → HealthWorker 回到 async 路径，业务无缝，HealthWorker 是 idempotent fallback 扫描，零数据风险。

**不变量**：DispatchSubscriber / SchedulerWorker / Business 全部仍走 async，34b 的破坏半径仅在 health worker 本身。

### 34c — SchedulerWorker 切 sync

- 同 34b 模式，换文件：`novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`。
- **生产观察**：bake 48h，Scheduler 的定时唤醒要在日志里能观察到（`event=scheduler_woke agent=...`）。
- **独立回滚**：revert → Scheduler 回到 async。
- **依赖**：34b 必须已稳定（证明 sync assembler API 在生产负载下工作正常）。

### 34d — Subscriber 切 sync + 提取独立子进程（最大一步，但仍 ≤ 400 行）

**两个变更同时做的理由**：Subscriber 从 sync 化转入 subprocess，其实只是把现有 `asyncio.create_task` 替换为 `subprocess.Popen`（由 start.sh 代理），代码量反而更少。但两者分步会有中间态"Subscriber 已 sync 但仍在 Business lifespan 里 `threading.Thread` 托管"——这个中间态的意义不大，不如直接一步到位。

- 新增 `novaic-business/main_subscriber.py`（复用 `main_business.py` 的 argparse / logging），`if __name__ == "__main__": subscriber.run()` 作为 subprocess 入口。
- `novaic-business/business/subscribers/dispatch_subscriber.py`：
  - `async def run` → `def run`，`asyncio.sleep` → `time.sleep`。
  - `async def _claim_batch`, `async def _deliver_one` → sync；`await self.assembler.assemble(...)` → `self.assembler.assemble_sync(...)`。
  - 改用 `httpx.Client`（外框请求 outbox 的）。
- `novaic-business/main_business.py`：删 lifespan 里 `asyncio.create_task(subscriber.run())` 和 SUBSCRIBER_ENABLED 判断（移到 start.sh，见下）。
- `scripts/start.sh`：
  - 新增 `start_subscriber()` 函数，参考现有 `start_health()` 结构。
  - 当 `ServiceConfig.SUBSCRIBER_ENABLED == true` 时拉起 subscriber subprocess。注意这个读取依赖 PR-33 §C.2 的 runtime_switches。**如果 PR-33 尚未 merge，34d 暂用 env 读取**（tech-debt 登记一行 34e 收尾时清），不要为了等 PR-33 而阻塞 34d。
  - `--stop` 支持 subscriber SIGTERM → 10s graceful → SIGKILL。
- **测试**：`tests/test_dispatch_subscriber.py` 整套 sync 迁移 + 新增 `test_subscriber_subprocess_entry_script_runs`（仅校验 `main_subscriber.py` 能 import + 立即退出）。
- **生产观察**：bake 48h，`ps aux | grep main_subscriber` 必有一条常驻进程，`/opt/novaic/data/logs/subscriber.log` 必在涨，outbox pending 保持 ≤ 1（subscriber 正常消费）。
- **独立回滚**：revert → Subscriber 回到 Business lifespan 内 asyncio task。注意 revert 时 start.sh 也回滚，subscriber subprocess 自动消失。
- **依赖**：34a（sync API 存在），34b/34c 其实不强依赖但**强烈建议**先稳，因为 34d 变更面最大。

### 34e — 清理收尾

- `novaic-business/business/message_actions.py::_dispatch_trigger`：`async def` → `def`，删 `await`。
- `novaic-business/business/internal/subagent.py::_dispatch_trigger`：同上。
- FastAPI handler 调用处：`await _dispatch_trigger(...)` → `await run_in_threadpool(_dispatch_trigger, ...)`。
- 删 `DispatchAssembler.assemble` / `.dispatch` / `.assemble_and_dispatch` 三个 async 方法（34a~34d 的调用者都已迁到 `_sync` 版）。
- 删 `AgentOwnershipResolver.resolve` async 版。
- 改名（technical-debt 第 42 行承诺）：
  - `scheduler_worker_sync.py` → `scheduler_worker.py`
  - `health_worker_sync.py` → `health_worker.py`
- 加 CI 守卫：`scripts/ci/check_no_internal_async.py`（见 §C.1.1），在 `.github/workflows/ci.yml` 里 fail-on-violation。
- 更新 `docs/architecture/agent-pipeline.md`：新增"Sync-by-default"原则节。
- 更新 `docs/roadmap/technical-debt.md`：关闭 37 行 `internal_client` 命名陷阱、42 行 `scheduler_worker_sync.py` 命名条目。
- **生产观察**：bake 7 天，确保没有 FastAPI handler 卡线程池（threadpool 默认 40，我们同时并发 ≤ 5，不会耗尽）。
- **独立回滚**：revert → async 版方法回归，34a~34d 不受影响。

---

## §E 验收 metrics（按 sub-PR 分段校验）

### 每 sub-PR 必过关

| sub-PR | 关键指标 | 手段 | 放行条件 |
|---|---|---|---|
| 34a | sync 方法测试全绿 | `pytest test_assembler_sync.py test_ownership_sync.py` | 9 + N 例全绿 |
| 34b | HealthWorker 在 prod bake 48h 无 async 残留错 | `grep -c "coroutine.*never awaited" health.log` | 0 |
| 34b | PR-19 的 4 个 health 测试迁 sync 后仍绿 | `pytest test_health_dispatch.py` | 绿 |
| 34c | SchedulerWorker bake 48h 正常唤醒 | `grep "event=scheduler_woke" health.log \| wc -l` | > 0（有定时触发） |
| 34d | Subscriber 独立子进程常驻 | `ps aux \| grep main_subscriber \| wc -l` | = 1（仅一个 subscriber 进程） |
| 34d | Subscriber bake 48h outbox 保持 drain | `sqlite3 entangled.db "SELECT COUNT(*) FROM message_outbox WHERE delivered_at IS NULL"` | ≤ 1（零流量 steady state） |
| 34e | CI 守卫拒 async 泄漏 | 故意加一个 `async def foo` 到 worker 文件 → CI 必须 fail | red ✓ |

### 整体验收（34e merge 后）

| 指标 | 手段 | 期望 |
|---|---:|---|
| repo 内 `async def` 数量（排除 tests） | `rg "async def" --type py -g '!tests/**' \| wc -l` | ≤ 原值的 **40%** |
| repo 内 `internal_async_client` 调用点 | `rg "internal_async_client" --type py` | ≤ 5 处 |
| repo 内 `asyncio.run(` 数量（非测试） | `rg "asyncio\.run\(" --type py -g '!tests/**'` | **0** |
| 全量测试 | `pytest` runtime + business + common | 全绿 |
| 生产复跑 PR-17 Phase 3 压测 | `traffic.py send --count 100 --tps 10` | p99 不劣化 > 10%，无 coroutine ERROR |

---

## §F 回滚路径（每一步独立可退）

v2 的 5-PR 结构每一步都能独立 revert 且生产**无缝回到上一步稳态**。这是 v1 "原子大 PR" 方案无法达成的关键升级——原方案整 PR revert 才算回滚，现在每步都是安全节点。

| sub-PR | 回滚动作 | 回滚后状态 | 数据风险 |
|---|---|---|---|
| 34a | `git revert <34a>` | sync 方法消失，没人调用过 | 零 |
| 34b | `git revert <34b>` + 重启 HealthWorker | HealthWorker 回到 async 路径；其他组件不受影响 | 零（HealthWorker 是 idempotent 的兜底扫描） |
| 34c | `git revert <34c>` + 重启 SchedulerWorker | SchedulerWorker 回到 async 路径 | 零 |
| 34d | `git revert <34d>` + `bash start.sh --stop && bash start.sh` | Subscriber subprocess 消失；旧 Business lifespan 内 asyncio task 复活 | **短暂 outbox 积压**（10-20s），重启后自动 drain |
| 34e | `git revert <34e>` | FastAPI handler 回走 async `_dispatch_trigger`；async 方法复活；CI 守卫消失 | 零 |

**混合回滚场景**：假如 34b 生产稳定但 34c merge 后 scheduler 异常，可以只 revert 34c，34b 保持在 sync 态——两者隔离。

**灾难场景**：假如 bake 后期（34d 已 merge）发现某个跨越 assembler 的性能问题，可一次性 revert 34d→34c→34b→34a，回到完全 async 的昨日状态，每步 revert ≤ 60s 生产影响。

---

## §G 不在本 PR 做的事（严格排除）

- ❌ 删除 `internal_async_client` 函数本身（FastAPI handler 场景还会用到几处）
- ❌ FastAPI 外部的 async（比如 WebSocket handler、Entangled 的 WS push）：这些**真的**需要 async，不碰
- ❌ Cortex 的 async（cortex 是独立服务，本 PR 范围不含）
- ❌ Entangled 的 WS handlers（Rust/Python 侧，框架约束）
- ❌ 引入新的线程池管理/concurrency 库（如 `anyio`, `trio`）—— 用 FastAPI 自带的 `run_in_threadpool` 就够

---

## §H 决策（v2，已锁定）

按"系统简单 + 无静默失败"双尺衡量后，以及对 v1 草稿的架构自审后，最终裁决：

| 决策点 | v1 倾向 | **v2 结论** | 理由（简单 / 静默失败两轴） |
|---|---|---|---|
| §C.1 async 只在 framework edge | ✅ | ✅ **锁定，并加 CI 守卫**（§C.1.1） | 简单：规则就一条，reviewer 易判。静默：没 CI 守卫则半年内必复发——async 是病毒式 coloring，人脑审不住，必须机器拒 |
| Subscriber 托管方式 | `threading.Thread(daemon=True)`（倾向） | ❌ **改为独立子进程**（§C.3） | 简单：与 HealthWorker / SchedulerWorker 心智模型统一，运维 `ps` / 日志路径一致。静默：daemon thread 挂了 Business 本身不掉、外部无感——典型静默失败；subprocess 挂了 `ps` 立刻看得见，start.sh 重启会报错 |
| Phase 2+3+4 原子 merge | 必须原子 | ❌ **拆为 5 步（34a-34e）**（§D） | 简单：每步 ≤ 400 行 diff，reviewer 能真正看完；每步可独立 bake 48h。静默：原子大 PR diff 过大就是静默 bug 温床，审不过来 |
| 中间态如何保证不破 | v1 承认 Phase 2 中间态破、必须原子 | ✅ **双 API 中间态**（34a 并列 async + sync 方法），各步单调迁移 | 简单：中间态始终有 working baseline。静默：任何步挂了可即刻独立 revert，不牵连其他 |
| `internal_async_client` 是否删 | 保留少数调用 | ✅ **保留但加调用点上限**（≤ 5 处，CI 检） | 简单：白名单 + 数量上限。静默：数量超限触发 CI fail |
| FastAPI 外 async（WebSocket/Entangled） | 不碰 | ✅ **锁定不碰**（§G） | 简单：本就是 async 的合理使用。静默：WS 协议天然要 async，硬改 sync 反而会引入更多静默 bug |

**T1 启动前提**：
- PR-17 Phase 4 bake 放绿（约 2026-04-19 22:40 UTC 满 24h）
- PR-33 进入至少 Phase 3（runtime_switches 已可读）；若 PR-33 未到，34d 用 env 过渡（登记为 tech-debt，34e 收尾清）

预估工时（v2 分 PR 版）：

| sub-PR | 工时 | 备注 |
|---|---:|---|
| 34a | 1 人·日 | 纯 add-only，双 API |
| 34b | 1 人·日 | 测试迁移占大头 |
| 34c | 0.5 人·日 | scheduler 较简单 |
| 34d | 1.5 人·日 | subprocess + start.sh 改造 |
| 34e | 1 人·日 | 清理 + CI 守卫 + 文档 |
| 小计 | **5 人·日** | 与 v1 估算同，但风险显著降低 |
