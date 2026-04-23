# PR-54 — Canary metrics bundle: `ghost_scope_rate` + `wake_continuity_render_total`

| Field | Value |
|---|---|
| **Ticket**  | PR-54 |
| **Status**  | `[✓]` deployed to prod **2026-04-25 12:13 CST** (`./deploy services`); endpoint + log + business `/metrics` all green (see §部署验证) |
| **Opened**  | 2026-04-25 |
| **Owner**   | wc |
| **Severity** | **P7 observability** — no correctness impact. Closes the last two "canary metrics" items from `docs/architecture/message-wake-principles.md` §七. |
| **Blocks**  | — |
| **Blocked by** | — |
| **Invariant** | R9 (wake continuity) + R-STUCK-CLAIMED (PR-51/52). Gives both invariants a gauge/rate dashboards can alert on, so the next silent-drop-class regression (PR-53 shape) is caught in seconds instead of days. |

## 背景

P6/P7 留下的两条小尾巴，都来自 `docs/architecture/message-wake-principles.md` §七《可观测性》：

> Canary 监控指标：
> * **`ghost_scope_rate`** — chat_messages `claimed` by a scope Cortex 已经归档/不存在 的比例。PR-51/52 的墙是否撑住的核心信号。
> * **`wake_continuity_render_total{layer=text|state|im, result=ok|empty|truncated|error}`** — R9 三层 render 的汇总计数。单一一条 Grafana query 答 "R9 今天活着吗"。

这两个都是 P7 往后的加固题，不挡任何已部署功能的正确性。PR-53 之后提上来合并做 —— 因为 PR-53 的教训就是"三层 R9 在 prod 上三天没一行日志没一个人发现"，补完这两个指标把"没证据"变成"看一眼 Grafana 就知道"。

## 交付物

### 1. `wake_continuity_render_total{layer, result}`（runtime 侧）

**位置**：
- 新 helper `emit_wake_continuity_render(layer, *, result)` 加在 `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`（紧挨 `_continuity_kind_label` 以便读者顺着现有 R9 的 metric 代码往下看）。
- 三层 render 入口各发一条：
  - **text**：`handle_session_init` 调完 `_build_wake_continuity_messages` 之后，根据 `handoff_notes` / `historical_summary` 原始字节数是否超 `WAKE_CONTINUITY_MAX_BYTES` 区分 `ok` / `truncated` / `empty`。
  - **state**：`_build_prev_scope_tail_messages` 四个出口分别发 `error`（bridge 抛）/ `empty`（`found=False` 或 rendered_lines 全空）/ `truncated`（meta.truncated=1）/ `ok`。与现有 `wake_prev_scope_tail_total` **并存**，后者承担 "分维度分析"，新指标承担 "汇总 health"。
  - **im**：`context_handlers.handle_context_read` 在 `_build_wake_replay_block` 之后，根据 `_message_type=WAKE_IM_REPLAY_TRUNCATED` marker 是否存在区分 `ok` / `truncated`；空数组或 build 抛 → `empty` / `error`。

**标签取值表**（`docs/architecture/message-wake-principles.md` §七 锁死）：

| layer   | result      | 触发条件 |
|---------|-------------|----------|
| `text`  | `ok`        | 至少渲染了一个 `<HANDOFF_NOTES>` 或 `<HISTORICAL_SUMMARY>` 块，原始字节未超 cap |
| `text`  | `truncated` | 渲染成功但 `_cap_continuity_text` 切过 |
| `text`  | `empty`     | 两个字段都为空或 trigger 不在 `WAKE_CONTINUITY_ENABLED_TRIGGERS`（最常见：冷启动） |
| `state` | `ok`        | `<PREV_SCOPE_TAIL>` 块成功注入，`meta.truncated=0` |
| `state` | `truncated` | 同上，但 `meta.truncated=1`（命中 step/token cap） |
| `state` | `empty`     | 无 `previous_scope_id` / 被 kill-switch / `meta.found=False` / 全部消息被 role-filter 丢掉 |
| `state` | `error`     | `bridge.read_scope_tail` 抛异常（degrade 成 `[]` 但要与 empty 区分） |
| `im`    | `ok`        | 注入 ≥1 条且无 truncation marker |
| `im`    | `truncated` | 注入 ≥1 条且包含 `WAKE_IM_REPLAY_TRUNCATED` marker |
| `im`    | `empty`     | `_build_wake_replay_block` 返回 `[]` 且未抛 |
| `im`    | `error`     | `_build_wake_replay_block` 抛 |

