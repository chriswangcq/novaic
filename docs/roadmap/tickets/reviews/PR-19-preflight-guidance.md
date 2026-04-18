# PR-19 Preflight 指引（HealthWorker 后遗症收尾）

**读者**：junior
**写者**：senior reviewer（PR-17 Canary 期间副产品归档）
**状态**：此文件是**任务导航**。写者需先回答 §F discovery、把 §B 范围钉死、拿批复后才进 T1 写代码。

---

## §A 背景与入口

PR-17 Canary 阶段 1/2 观察期在生产日志里发现两类 HealthWorker 噪声，按 PR-17 `§H 不在本 PR 做的事` 的范围纪律，**不在 PR-17 内修**，独立开 PR-19 处理。相关记录已登记在 `docs/roadmap/technical-debt.md` 的 "HealthWorker 遗留观察项 (PR-19 追踪)"。

**2026-04-18 22:00 UTC 生产现场实测数据**（`/opt/novaic/data/logs/health-20260418.log`）：

| 指标 | 计数 | 说明 |
|---|---|---|
| `Recovery API returned 401` | 796 | `/api/queue/recover/all` 调用缺 `X-Internal-Key` 被 Queue middleware 拒。每 30s 一次循环噪声 |
| `API error (400): user_id is required` | 88 | Fallback dispatch 链路打出 `user_id=""` 到 Queue，被 `/api/queue/dispatch` 返回 400 |
| `no_owner` 显式计数 | 0 | 现代码 `DispatchError(kind=no_owner)` 分支没被触发过 |
| 400 loop 针对的 agent_id | `415f6cfd4e5b4a04911b66cb8ab2cad7` | 在 `agents` 表里 **存在且 `user_id` 完好**（`155cc065-...`） |

---

## §B 范围（严格收窄，3 点）

### B.1 `HealthWorker` → Queue Service 调用补 `X-Internal-Key`

