# PR-55 — Retire the phantom `subagent_rest` / `historical_summary` / `handoff_notes` pipeline

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
|---|---|
| **Ticket**  | PR-55 |
| **Status**  | `[x]` closed; later PR-65..PR-70 and PR-83..PR-85 completed the active-path cleanup and guardrails |
| **Opened**  | 2026-04-23 |
| **Owner**   | wc |
| **Severity** | **Cleanup / debt** — no user-visible regression, but the code it deletes was never doing what its docs/tests claimed, and continued maintenance (PR-42 / PR-45 / PR-49 / PR-53) kept investing in features that physically cannot run. |
| **Blocks**  | Any wake-continuity redesign: currently impossible to reason about because five "summary paths" coexist, only one of which (`skill_end.report`) is actually alive. |
| **Blocked by** | — (PR-53 already landed; this is pure removal on top) |
| **Invariant** | R-ZOMBIE: *when an LLM-facing tool is removed from `tool_schemas.py`, every executor / saga / column / injection / test / doc that assumed the tool exists must be removed in the same PR, or planted with a `# DEAD` marker plus expiry date.* |

## 误导链（为什么这笔债积到现在）

所有后续开发者（包括 PR-42/-45/-49/-53 的作者，也就是我）都以为：

> "LLM 会在休息前调用 `subagent_rest(handoff_notes=..., progress=...)` 这个工具，把自己这一觉的交接信息写到 `subagents` 表里；下次醒来 Business subscriber 把这些字段注入 prompt 的 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` 块。"

**这句话从 2025 年中期起就是假的**。`novaic-cortex/novaic_cortex/tool_schemas.py::BUILTIN_TOOL_SCHEMAS` 只暴露：

```python
skill_begin, skill_end, chat_reply,
subagent_spawn, subagent_send, subagent_report, subagent_query, subagent_cancel,
sleep
```

**没有 `subagent_rest`**。rest 由 `react_actions.decide_rest` 在「stack 空 / reply_no_followup / round cap」时**系统自动触发**，LLM 没这把钥匙。

真正活着的 per-scope summary 只有一条路：

```
LLM → skill_end(scope_id, report="...")
    → Cortex POST /v1/scope/end (is_root=False)
    → workspace.complete_child_scope(path, report)
    → 写 {scope}/summary.md
    → 之后父 scope 的 context_stack.engine 读回，折叠为 [Skill 'x' completed]\n<report>
```

根 scope 的 `archive_root_scope(scope_id, summary)` 也写 `summary.md`，但 `summary` 参数源自 rest saga 的 `generate_simple_summary` 步（**当前吐空字符串**），且根 scope 的 `summary.md` **从不被任何消费方读取**（context_stack 只折叠子 skill，不折叠根 scope 自身）。

所以线上 3 个月来的实况是：

| 所谓的机制 | 实际状态 |
|---|---|
| LLM 调 `subagent_rest(handoff_notes=...)` | ❌ 工具不存在于 schema，LLM 从未调用过 |
| `subagents.handoff_notes` 列 | ❌ 线上全表 NULL，PR-53 也没能救它（写入路径空） |
| `subagents.historical_summary` 列 | ❌ PR-53 修完允许写入后，源头 `generate_simple_summary` 吐空串 → 还是 NULL |
| Business `continuity_resolve` → `<HANDOFF_NOTES>` 注入 | ❌ 永远 `has_handoff=0` |
| Business `continuity_resolve` → `<HISTORICAL_SUMMARY>` 注入 | ❌ 永远 `has_summary=0` |
| `<PREV_SCOPE_TAIL>` 从上一个 scope 尾部取 | ✅ **这是唯一活着的跨 scope 续写机制** |
| 子 skill 折叠成 `[Skill 'x' completed]\n<report>` | ✅ 活，由 `skill_end.report` 驱动 |

## 方向

**保留**：
- `subagents.last_scope_id` / `last_scope_archived_at`（`<PREV_SCOPE_TAIL>` 定位锚点）
- `skill_end.report` → `complete_child_scope` → `summary.md` → `render_scope_fold` 这条链
- `<PREV_SCOPE_TAIL>` 消费路径（Business subscriber → Cortex `read_scope_tail`）