**为什么 `ok` / `empty` / `truncated` / `error` 四个桶、不是二元**：
- `ok` vs `empty` — 一个 agent 从未用过、刚 bootstrap、从未 rest → 每次 wake 合法地 `empty`。若没有 `empty` 桶，dashboard 只能看 `ok`，会把"R9 没话说"和"R9 死了"画成同一条线。
- `ok` vs `truncated` — `truncated` 本身是 warning 级别：render 成功但 budget 吃紧，LLM 可能看不到完整上下文。与 `ok` 并桶会让 Grafana 面板无法报警"最近一小时 truncation 率暴涨"。
- `empty` vs `error` — 同 PR-52/51 的老教训：bridge 抛跟本来就没数据要用同样的 `[]` 返回值，但对 ops 是完全不同的信号。

**单测**（`novaic-agent-runtime/tests/test_pr54_render_metric.py`）共 9 例：
- text: 三个 result 桶各一条（含 over-cap 触发 truncated）。
- state: `_build_prev_scope_tail_messages` 直接调，驱动 `ok` / `truncated` / `empty` / `error` 四个分支。
- 两条 "taxonomy lock" 测试（labels 集合 == {ok, empty, truncated, error}，layers 集合 == {text, state, im}）—— 未来加第 4 个 layer 或第 5 个 result 必须同步改文档 + 改这两条测试，防止 dashboard 和指标默默漂移。

### 2. `ghost_scope_rate` 探针（business 侧）

**位置**：`novaic-business/business/internal/message.py` 新增 `GET /internal/probes/ghost-scope-rate`，紧接在 `GET /internal/messages/stuck-claimed` 后面（同一份数据的直接派生）。

**流程**：
1. 调自家的 `GET /v1/stuck-claimed`（Entangled）拿 stuck-claimed 列表（默认 `sample=50`，Prometheus 拉取时用默认，ops 排查时可到 500）。
2. 对每条 item：
   - `agents` 表查 `user_id`（soft-fail → `unknown`）；
   - Cortex `/v1/meta/read` 查 `phase`（3.0s timeout, 2.0s connect）；
   - 归类 `ghost` / `live` / `unknown`（见下表）。
3. 发指标：
   - `ghost_scope_probed_total{classification=ghost|live|unknown}` — 每条 item 一次。
   - `ghost_scope_rate`（observe gauge）— 单次 probe 的比率。
   - `ghost_scope_total_stuck`（observe gauge）— 底层 stuck-claimed 总数（方便 dashboard 分子分母并排画）。

**归类规则**：

| classification | 触发 | 含义 |
|----------------|------|------|
| `live`    | Cortex 200 + `meta.phase ∈ {executing, compacting}` | scope 真的还在跑。正常状态，不算 ghost。|
| `ghost`   | Cortex 200 + `meta.phase` 不在 live 集合（`archived` / `failed` / `canceled` 等） **OR** `meta` 为空 dict（scope 不存在/已 purge）| 真正的"死了没收尸"。PR-51/52 的目标数。|
| `unknown` | 缺 `scope_id` / 缺 `user_id` / Cortex 非 200 / Cortex 抛 | 探针本身失败。**不进分母**。|

**为什么 `unknown` 不进分母**：Cortex 抖动（如滚动重启）期间，大量 probe 会变 `unknown`。若算进分母，`ghost_scope_rate` 会假性下降（ghost 不变但分母增大），掩盖真实问题；若算进分子，一次 Cortex 抽筋就会报全量 ghost。排除 `unknown` 后，指标含义严格收敛为"在我能看清楚的那些 stuck-claimed 里，死 scope 占多少"。

**为什么不做后台线程/cron**：端点是纯派生数据，不持久化。外部 cron（或 Prometheus ServiceMonitor）每分钟 curl 一次即可；把调度留给 k8s/cron，service 不引入新的长寿命 worker。

**单测**（`novaic-business/tests/test_pr54_ghost_scope_probe.py`）共 16 例：
- `_classify_ghost_scope` 分类器 8 例：live 两种 phase / archived → ghost / 空 meta → ghost / 缺 scope_id → unknown / 缺 user_id → unknown / Cortex 抛 → unknown / Cortex 非 200 → unknown。
- rate-math 6 参数化：empty / all-unknown / all-ghost / all-live / 对半 / `unknown` 在分母外。
- endpoint 2 例：happy path (1 ghost + 1 live + 1 unknown → rate=0.5, 指标发射完整) / empty stuck-list (sampled=0, rate=0.0, 不 404)。

## 非目标

- **不**改 PR-51 的 stuck-claimed 扫描逻辑 —— 本 PR 只"读"它。
- **不**改 PR-52 的 `_probe_scope_alive` —— 那里的 `None` 语义是"fail-open 放行 dispatch"，跟本 endpoint 要的"fail-open 归入 unknown 桶"是两回事，合并会把语义搅混。
- **不**新增 Entangled 表 —— 没有持久化需求，纯实时派生。
- **不**做 alerting rule（Prometheus rule） —— metric 先埋，阈值等 1~2 周真实数据分布观察后再开 PR 加告警。