- 文件：`novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- 症状：`_get_client()`（line 86-93）通过 `internal_async_client(service_name=...)` 建 httpx client，但 common wrapper **只注入 `X-Internal-Service`，不注入 `X-Internal-Key`**。Queue Service 的 `_queue_internal_key_middleware` 只认 key，于是两条 Queue 调用都 401：
  - `POST /api/queue/recover/all`（line 145）
  - `GET /api/queue/sessions`（line 198）
- 修法（与 `DispatchAssembler.__init__` 同一 pattern）：
  ```python
  queue_key = ServiceConfig.QUEUE_SERVICE_INTERNAL_KEY or ""
  extra_headers = {"X-Internal-Key": queue_key} if queue_key else {}
  self._client = internal_async_client(
      service_name="runtime-health",
      base_url=self.queue_service_url,
      headers=extra_headers,
      timeout=httpx.Timeout(10.0, connect=3.0),
  )
  ```
- 测试：mock httpx, 断言 `/api/queue/recover/all` 请求的 header 里含 `X-Internal-Key`。

### B.2 查清并修掉 `400 user_id is required` 循环

- 症状：agent `415f6cfd...` 有合法 `user_id` 但 HealthWorker fallback 仍以 `user_id=""` 调 `/api/queue/dispatch`。
- 日志格式 `Fallback dispatch failed for {agent_id}: API error (400): ...` 对应 `_scan_unhandled_messages` 外层 `except Exception as e:`（line 246），**不是** `DispatchError` 分支（line 237-245）。说明抛的是非 `DispatchError` 的其他异常类型。
- **Discovery（必须做完才能提交实施方案）**：
  1. 把 prod `health.log` 的一次 400 触发前后 30 行（带 traceback）抓回本地：
     ```bash
     grep -B 3 -A 30 "Fallback dispatch failed for 415f6cfd" /opt/novaic/data/logs/health-20260418.log | head -80
     ```
     如果 traceback 丢失，本地加 `logger.exception(...)` 补打后复现。
  2. 定位 "API error (400): " 这条字符串的**抛出点**（不是 `DispatchAssembler.dispatch` 的 `DispatchError`，大概率是 `task_queue/client.py` 或 `common/agents/ownership.py` 的老分支）。
  3. 回答：resolver 是否返回了 `user_id=""`（某种静默失败）？还是 assembler 被跳过、直接走了 legacy task_queue client？
- 候选修法（依据 §F discovery 选一个，不能并存）：
  - (a) 如果是 `AgentNotOwnedError` 或非 `DispatchError` 型异常：把 `_scan_unhandled_messages` 的 `except Exception` 收窄成 `except (DispatchError, AgentNotOwnedError, httpx.HTTPError)`，把过滤集合扩到 `{"no_owner", "queue_400", "agent_not_owned"}`。
  - (b) 如果是 legacy task_queue client 直发：删掉 legacy path，只走 `get_assembler().assemble_and_dispatch`。
  - (c) 如果是 resolver 侧偶发空 user_id：在 `AgentOwnershipResolver.resolve` 对 empty user_id 响应直接 raise `AgentNotOwnedError` 而不是返回空串。
- 一律补一个 `event=health_skip reason=<kind>` 的 INFO 日志 + `HealthWorkerMetrics.skipped_count` 计数，替代目前的 `WARNING "Fallback dispatch failed for {id}: API error ..."`（这个格式既掩盖 kind 又难 grep）。

### B.3 孤儿数据清洗脚本（降级为可选）

**实测结论**：2026-04-18 prod DB 盘点:
- `SELECT COUNT(*) FROM chat_messages WHERE agent_id NOT IN (SELECT id FROM agents)` = **0**
- `SELECT COUNT(*) FROM agents WHERE user_id = '' OR user_id IS NULL` = **0**
- 无 `agent_ownership` / `scheduled_wake` 表（原 tech-debt 条文猜测错误，这两个表在当前 schema 里根本不存在）

**结论**：当前生产没有孤儿数据需要清洗。PR-19 **不再写** `scripts/data-tools/cleanup-orphan-schedules.py`。如果 B.2 discovery 阶段发现其他**结构性**孤儿（比如 `api_keys` 指向已删 agent、`agent_state` 滞留），再视情况追加脚本，**并更新本文件**说明发现与清洗口径。

---

## §C 实施与验证阶段

### 阶段 0：Discovery + 本地单测（在本仓写代码前必须做完）

1. `§A` 三表三计数在本地 / 测试环境复现（至少 401 那条可以通过 `QUEUE_SERVICE_INTERNAL_KEY` 环境变量设错触发）。
2. 把 400 循环 traceback 抓出来、定位抛出点、**把 §B.2 的候选修法圈选到一个**，在 preflight 报告里明示。
3. 本地加 `logger.exception` 复现一次 400 循环，把 traceback 贴到 preflight 报告。

### 阶段 1：单测 + 回归（本仓）

1. 单测 `test_health_worker_injects_internal_key`（contract test，与 `novaic-common/tests/test_assembler.py::test_dispatch_injects_internal_key` 同 pattern）。
2. 单测 `test_health_worker_filters_<b2_kind>_no_user_id`（用 fixture 模拟 resolver 返回空 user_id / 抛特定异常，断言 HealthWorker 不再调 `/api/queue/dispatch`，只打 `event=health_skip` 一条）。
3. 单测 `test_health_worker_skipped_metric_counter`：断言 `metrics.skipped_count` 增 1。
4. 跑 `pytest novaic-agent-runtime/tests/test_health_dispatch.py` + PR-17 尾声的 `test_health_worker_fallback_user_id`（如存在），确认 **没有回归**。

### 阶段 2：生产灰度

因为 HealthWorker 默认每 30s 跑一次、单线程且不直接影响用户请求，灰度**不需要 flag**（改动本身是去噪，不是行为开关）。但生产部署后需在 1 个健康检查周期（30s）内验证：

- `health-YYYYMMDD.log`  不再出现 `Recovery API returned 401`（新条数 = 0）
- 若 agent 415f... 仍被扫到（还未清理），出现 `event=health_skip reason=<b2_kind>` 而不是 `API error (400): user_id is required`
- `metrics.tasks_recovered` / `sagas_recovered` 从 0 开始增长（证明 recovery 真的跑通了）

**回滚**：本 PR 纯去噪，真出问题就回滚到 PR-17 结束态的 HealthWorker 代码。

---

## §D 回滚 playbook

```bash
# 假设 PR-19 commit 是 <PR19_SHA>，PR-17 尾声是 <PR17_SHA>
cd /opt/novaic/services/novaic-agent-runtime
git checkout <PR17_SHA> -- task_queue/workers/health_worker_sync.py
bash /opt/novaic/services/scripts/start.sh --stop
bash /opt/novaic/services/scripts/start.sh
tail -f /opt/novaic/data/logs/health-$(date -u +%Y%m%d).log
```

**副作用**：
- 回滚后 401 循环会回到每 30s 一条（798/天的水位），但 recover_all 本来就没跑成过，业务无退化
- 回滚前落在 `event=health_skip` 的消息会退回到 `Fallback dispatch failed for ...: API error (400)` 格式，语义等价

---

## §E log 替代 metric 表（PR-32 metrics 上线前）

| PR-19 引入的指标 | 替代查询 | 目标 |
|---|---|---|
| `health_recover_success_total` | `grep -c "Recovered: " health-*.log` | 单调增 |
| `health_recover_401_total` | `grep -c "Recovery API returned 401" health-*.log` | **PR-19 上线后 = 0** |
| `health_skipped_total{reason=...}` | `grep -c "event=health_skip" health-*.log` | 有增量代表过滤生效 |
| `health_fallback_error_total` | `grep -c "Fallback dispatch failed" health-*.log` | **PR-19 上线后新增 = 0** |

---

## §F Discovery 实测结果（2026-04-18 22:13 UTC 收尾）

### F.1 `recover_all` 401 — ✅ 仍在发生

```
$ grep -c "Recovery API returned 401" /opt/novaic/data/logs/health-20260418.log
# → 827
# 当前 health.log（rotating，python logging 格式）每 5s 一次：
# 2026-04-18 22:17:15 [INFO] httpx: POST .../api/queue/recover/all "HTTP/1.1 401 Unauthorized"
```

根因确认：
- `queue_service_internal_key` 在 `novaic-agent-runtime/config/services.json` 与 `novaic-common/config/services.json` 都已配置（`"queue-internal-dev"`），**配置齐全但 HealthWorker 的 httpx client 没把它塞到 header**。
- `common.http.clients.create_internal_async_client` 只注入 `X-Internal-Service`（line 33）；**Queue Service 侧中间件要求 `X-Internal-Key`**（见 `queue_service/main.py::_queue_internal_key_middleware`）。
- 这与 `DispatchAssembler.__init__`（`novaic-common/common/wake/assembler.py:74-85`）的修法同源，当时已显式注入，HealthWorker 没跟上。

注：log 里同时出现的 `WARNING common.http.clients: NOVAIC_INTERNAL_KEY is not set.` 是 **无关 red herring** —— 那是未来统一 key 的前瞻性警告（technical-debt 第 33 行），当前系统用的是 `QUEUE_SERVICE_INTERNAL_KEY` per-service key，完整存在。**PR-19 不要去动那条警告**。

### F.2 `400 user_id is required` — ✅ 已随 PR-12 部署自动修复（88 条是部署前残留）

时间序列证据：

| 时段 | 日志格式 | 条数 | 路径 |
|---|---|---|---|
| 12:05:46 ~ 12:55:31 UTC | `Fallback dispatch failed for 415f...: API error (400): user_id is required ...` | 88 | 老代码 / 未知非-DispatchError 异常分支 |
| 12:55:32 UTC 起 | `Skip waking agent=415f...: queue_400` | 76 | PR-12 `_scan_unhandled_messages` 的 `DispatchError kind=queue_400` 显式分支 |

12:55 UTC 是当日 agent-runtime 重启（新 health-worker pid），新代码已在走 `DispatchError` 分支把 `kind=queue_400` 吞掉。`"API error (400): user_id is required ..."` 是 **Queue Service 自己抛**出的字符串（`queue_service/main.py` 里 `HTTPException(400, "user_id is required ...")`），新代码已经正确识别成 `DispatchError(kind=queue_400)`。

**所以 §B.2 的三个候选修法里 `(a)` 已经在生产生效了**。PR-19 只需要把这条分支**再打磨一下**：改 log 级别从 `ERROR` 到 `INFO`（现在每次 dispatch 都被 filter 过滤掉却打 ERROR，会误报），改 event 名为 `event=health_skip reason=queue_400`，顺便加个 `HealthWorkerMetrics.skipped_count`。

**附加发现**：agent `415f6cfd4e5b4a04911b66cb8ab2cad7` 在 `agents` 表里**有合法 `user_id=155cc065-...`**。推测 PR-12 之前的问题是 `AgentOwnershipResolver` 初次部署时 TTL cache 或首次查询落空，老代码路径没做好 fallback 直接发了 `user_id=""`。已由 PR-12 的 resolver 串行初始化 + DispatchError 分支治本。

### F.3 `"API error ("` 抛出点 — ✅ 定位完成

repo grep `"API error ("` 的 raise 点已确认不在 novaic-*-runtime 现代码里。历史位置在 `task_queue/client.py` 的老分支，PR-12 迁移后已被 `DispatchAssembler.dispatch`（novaic-common/common/wake/assembler.py）+ `DispatchError(kind=queue_400)` 取代。可以在 PR-19 commit 里顺手删掉 `task_queue/client.py` 中残留的老字符串定义（如果还有 dead code）。

### F.4 resolver 空 user_id 分支 — ⏳ 推迟到独立 common PR

`AgentOwnershipResolver.resolve()` 已经在 404 / 400 时抛 `AgentNotOwnedError`。但空字符串 `{"user_id": ""}` 的分支**没有单测**。本次 PR-19 **不扩** common 子模块，仅在 guidance 里登记：下次 common PR 需补 `test_resolve_empty_user_id_raises_agent_not_owned` + 对应修法。

### F.5 其他缺 `X-Internal-Key` 的 Queue 方向调用

扫描 `internal_async_client` / `internal_sync_client` 全 repo callsites，筛选指向 Queue Service 的：

| 文件:行 | 端点 | 状态 | 是否纳入 PR-19 |
|---|---|---|---|
| `novaic-agent-runtime/task_queue/workers/health_worker_sync.py:89` | `/api/queue/recover/all`, `/api/queue/sessions` | ❌ 缺 key（B.1 主修） | ✅ 修 |
| `novaic-business/business/internal/message.py:116` | `/api/queue/recover/cancel-all`（`interrupt_agent`） | ❌ 缺 key（同类 bug，生产当前未触发） | ✅ 修（novaic-business 顺手 commit，不算扩范围） |
| `novaic-common/common/wake/assembler.py:81` | `/api/queue/dispatch` | ✅ 已注入 | — |

其他 `internal_async_client` 调用点**全部指向 Business / Device / Gateway / Entangled / Cortex**，这些服务不强制 `X-Internal-Key`（有些有 `CallerLoggingMiddleware` 只日志不拦截），不受此 class bug 影响。

### F.6 新出现的 "fallback dispatch storm"（2026-04-18 PR-17 收尾时发现）

`health.log` 在 `canary_a_1` 上重复打了 1183 次 `event=health_fallback messages=108 result=ok action=buffered`。根因：压测脚本灌进去的 108 条 USER_MESSAGE 一直 `read=0, processed=0`，HealthWorker 每 5s 扫到 → dispatch 到 Queue → Session Coordinator buffer 但 `model_id=canary` 没真 LLM 让 saga 消费，于是无限循环。

**已在本次 discovery 结束时手工止损**（22:16 UTC）：
```sql
UPDATE chat_messages SET read=1, processed=1, status='read'
 WHERE agent_id='canary_a_1' AND read=0;