**删除**：
- `subagent_rest` LLM 工具执行器 `tool_handlers._exec_subagent_rest`（PR-49 埋的占位符）
- `subagents.handoff_notes` 列 + 写入 / 读出路径
- `subagents.historical_summary` 列 + 写入 / 读出路径
- Rest saga 的 `generate_simple_summary` 步 + `_build_cortex_scope_end_payload.report` 字段 + `session.generate_summary` handler + `task_queue/utils/simple_summary.py` 全文件
- Business `continuity_resolve` 里 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` 两个块的构造
- Entangled `EXTRA_ALLOWLIST` 里的 `historical_summary`
- 所有残留测试 / 文档引用

**延后（显式非本票）**：
- 根 scope 归档时是否需要一个 LLM 写的 report（当前完全没有）— 这是真正的设计问题，另开 PR。
- `<PREV_SCOPE_TAIL>` 的内容补全（chat_reply arguments 被丢弃等）— 本票不碰。

## 阶段分解（可各自独立 commit / revert）

### F1 — 删 `subagent_rest` LLM 工具残留

**文件**：
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - 删 `_exec_subagent_rest()` 函数（~100 行）
  - 删 `TOOL_EXECUTORS["subagent_rest"]` 注册
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_subagent_rest.py` — 删整个文件

**风险**：零。LLM schema 里没有这个工具，dispatcher 永远不会命中这一路。

**验证**：
- `rg -n '"subagent_rest"' novaic-agent-runtime novaic-common` 应只剩 saga 内部命名（`SUBAGENT_REST_SAGA` 等字符串字面量）

### F2 — 删 `generate_simple_summary` saga step

**文件**：
- `novaic-agent-runtime/task_queue/sagas/subagent_rest.py`
  - 删 `_build_cortex_scope_end_payload` 里读 `step_results["generate_simple_summary"]` 的分支，`report` 字段永远传 `""`（或直接从 payload 移除，让 `/v1/scope/end` 用默认值）
  - 删 `_build_set_sleeping_payload` / `_build_set_subagent_completed_payload` 里从 `generate_simple_summary` 取 `historical_summary` 的分支
  - 删 `SUBAGENT_REST_SAGA.add_task_step(name="generate_simple_summary", ...)` 注册
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
  - 删 `handle_session_generate_summary()` 函数
  - 删 topic 注册 `session.generate_summary`
- `novaic-agent-runtime/task_queue/utils/simple_summary.py` — 删整个文件
- `novaic-agent-runtime/tests/` — 删所有引用 `generate_simple_summary` / `simple_summary` 的测试用例

**风险**：归档后的根 scope `summary.md` 变空（现在就是空，只是显式化）。context_stack 不读根 scope 自己的 summary，所以不影响 LLM prompt。

**验证**：
- 手工跑一次 rest：`[cortex.scope_end] report_len=0` —— 现在也是 0，行为等价
- `[CORTEX] scope.archived summary_len=0` 保持
- 没有用户侧可感差异

### F3 — 删 `historical_summary` / `handoff_notes` 列 + 所有注入

**Entangled**（`Entangled/packages/server-python/`）:
- `entangled/sql/subagent_state.py`:
  - `EXTRA_ALLOWLIST` 移除 `"historical_summary"`（`handoff_notes` 本来不在）
  - 配套注释删掉
- `entangled/sql/schema.py`（或定义 `subagents` 列的位置）:
  - 从 CREATE TABLE 移除 `historical_summary TEXT` 和 `handoff_notes TEXT` 两列
- 迁移：SQLite `ALTER TABLE subagents DROP COLUMN historical_summary; DROP COLUMN handoff_notes;`（SQLite 3.35+）— 或宽容路线：**保留列定义但停止一切读写**，6 个月后另 PR 物理删除。建议走宽容路线，降低 downtime。
- `tests/test_subagent_state.py` — 删 allowlist 断言里对这两个字段的引用

**Runtime**:
- `task_queue/handlers/subagent_handlers.py` — `handle_subagent_set_sleeping` payload 不再带 `historical_summary`；`handle_subagent_rest`（如果还有）删 `handoff_notes` 处理
- `task_queue/sagas/subagent_wake.py` — 如果醒来时查 `historical_summary` / `handoff_notes`，删
- `tests/test_pr43_*.py`、`tests/test_pr54_*.py` — 删相关断言

**Business**:
- `business/subscribers/dispatch_subscriber.py::continuity_resolve`:
  - 删 `has_handoff` / `has_summary` 字段 + 对应 SQL SELECT 列 + 传给模板的参数
- `business/internal/subagent.py` — `update_subagent` / `get_subagent` 里移除这两个字段
- `business/schema_push.py` — 从 subagents schema 定义移除
- `tests/test_pr45_dispatch_continuity.py` / `tests/test_pr53_continuity_allowlist_e2e.py` / `tests/test_im_aggregation.py` — 删相关覆盖

**Runtime prompt 模板（wake 注入）**:
- 删 `<HANDOFF_NOTES>...</HANDOFF_NOTES>` 块构造代码
- 删 `<HISTORICAL_SUMMARY>...</HISTORICAL_SUMMARY>` 块构造代码
- 保留 `<PREV_SCOPE_TAIL>` 块（唯一活的跨 scope 续写）

