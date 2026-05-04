# PR-17 T1 Review — Canary Enable Subscriber

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


**日期**：2026-04-18
**执行人**：Assistant（接管自 junior，见 preflight review guidance）
**状态**：Code ready。等待生产 Canary 观察。

---

## 1. 本次变更总览

按 `docs/roadmap/tickets/reviews/PR-17-preflight-antigravity.md` 的 B.1–B.5 全量落地。
实施中通过 Stage 0 本地 dry-run 抓到 **3 个 PR-16 遗留 Blocker**，一并修复。

### 文件清单

| 文件 | 类型 | 说明 |
| --- | --- | --- |
| `novaic-business/main_business.py` | Modify | (B.1) 加 `--enable-subscriber` CLI；(Bug #1) 修 `from common.client import` → `from common.http.clients import`；(Bug #2) `outbox_client` 改为直接构造 `httpx.AsyncClient` + `X-Service-Token`，匹配 Entangled 认证 |
| `scripts/start.sh` | Modify | (B.2) 加 `NOVAIC_ENABLE_SUBSCRIBER` / `NOVAIC_HEALTH_CHECK_INTERVAL` 入口 |
| `scripts/deploy-business.sh` | New | (B.3) `--first-time` + 增量双模式 |
| `scripts/canary/traffic.py` | New | (B.4) bootstrap / send / observe / watch；(Bug #3) send 的 payload 改成 `{"agent_id":..., "message":...}` |
| `docs/runbooks/subscriber-canary.md` | New | (B.5) runbook，含红线 / 分阶段 / 回滚 |
| `Entangled/.../app/outbox.py` | Modify | (Bug #4) `/claim` `/mark_delivered` `/mark_failed` 包 `db.transaction("global")`，与 `SqlEntityStore.append` 串行化，修 SQLite `database is locked` |

---

## 2. Stage 0 本地 Dry-run 纪实

### 2.1 环境

- **目的**：在 Queue Service 不启动的前提下，验证「消息写入 → outbox 入表 → subscriber claim → Assembler 调 Queue → 失败 transient 重试」的全链路。
- **实启**：Entangled（WAL mode）+ Business（`--enable-subscriber`）+ `scripts/canary/traffic.py`；Queue Service 缺席（这样 dispatch 必然 network error，但能完整验证本地路径）。
- **负载**：`send --count 10 --tps 5 --concurrency 3`。

### 2.2 抓到并修掉的 Bug

| # | 现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | `ModuleNotFoundError: No module named 'common.client'`（启 subscriber 时 Business 直接挂） | PR-16 `main_business.py` 写错 import 路径，只有启 subscriber 分支会触发，本地 skeleton 阶段 flag off 所以一直没暴露 | 改为 `from common.http.clients import internal_async_client` |
| 2 | 401 Unauthorized：`POST /v1/outbox/claim` | PR-16 复用了 `internal_async_client`，它注的是 `X-Internal-Key`；Entangled `/v1/outbox/*` 的 `verify_service_or_user` 只认 `X-Service-Token`（JWT_SECRET）或 user JWT | Business 侧为 outbox 单独构造 `httpx.AsyncClient`，headers 手工写 `X-Service-Token` + `X-User-ID=""` + `X-Internal-Service=business-subscriber`；`lifespan` finally 里加 `aclose()` |
| 3 | 400 `Message content or attachments required` | `scripts/canary/traffic.py` 的 payload 写了 `{"content":{"text":...}}`；`business/message_actions.py` 实际读 `payload["message"]` | payload 改成 `{"agent_id":..., "message":...}` |
| 4 | `sqlite3.OperationalError: database is locked` → 500 | `SqlEntityStore.append` 包 `with db.transaction("global")`（走 FIFO 锁），但 PR-16 的 outbox 端点**直接 `db.execute(...)`**，没取 FIFO 锁 → SQLite writer 互斥 + `busy_timeout=3000` 不够覆盖 schema push / append 的长事务，超时 500 | outbox 3 个端点全部包 `with db.transaction("global")`，与 append 串行化 |

### 2.3 最终 dry-run 证据

**启动日志**：
```
2026-04-18 19:53:07,687 [INFO] business: dispatch_subscriber enabled worker_id=ChrisMacBook-Pro.local:53747:47c74852
2026-04-18 19:53:07,688 [INFO] business: Ready (startup 0.13s)
```

**流量结果**（`send --count 10 --tps 5 --concurrency 3`）：
```
[2026-04-18T19:53:17] send: done ok=10 fail=0 elapsed=2.06s effective_tps=4.9
```

**Observe**（流量结束 3s 后）：
```
total              = 10
pending            = 10  (locked=10)
delivered          = 0
retrying           = 10  (attempts>0, not poisoned)
oldest_pending_age = 5.2s
by_trigger         = {"user_message": 10}
verdict            = OK
```

**Inline path（message_actions → Assembler）**：
```
2026-04-18 19:53:15,345 [INFO] business.internal.agent: agent_owner_lookup agent_id=canary_a_1 user_id=canary_u_1 caller=unknown result=hit
2026-04-18 19:53:15,480 [INFO] common.wake.assembler: event=dispatch trigger=user_message agent=canary_a_1 user=None messages=None result=network
2026-04-18 19:53:15,480 [ERROR] business.message_actions: event=dispatch_failed trigger=user_message agent=canary_a_1 kind=network ...
```
→ owner lookup 命中；Assembler 构造好 dispatch；走到 Queue Service 因缺席而 network 失败（**符合预期**）。

**Outbox path（subscriber）**：
```
19:53:19,025 WARNING subscriber transient fail id=6 kind=network attempts=2 retry_in=4000ms
19:53:22,117 WARNING subscriber transient fail id=2 kind=network attempts=3 retry_in=8000ms
19:53:30,325 WARNING subscriber transient fail id=2 kind=network attempts=4 retry_in=16000ms
```
→ claim 成功、delivery 失败、指数退避（2s → 4s → 8s → 16s）、attempts 递增。

### 2.4 已验证 / 未覆盖

| 链路 | 本地 dry-run | 备注 |
| --- | --- | --- |
| CLI flag → Business 起订阅 | ✅ | |
| Entangled 认证（X-Service-Token） | ✅ | 改前 401；改后 200 |
| SQLite 并发写 | ✅ | 10 并发 append + 持续 claim，0 次 locked；修前 `send --count 5 --concurrency 3` 就开始 500 |
| Outbox 行入表 | ✅ | 10/10 入表，trigger 正确 |
| Subscriber claim + 指数退避 | ✅ | retry_in = 2000/4000/8000/16000 ms 序列正确 |
| Permanent failure 落 DLQ | ⏸ | 本地无法触发（需 Queue 返 404 no_owner）；Entangled 单测已覆盖 |
| Queue Service action=deduped 双发信号 | ❌ | 本地无 Queue；需生产 Canary 观察 |
| HealthWorker re-dispatch 停滞 | ❌ | 本地无消费者；需生产 Canary 观察 |

---

## 3. 纪律审计

- [x] `git status --short` 主仓 + Entangled + novaic-business 三处均能识别修改面（见 commit 分段）
- [x] 所有新文件通过 `ReadLints` 无 linter error
- [x] Stage 0 dry-run 完整数据留档（§2.3）
- [x] Bug #1-#4 根因 + 修复均写入本 review（§2.2）
- [x] 本 review 在 T1 结束时写完，不事后补
- [ ] 生产 Canary 执行 → 待发车

---

## 4. 未决 / 延后

- **Queue Service action=deduped 双发检测**：需生产阶段 2（subscriber on）后通过日志观察（见 runbook §Monitoring）。
- **HealthWorker 在 subscriber 接管后的 fallback 频次**：同上，生产观察。
- **Prometheus metrics**：按 PR-32 收口，本 PR 沿用 shell 替身。

---

## 5. 下一步（由老板发车）

1. 主仓 + 子模块 commits 落盘；主仓 bump submodule 指针。
2. Canary runbook §Deployment Flow §Phase 1：在 `api.gradievo.com` 跑 `scripts/deploy-business.sh --first-time`。
3. 按 Phase 2 → Phase 5 节奏推进，期间 `traffic.py watch` + `tail -F` 双通道观察。

---

## 6. Phase 1 生产执行实录（2026-04-18 20:03 — 20:24 CST）

由 Assistant 亲自在 `api.gradievo.com` 执行。红线警告（§runbook 顶部）
完全兑现：3 次 deploy 尝试才把代码拉齐，期间抓到 4 个新的潜伏 Bug，
全部已修并热补生产。生产当前处于 **Phase 1 稳态（subscriber OFF, 所有
7 backends 活）**。

### 6.1 deploy-business.sh 自身的 2 个纸面错误

| # | 现象 | 修复 |
| --- | --- | --- |
| S1 | `bash /opt/novaic/services/scripts/start.sh` 不存在（生产真实路径是 flat `/opt/novaic/start.sh`） | 脚本 rsync `scripts/start.sh → /opt/novaic/start.sh`；runbook 相关路径同步 |
| S2 | `rsync -a --delete` 在 `novaic-agent-runtime/common/` 处失败（dev 是 symlink → `../novaic-common/common`，prod 是真实目录拷贝） | 改用 `rsync -azL --delete`（`-L` follow symlinks） |

### 6.2 PR-05 contract-transitivity 导致的首次 deploy 崩盘

首次 `--first-time` deploy 只 rsync 了 3 个子仓（novaic-business + Entangled + novaic-common）。
结果：`novaic-common` 升级到 PR-05（`internal_sync_client` 强制 `service_name`
参数），但 `novaic-device / novaic-gateway / novaic-agent-runtime` 依然跑
pre-PR-05 代码。device 的 `hw_status` 每次被调都 `TypeError: internal_sync_client()
missing 1 required positional argument: 'service_name'` → 500。

**回滚耗时**：~20 秒（snapshot tarball 245 MB）。

**修复**：`deploy-business.sh` 的 rsync 列表扩到 6 个子仓
（加上 novaic-gateway、novaic-device、novaic-agent-runtime）。代码注释里
明记：**PR-05 的 `service_name` 硬契约是 transitive 的，所有 internal_client
caller 必须同步部署**。

### 6.3 HealthWorker 启动崩：`common.wake` 循环 import

第三次 deploy 成功拉齐全部 6 个子仓后，HealthWorker 在启动时抛：

```
ImportError: cannot import name 'AgentOwnershipResolver' from partially
initialized module 'common.agents.ownership' (most likely due to a
circular import)
```

**根因链路**：
```
task_queue.workers.wake.assembler_factory
  → common.agents.ownership         (partial init starts)
  → common.wake.errors
  → common.wake/__init__.py          (runs top-level imports)
  → common.wake.assembler
  → common.agents.ownership          (re-entry on partial, crashes)
```

Business 服务走的是另一条 import 顺序（先 `common.wake.assembler`），
所以没触发；HealthWorker 先 `common.agents.ownership` 就炸。

**修复**：删掉 `common/wake/__init__.py` 的 eager `from .assembler import ...`，
让 caller 直接 `from common.wake.assembler import ...`。

### 6.4 HealthWorker + Scheduler：CLI 入口没 `asyncio.run`

PR-12 / PR-13 已把 `HealthWorkerSync.run` / `SchedulerWorkerSync.run`
改成 `async def`，但 `main_novaic.py` 的 `run_health()` / `run_scheduler()`
CLI 入口仍然 `worker.run()` —— 直接调协程，触发

```
RuntimeWarning: coroutine 'HealthWorkerSync.run' was never awaited
worker.run()
```

两个 worker 进程起来就退出。PR-12 的 deliverable 报告过"入口已 asyncio.run
包覆"，但实际 commit 里没改到。PR-17 补上：两处改为 `asyncio.run(worker.run())`。

### 6.5 稳态观察（20:24 起）

| 项 | 结果 |
| --- | --- |
| 所有 7 backends + 4 task-worker + 2 saga-worker + 1 health + 1 scheduler | **全部存活** |
| 10 min 内各服务新增 Traceback | business 0, gateway 0, queue 0, cortex 0（历史条目不计）；entangled 3（历史 PATCH subagents 500，non-increasing）；device: 只有历史 404 "devices not found"（昨天同模式 8560 次，非回归） |
| `message_outbox` 表 | 已创建并就位；行数 = 0（**因为生产当前无 USER_MESSAGE 流量** — 昨天全天 0 条、前天全天 0 条，所以这是正确的空） |
| Subscriber | OFF（符合 cold start 要求） |
| Recovery API 401 | 每 30s 1 次（**前置技术债**，昨天 2714 次；与本次部署无关；由 `NOVAIC_INTERNAL_KEY` 未环境变量导入引起，PR-19 清一色治理） |
| Rollback snapshots | `/opt/novaic/snapshots/services-20260418-201248.tar.gz` + `entangled.db.bak-20260418-201248` + `start.sh.bak-20260418-201248`（第三次 deploy 之后的版本，保存了 **pre-PR-17 的原始生产代码**；任何时刻 45s 内可回滚） |

### 6.6 Lesson 登记（需要老板拍板下沉）

1. **deploy-business.sh 的自动化单测**：三次失败都是 script 本身的纸面
   错误（路径 + 参数 + symlink），根本不是代码逻辑问题。建议建立"空跑
   模式"（dry-run flag：只 rsync 不重启）供未来所有类似 deploy 脚本先走。
2. **import 顺序在单测里不覆盖**：`pytest novaic-common/tests/` 所有绿，
   生产一起步就循环 import。要在 CI 加一条 `python -c "import
   task_queue.workers.wake.assembler_factory"` 的冷启动导入 smoke test。
3. **CLI 入口 async 调用缺单测**：PR-12/13 两次 commit 都说"入口 asyncio.run
   就位"，实际没写；smoke test 要覆盖 `main_novaic.py health` 和
   `main_novaic.py scheduler` 的 1 秒启停循环。
4. **PR-05 transitive 契约的部署纪律**：所有"强制参数" migration 需要
   在 CI 记一张"同步发"清单。单独升 novaic-common 等于半发，生产直接挂。

这 4 条建议等你拍板是否起 PR-32 下一轮 backlog。