-- rows_marked = 108
```
验证：22:16:50 后 `health.log` 不再出现 `agent=canary_a_1` 的 fallback 行。

**这不算 PR-19 的 bug**（HealthWorker 只是 naive 重试器，unread 没 clear 就会一直扫），但提示 PR-19 应该把 "同 agent 连续 N 次 `action=buffered` 后降频或退避"纳入**discovery 选修项**：
- 选项 α（保守）：不做退避，仅加 `event=health_fallback_buffered_streak agent=X count=N`（每 10 次打一条），便于告警
- 选项 β（激进）：同 agent 连续 K 次 action=buffered 则这一轮跳过该 agent，下一轮再试；这会让 buffered saga 的唤醒变慢

**PR-19 默认采用 α**。β 如果做，起码需要 runbook 追加一节说明降频对 SLA 的影响。

### F.7 `internal_client` 命名陷阱联动

PR-19 可以借机把 `health_worker_sync.py` 的 `from common.http.clients import internal_async_client` 保持原样（**不改为别名**），作为 technical-debt 第 37 行 alias 清理的第一个示范点（"显式导入，不走 alias"）。这是零代码变动的文档化改进，不入 commit。

---

## §G Commit 拆分

| # | 子模块 | Message |
|---|---|---|
| 1 | `novaic-agent-runtime` | `fix(health): inject X-Internal-Key on Queue Service calls (PR-19)` |
| 2 | `novaic-agent-runtime` | `fix(health): swallow <b2_kind> before Queue dispatch + event=health_skip (PR-19)` |
| 3 | `novaic-agent-runtime` | `test: health worker internal-key + skip path regression (PR-19)` |
| 4 | 主仓 docs | `docs(technical-debt): close PR-19 HealthWorker items` |
| 5 | 主仓 | `chore: bump novaic-agent-runtime for PR-19` |

**Declare Done 前自检**：
1. §E 四条 metric 的 log grep 输出分别贴进 PR-19 preflight report（不是这个 guidance 文件）。
2. Commit 1 / 2 能各自独立 revert。
3. 只删代码 → 测试不红。

---

## §H 不在本 PR 做的事（严格排除）

- ❌ Queue Service middleware 本身的改动（401 的根因在 middleware 是正确的、不能放松）
- ❌ `internal_client` alias 全局替换（technical-debt 第 37 行，等独立清理 PR）
- ❌ 写孤儿数据清洗脚本（§B.3 已降级）
- ❌ 动 `DispatchAssembler` / `AgentOwnershipResolver`（除非 §F discovery 4 找到 resolver 返回 empty user_id 的 bug，那样也先单独开一个 common 的 fix PR，不绑 agent-runtime）
- ❌ 改 HealthWorker 调度周期或 `MAX_FALLBACK_PER_TICK` 阈值

---

## 老板决策需要在 preflight report 里承诺

- ✅ §B.1 修 X-Internal-Key 是无争议去噪
- ⏳ §B.2 候选修法三选一（a/b/c）必须在 preflight report 给出 discovery 证据 + 选择理由 + 回避其他两条的原因
- ✅ §B.3 不写清洗脚本（除非 discovery 推翻）

---

## §I 交付记录（PR-19 T1 实施收尾，2026-04-18 22:45 UTC）

### I.1 代码变更（1 个 commit 批次）

| 文件 | 变更 |
|---|---|
| `novaic-agent-runtime/task_queue/workers/health_worker_sync.py` | B.1 `_get_client` 注入 `X-Internal-Key` + B.2 `event=health_skip` + B.6 `_buffered_streak` rate-limited 日志 + `fallback_skipped` 指标 |
| `novaic-business/business/internal/message.py` | B.5 `interrupt_agent` 调 `/api/queue/recover/cancel-all` 补 `X-Internal-Key` |
| `novaic-agent-runtime/tests/test_health_dispatch.py` | 新增 4 个用例覆盖 B.1 / B.2 / B.6 / streak-cleared |

### I.2 测试结果

```text
novaic-agent-runtime: 24 passed
novaic-business:      15 passed
novaic-common:        31 passed (excl. cross-repo contract dir)
```

覆盖点：
- `test_health_worker_injects_internal_key_header` — B.1 契约
- `test_health_worker_skips_key_header_when_secret_missing` — 防御性：空 key 不注入空 header
- `test_health_worker_skip_logs_as_info_and_increments_skipped` — B.2 降噪 + 指标
- `test_health_worker_buffered_streak_rate_limited` — F.6 streak 1st / 10th / 20th
- `test_health_worker_buffered_streak_cleared_on_non_buffered` — 转场一行 `event=health_fallback_streak_cleared`

### I.3 生产验证

重启时间：`2026-04-18T22:40:30Z`（`stop + start` 全栈）。

| 指标 | 重启前 | 重启后 20s |
|---|---:|---:|
| `Recovery API returned 401` | 3544（累计） | **+0** |
| `/api/queue/recover/all → 200` 状态码 | 10797 | **14340**（+3543） |
| `/api/queue/recover/all → 401` 状态码 | 3946 | **不再增长** |
| `messages_by_agent` | （canary_a_1 × 108） | `{}`（F.6 止血后已归零） |

401 归零命令（可复现）：

```bash
ssh root@api.gradievo.com 'awk "/^2026-04-18 22:40:30/{flag=1} flag" \
  /opt/novaic/data/logs/health.log | grep -c "Recovery API returned 401"'
# → 0
```

### I.4 未触发的分支（已验证设计正确，仅缺压力场景）

- `event=health_skip reason=queue_400` — prod 当前 `messages_by_agent={}`，没有触发条件。单测覆盖充分。
- `event=health_fallback_streak_cleared` — 同上。
- `event=health_fallback_streak agent=… streak=1|10|20` — 同上。

PR-17 Phase 4 bake 期间若有任何真实 agent 进入 buffered streak，`pr17-bake.log` 的 `hlth_log` 断面会自动记下。