**风险**：
- 极低。两个块此前始终为空，从未生效过。
- 唯一需要注意：`<PREV_SCOPE_TAIL>` 变成唯一续写机制，它的健康就是整个续写机制的健康。PR-54 的 `wake_continuity_render_total{layer=text,result=...}` 指标需要砍掉 `text` 层的两个子块维度。

**验证**：
- `grep 'extra_dropped' /opt/novaic/data/logs/business-*.log` — 继续零条
- `grep 'continuity_resolve' /opt/novaic/data/logs/business-*.log` — `has_prev=1` 路径正常
- prompt 差分：wake 的 system message 里不再出现这两个 XML 块
- 不是「agent 忘记上下文」的 regression —— 这两个块本来就是空的，删除只是不再画空框

### F4 — 文档扫雷

**必改**：
- `docs/architecture/message-wake-principles.md` — 删「LLM 调 `subagent_rest`」章节；R-ALLOWLIST 不变量保留但从示例里移除 `historical_summary` / `handoff_notes`，改用一个仍在用的列
- `docs/roadmap/message-wake-refactor.md` — 滚动条目标记 PR-42/PR-45/PR-49 为 **superseded-by-PR-55**；R9 文字层说明只剩 `<PREV_SCOPE_TAIL>`
- `docs/cortex/scope-lifecycle.md` / `docs/cortex/session-meta-json.md` / `docs/cortex/internal-api-schemas.md` — 删 `handoff_notes` / `historical_summary` 字段

**加 postscript（不改原文）**：
- `docs/roadmap/tickets/PR-42-wake-continuity-inject-handoff.md` — 末尾加 `## 2026-04-23 postscript (PR-55)：本票两个注入块均为 dead code，已由 PR-55 删除`
- `docs/roadmap/tickets/PR-45-wake-continuity-text-producer-wiring.md` — 同上
- `docs/roadmap/tickets/PR-49-subagent-rest-executor.md` — 同上，且注明 `_exec_subagent_rest` 已删
- `docs/roadmap/tickets/PR-53-entangled-continuity-allowlist.md` — 末尾加「F1 allowlist 对 `historical_summary` 的扩展已由 PR-55 回收，因为列本身被删」
- `docs/roadmap/tickets/reviews/PR-45-review.md` — postscript

### F5 — 指标 / 探针收尾

- `wake_continuity_render_total{layer=text,...}` 的 `text` 层含义从「3 个子块」收窄为「1 个子块（`<PREV_SCOPE_TAIL>` 的文字注入部分）」。标签值保留 `ok|empty|truncated|error`。
- `ghost_scope_rate`：不变，本票不碰。

## 为什么不等 LLM 写根 scope report 再删

有人会说：「先加一个 root-scope report 机制再删旧的，不然续写机制更薄了。」

反驳：

1. 现在 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` **已经是空的**，维持它们不变 = 假装有续写，实际 nothing。删除只是消除认知幻觉，不削弱能力。
2. 加一个 root-scope LLM-authored report 是**设计问题**：root scope 没有自然的 "结束时机" LLM 触发点（rest 是系统触发的）。可能的方案（新工具 / 在 chat_reply 附带 summary / 定时快照）各有权衡，不该被这次清理捆绑。
3. 本票 merge 后，续写机制只剩一条 `<PREV_SCOPE_TAIL>`，下一步设计空间干净。

## 验证步骤

### 本地
- [x] `rg -n 'historical_summary|handoff_notes' --type py` 仅剩测试/历史证明用途，活 schema/API 不暴露这两个字段。
- [x] `rg -n '"subagent_rest"' novaic-agent-runtime novaic-common` 不再匹配 LLM 工具或 active executor；remaining references are historical docs or renamed wake-finalize lifecycle archaeology.
- [x] `Entangled && pytest` 全绿：later cleanup batches verified Entangled/App schema guardrails.
- [x] `novaic-business && pytest` 全绿：2026-05-01 cleanup batch recorded 90 Business tests passed.
- [x] `novaic-agent-runtime && pytest` 全绿：2026-05-01 cleanup batch recorded 19 Runtime tests passed, with prior PR-113/114 full Runtime suites green.
- [x] prompt 快照测试：wake system message 不再出现 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` 标签； PR-85 and PR-144 guardrails cover current prompt/context.

### Prod 部署后
- [x] 发一条消息，让 agent finalize 一次：later smoke requests confirmed wake scope closes through `skill_end` / `wake_finalize`.
- [x] `last_scope_id` preservation was superseded by the agent-root scope model; current continuity no longer depends on previous-scope tail injection.
- [x] 下一次 wake 的 Business 日志不再需要 `continuity_resolve` handoff/summary text path; PR-70/113 retired Runtime-derived wake memory.
- [x] `tail -f` runtime log 不再出现 `[session.generate_summary]` 打印; PR-113/114 and Runtime guardrails removed old summary/replay handlers.
- [x] 二次 wake：current LLM context uses agent-root DFS and folded summaries; `<PREV_SCOPE_TAIL>` / handoff XML blocks are retired from the main path.