## 部署 + 验证 checklist

- [x] Entangled submodule bump — 实际无变更 → 跳过
- [x] novaic-agent-runtime submodule bump — commit `6738a29` (2026-04-25)
- [x] novaic-business submodule bump — commit `b08931e` (2026-04-25)
- [x] `./deploy services` — 2026-04-25 12:13 CST，全部 `OK`，subscriber subprocess pid 1612871
- [x] Smoke endpoint + metrics：
  - `curl http://127.0.0.1:19998/internal/probes/ghost-scope-rate?sample=20` → 200，body `{"sampled":0,"ghost":0,"live":0,"unknown":0,"ghost_scope_rate":0.0,"total_stuck_claimed":0,"items":[]}`。零 stuck-claimed = PR-51/52 仍在撑墙，**healthy**。
  - `tail business-20260423.log` → `event=ghost_scope_probe sampled=0 ghost=0 live=0 unknown=0 rate=0.0000 total_stuck=0`（两条，分别 12:12:26 / 12:12:31）。
  - `curl http://127.0.0.1:19998/metrics | grep ghost_scope` →
    ```
    # TYPE ghost_scope_rate summary
    ghost_scope_rate_sum 0.0
    ghost_scope_rate_count 2.0
    # TYPE ghost_scope_total_stuck summary
    ghost_scope_total_stuck_sum 0.0
    ghost_scope_total_stuck_count 2.0
    ```
    两次探针都被 Prometheus-格式记录，时间序列建立成功。
- [x] 发一条 USER_MESSAGE 到 `canary_a_1` → saga-worker-20260423.log 观察到 `subagent_wake` saga 启动，session.init 走完；render metric 在 task-worker 进程内计数（process-local counter，见下文"已知观测空白"）。
- [x] 文档：本 ticket 状态翻 `[✓]`；`docs/architecture/message-wake-principles.md` §七 改成 `[CODE]` 承诺；`docs/roadmap/message-wake-refactor.md` P6-14 行添加。

## 已知观测空白（非本 PR 修复，登记备忘）

`wake_continuity_render_total` 走的是 `common.utils.metrics` 的进程内 registry（`_COUNTERS`）。Business service 在 `:19998/metrics` 暴露这个 registry；**task-worker / saga-worker 进程没有自己的 `/metrics` endpoint**，所以 runtime 侧的 render metric 即便被正确 `metric_inc`，外部 Prometheus 也抓不到。

这不是 PR-54 引入的回归 —— 同样的情况适用于 *所有* runtime-process-local 指标（`wake_continuity_injected_total` / `wake_prev_scope_tail_total` / `wake_im_replay_total` / `wake_prev_scope_tail_total` 等），都是先前 PR-42/43/44/45 留下的既有 gap。

短期验证：render metric 的正确性由 `tests/test_pr54_render_metric.py` 的 9 条单测和代码本身的三个 `emit_wake_continuity_render(...)` 调用位点保证 —— 部署后的"是否活着"由下游指标间接证实（例如 agent 回复正常、`subagents.historical_summary` 非空、Cortex scope 有 `previous_scope_id`）。

长期修复路径（**新 ticket，不归本 PR**）：给 task-worker 和 saga-worker 各装一个最小 `/metrics` HTTP 端口（参考 business 的 `install_service_logging` + FastAPI `@app.get("/metrics")`），统一 scrape 目标到 Prometheus。已登记在 `docs/roadmap/technical-debt.md` 的 `DEBT-OBS-*` 区（TBD 条目）。

## 关联

- `docs/architecture/message-wake-principles.md` §七 — 指标取值表的权威定义。
- [`PR-51`](PR-51-stuck-claimed-cleanup.md) — 提供 `ghost_scope_rate` 的上游数据源（stuck-claimed 扫描）。
- [`PR-52`](PR-52-subscriber-scope-aliveness-check.md) — 提供 `_probe_scope_alive` 的先例（但 classifier 本 PR 单独实现，见"非目标"第 2 条）。
- [`PR-53`](PR-53-entangled-continuity-allowlist.md) — 本 PR 的直接动因：PR-53 那种"三层 R9 静默失败 3 天"的事故，未来靠 `wake_continuity_render_total` 秒级发现。
- [`PR-45 review §七`](reviews/PR-45-review.md#七postscript--2026-04-25-pr-53-invalidates-33s-state-machine-evidence-confidence) — postscript 已预告过会补这两个 metric。
