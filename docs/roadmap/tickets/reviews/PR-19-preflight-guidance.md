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

## §F Discovery（必须实测回答）

1. **`recover_all` 401 是否正在生产发生**？
   - `ssh root@api.gradievo.com 'grep -c "Recovery API returned 401" /opt/novaic/data/logs/health-$(date -u +%Y%m%d).log'` ≥ 1 即确认
   - **2026-04-18 答案：796/日** ✅
2. **400 循环的 traceback**：从 `health.log` 抓整条异常栈（见 §B.2 discovery 步骤 1）。
3. **抛 "API error (400): " 的代码位置**：repo-wide grep 字符串 `API error (` 找到具体 raise。
4. **resolver 是否会返回空 user_id**？把 `AgentOwnershipResolver.resolve` 路径跑一遍单测，覆盖 Business 返回 `{"user_id": ""}` / `404` / `500` / 超时 四种分支，断言各自抛什么。
5. **是否有其他**调用方同样缺 `X-Internal-Key`？`rg "internal_async_client|internal_sync_client" --glob '!common/http/clients.py'` 扫一遍列表，挑出所有指向 Queue Service 的调用点确认 header 完整性。PR-19 顺手在同一 commit 里修掉其他 Queue 方向的同类调用（范围必须在本文件里列清楚；发现 Cortex / Gateway 等方向的就转新 PR，不扩本 PR）。
6. **是否影响 `internal_client` 命名陷阱技术债**（technical-debt.md 第 37 行）？PR-19 可以借机强制 `health_worker_sync.py` 显式 `from common.http.clients import internal_async_client`（不用别名），作为 alias 清理的第一个示范点。

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