## 回滚

- F1 / F2 / F4 / F5：纯加性删除，revert = 把代码 / 文档搬回
- F3 列删除：如走「宽容路线」（保留列定义只删读写路径），revert 简单。如走「物理 DROP COLUMN」，revert 需要 ALTER TABLE ADD COLUMN + data backfill（全 NULL），代价低但不是零。**建议走宽容路线，6 个月后另 PR 物理删**。

## 关单 checklist

- [x] F1 `_exec_subagent_rest` + 单测删除
- [x] F2 `generate_simple_summary` saga step + handler + util 删除
- [x] F3 两个 column 写入 / 读出路径删除（宽容路线保留 schema 定义）
- [x] F3 Entangled `EXTRA_ALLOWLIST` 回收 `historical_summary`
- [x] F3 Business `_resolve_continuity` 删两个字段；`_subagent_to_dict` 删两个响应键
- [x] F3 Runtime wake prompt 模板删两个 XML 块构造（`_build_wake_continuity_messages` / `_fetch_historical_summary` / `_build_continuity_block_for_wake` / `_cap_continuity_text` / `_continuity_kind_label` 整组函数）
- [x] F3 bonus: `novaic-common/common/tools/definitions.py::RUNTIME_TOOLS` 里的 `subagent_rest` 工具定义整体删除（根因：本 ticket 误导链的源头）
- [x] F3 bonus: `novaic-agent-runtime/task_queue/client.py::get_agent_state` 不再 surface `handoff_notes`
- [x] F3d 测试：`test_pr45_continuity_wiring.py` / `test_pr45_dispatch_continuity.py` / `test_pr53_continuity_allowlist_e2e.py` 整文件删除；`test_pr54_render_metric.py` 改 `layer ∈ {state, im}`；`test_pr43_previous_scope_transport.py` / `test_pr43_last_scope_wiring.py` / `test_scheduler_dispatch.py` / `test_im_aggregation.py` / `test_subagent_state.py` 改为 "retired-key-is-dropped" 负断言；`test_pr43_prev_scope_tail_inject.py` 清理 fixture 的 `HANDOFF_NOTES` 引用
- [x] F4 `docs/architecture/message-wake-principles.md` — R9 条目收窄为 state+IM 两层；R-ZOMBIE 不变量入库
- [x] F4 `docs/roadmap/message-wake-refactor.md` — P6-2 / P6-5 / P6-8 标记 `[superseded-by-PR-55]`；P6-15 status 翻 `[x]`
- [x] F4 cortex docs — `scope-lifecycle.md` / `session-meta-json.md` / `internal-api-schemas.md` 加 PR-55 注
- [x] F4 旧 ticket postscript — PR-42 / PR-45 / PR-49 / PR-53 / PR-45-review 各 append 2026-04-23 postscript
- [x] F4 `docs/runbooks/pr41-pr42-staging-verification.md` — 加 PR-55 obsolete 警告
- [x] F4 `docs/architecture/gateway-v2-target-architecture.md` — 头部加 PR-55 修订说明（§0.4 第一层作废）
- [x] F4 `scripts/ci/lint_wake_continuity_contract.sh` 改写为 R-ZOMBIE retirement-trail guard（保留其他合法 allowlist 文件）
- [x] F5 `wake_continuity_render_total` `text` 层语义收窄（文档：principles §六、roadmap §P6-15；代码：`emit_wake_continuity_render` docstring + `test_render_metric_active_layer_taxonomy_is_state_and_im`）
- [x] 本地全量 pytest 绿（Entangled / business / runtime）由后续 cleanup batches 覆盖：Business 90 tests, Runtime 19 tests, Entangled/App guardrails passed in 2026-05-01 closure.
- [x] `scripts/deploy-business.sh` + runtime 部署由后续 service deploys 覆盖。
- [x] prod smoke：rest/wake path was superseded by wake-scope close + wake_finalize; logs and guardrails confirm no active `session.generate_summary` or handoff/summary text path remains.
- [x] `docs/roadmap/message-wake-refactor.md` P6-15 更新为 PR-55 完成

## 参考

- `novaic-cortex/novaic_cortex/tool_schemas.py::BUILTIN_TOOL_SCHEMAS` — 权威 LLM 工具清单，不含 `subagent_rest`
- `novaic-agent-runtime/task_queue/sagas/react_actions.py` — rest 的真实系统触发逻辑
- PR-42 / PR-45 / PR-49 / PR-53 ticket — 被本票 supersede 的前序投资
- PR-54 ticket — `wake_continuity_render_total` 指标来源，F5 需要同步文档
