# PR-43  Scope 续链（`previous_scope_id`）—— wake 后能回溯上一次 scope 的尾部上下文

| 字段 | 值 |
| --- | --- |
| **Phase** | R9 加强版（wake continuity 的"完整形态"） |
| **Milestone** | — |
| **承诺** | R9（见 PR-42）+ R4（context 可追溯） |
| **Status** | `[closed — implemented, then retired from main path by PR-69]` |
| **Depends on** | PR-20（scope meta inputs）、PR-29（scope 状态机）、PR-39（context assembly DFS） |
| **Blocks** | — |
| **估时** | 2–3 d（含 Cortex engine 配合） |
| **Owner** | __（需 cortex 线 + runtime 线协同） |
| **PR 标题** | `feat(cortex+runtime): scope chaining — new scope records previous_scope_id and context assembly back-references last N steps` |

## 2026-05-01 Ledger Closure

This ticket is no longer open. Its Wave A-D implementation landed, but the later agent-root scope design made `previous_scope_id` / `<PREV_SCOPE_TAIL>` a historical transition path rather than the current LLM context mechanism. Current continuity is agent-root DFS plus folded scope summaries; PR-69 retired `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` from the main LLM path.

Keep this document as archaeology for why the intermediate previous-scope chain existed. Do not use it as a current implementation plan.

## 事件摘要 & 前情

PR-42 已把 `handoff_notes` / `historical_summary` 这种"agent 自描述文字"注入新 scope，解决了"agent 记得自己睡前想说什么"。**本 PR 解决的是另一层**：agent 醒来后，能读到上一次 scope 里的**具体工具调用 / 代码改动 / LLM 推理轨迹**这些非摘要信息。

### 现状的局限

**每次 wake 都是一个全新的 Cortex scope**：
- `SessionRepository.dispatch` line 109 / 268 / 390: `scope_id = str(uuid.uuid4())`
- 新 scope 的 `context.jsonl` 初始只有：system prompt、recall（全局归档 root scope 的粗摘要）、handoff（PR-42 之后）
- 上一次 scope 的 `context.jsonl` / `steps/*.jsonl`（工具调用、tool output、代码 diff 等）**完全不可见**

### 这造成什么

假设 agent 在 scope X 里调用了 `grep / read / edit` 十几次，正一步步排查 bug，`subagent_rest(handoff_notes="继续排查 foo.py 里的 NullPointer")` 入睡。醒来新 scope Y：
- 知道"在排查 foo.py 的 NullPointer"（handoff_notes）
- 不知道之前 `grep` 查到的调用点、`read` 过哪几段代码、已经排除的假设

→ 被迫重复执行工具，浪费 token、绕弯路。

## 方案

**引入 scope 间的 `previous_scope_id` 链**。不打破"每个 wake 一个 scope"的 Cortex 语义，而是让 Cortex 的 **context assembly** 在读取时沿链往回看一跳（可配置）。

### 数据流

```txt
                 wake (SCHEDULED_WAKE / RECOVERED / USER_MESSAGE after sleep)
                           ↓
   SessionRepository.dispatch
     - 新 scope_id = uuid4()   ← 保持
     - 查 subagents.last_scope_id → 如果非空，塞进 metadata["previous_scope_id"]
                           ↓
   saga_context (含 previous_scope_id)
                           ↓
   subagent_wake._build_session_init_payload  (透传 previous_scope_id)
                           ↓
   handle_session_init
     - bridge.create_scope(scope_id=Y, previous_scope_id=X)  ← 写进 meta.json
                           ↓
   后续 react_think 的 context.read
     - Cortex engine 读 Y 的 context.jsonl
     - 如果 Y.meta.previous_scope_id = X 且预算允许
         → 读 X 的 last K steps（tool call + tool result）
         → 以 system role 前置注入（标记 _message_type=PREV_SCOPE_TAIL）
```

### 关键子改动

#### 1. 记录"上一次 scope"（runtime 侧）

`subagent_rest` saga 的 `cortex_scope_end` 完成后，写入：

```python
business_client.update_subagent(agent_id, subagent_id, {
    "last_scope_id": scope_id,  # 刚 archive 的 root scope
    "last_scope_archived_at": now_iso(),
})
```

- 新增 `subagents.last_scope_id` / `last_scope_archived_at` 字段（Entangled schema + Business PATCH）
- `set_subagent_sleeping` / `set_subagent_completed` 之前做，保证原子

#### 2. Dispatch 带 previous_scope_id（queue-service 侧）

`SessionRepository.dispatch`：

```python
# Step 2 新 scope 之前，从 metadata 或现场查
previous_scope_id = metadata.get("previous_scope_id")
if not previous_scope_id and trigger_type in PREV_SCOPE_ELIGIBLE_TRIGGERS:
    # 由上游 Assembler 已经 resolve 好塞进 metadata；这里仅做防御
    # 如果没塞，short-circuit 不拉 Business（避免 dispatch 路径引入新依赖）
    pass
saga_context = {
    ...
    "previous_scope_id": previous_scope_id,
}
```

**Assembler 侧（`common/wake/assembler.py`）** 是 previous_scope_id 的源头：
- `assemble_and_dispatch_sync(trigger, agent_id, ...)` 时，对"续接类 trigger"（SCHEDULED_WAKE / RECOVERED / USER_MESSAGE / SUBAGENT_SEND）**主动** resolve 一次 subagent 的 `last_scope_id`（走 AgentOwnershipResolver 同款 TTL 缓存）
- `SPAWN_SUBAGENT` 不 resolve（新生 subagent 无前序）

这把"要不要续链"的判断收敛到一个入口（Assembler），避免每个 dispatch caller 自己操心。

#### 3. Scope meta 记录（cortex 侧）

`POST /v1/scope` / `bridge.create_scope` 接受新参数 `previous_scope_id`，写入 `meta.json`：

```json
{
  "scope_id": "Y",
  "previous_scope_id": "X",
  "phase": "executing",
  "input_message_ids": [...],
  ...
}
```

无 previous_scope_id 也 OK（冷启动 / 首次 spawn）。

#### 4. Context assembly 读取（cortex engine）

`novaic-cortex/novaic_cortex/context_stack/engine.py` 的 assembly 路径：

```python
def assemble_context(scope_id, budget_tokens):
    # 现状：读当前 scope 的 context.jsonl + DFS 展开子 scope（PR-39）
    ...
    # 新增：如果 meta.previous_scope_id 存在且预算剩余 > PREV_SCOPE_MIN_BUDGET
    if meta.previous_scope_id and remaining_budget > PREV_SCOPE_MIN_BUDGET:
        prev_tail = read_scope_tail(
            meta.previous_scope_id,
            max_steps=PREV_SCOPE_MAX_STEPS,     # 默认 20
            max_tokens=min(remaining_budget, PREV_SCOPE_MAX_TOKENS),  # 默认 8k
        )
        prev_tail_messages = render_as_system_messages(prev_tail,
            wrapper="<PREV_SCOPE_TAIL scope={scope_id} from={archived_at}>")
        context = prev_tail_messages + context  # 放在最前（system prompt 之后）
    return context
```

`read_scope_tail` 仅读尾部 K 步，不递归 DFS（避免组合爆炸）。如果 prev scope 也有 `previous_scope_id`，**不继续往上链**（单跳，避免雪崩；多跳用 recall_messages 兜底）。

### 5. 不做的事

- **不**改 recall_messages 的语义（跨 session 长期记忆仍走 archived summary 路径）
- **不**把前序 scope 的 `context.jsonl` 物理复制到新 scope（重复存储 + 删除策略复杂）
- **不**支持多跳链式回溯（K=1 跳；更深的历史由 recall 兜底）
- **不**动 `SessionRepository.dispatch` 的 `scope_id = uuid4()` 主语义

## 范围

### runtime 侧
- `common/wake/assembler.py`（resolve last_scope_id）
- `novaic-agent-runtime/queue_service/session_repo.py`（透传 previous_scope_id 到 saga_context）
- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py::_build_session_init_payload`
- `novaic-agent-runtime/task_queue/sagas/subagent_rest.py`（`cortex_scope_end` 成功后写 `last_scope_id`）
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py::handle_session_init`（传 `previous_scope_id` 给 `bridge.create_scope`）

### business 侧
- `novaic-business/business/schema_push.py`：`subagents` 加 `last_scope_id` / `last_scope_archived_at`
- `novaic-business/business/internal/agents/subagent.py`：PATCH 接受新字段；`AgentOwnershipResolver` 或新 `last_scope_resolver` 暴露 GET

### cortex 侧
- `novaic-cortex/novaic_cortex/api.py`：`create_scope` 接受 `previous_scope_id`
- `novaic-cortex/novaic_cortex/workspace.py`：写进 `meta.json`
- `novaic-cortex/novaic_cortex/context_stack/engine.py`：assembly 插入 prev_scope_tail 读取
- `novaic-cortex/novaic_cortex/scope.py`：`read_scope_tail(scope_path, max_steps, max_tokens)` helper

## 前置 Checklist

- [x] PR-20 scope meta.input_message_ids 已生效
- [x] PR-29 Scope 状态机已稳定（archive 动作可被 hook）
- [x] PR-39 context assembly DFS 已生效（engine.py 已有组装主循环）
- [x] PR-42 已先行（confirm R9 承诺文档已落）
- [x] 与 cortex 线对齐 assembly 插入点、tail 读取 API 的签名

## 实施 Checklist

### A. 写入侧 —— 记录 last_scope_id  *(landed 2026-04-24)*

- [x] Entangled schema: `subagents` 加 `last_scope_id TEXT NULL`, `last_scope_archived_at TEXT NULL`（`novaic-business/business/schema_push.py::SUBAGENTS_DEF`；schema_push 自动 migration）
- [x] Business PATCH endpoint 白名单新增字段 —— **无需改**。确认：`PATCH /internal/entities/{entity}/{id}` 走 `Entangled/packages/server-python/entangled/app/crud.py::update_entity` → `store.update`，字段白名单直接来源于 `SqlEntityDef.fields`，schema 加字段即开放 PATCH。
- [x] `subagent_rest` saga：**采用"piggyback on terminal step"模式**（与 PR-45 A 同策略 / 一次原子写）：
  - `_build_set_sleeping_payload` / `_build_set_subagent_completed_payload` 调用新增 helper `_last_scope_fields(ctx)`
  - helper 的守卫：仅当 `step_results["cortex_scope_end"]` 存在且 `success != False`，且 `ctx.scope_id` 非空，才返回 `{last_scope_id, last_scope_archived_at}`
  - `handle_subagent_set_sleeping` / `handle_subagent_set_completed` 以 additive 语义 append 两字段到 `entity_update`（非 str / 空值 silent drop，绝不覆写已有值）
  - 决策 note：ticket 原稿写的是"cortex_scope_end 后独立一步 `update_subagent`"。落地时改为复用 terminal step 的 `entity_update` 同一次调用，避免"两次写可能部分失败"的 skew，同时承接 PR-45 A 的 `historical_summary` piggyback 模式，代码面扩散最小。
- [x] 单测：`novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py` — 19 个用例覆盖 `_last_scope_fields` 守卫（5）、saga payload builder（4）、handler writeback（10，含 5 组 `pytest.parametrize` malformed-value 防御）

### B. Producer / Transport —— previous_scope_id 落到 dispatch metadata  *(landed 2026-04-25)*

落地决策：**不**引入独立的 `LastScopeResolver` / 新 GET endpoint。复用各 wake caller 已有的 `subagents` entity 读取路径，一处 resolve、统一在 metadata 边界把 `last_scope_id` 重命名为 `previous_scope_id`。

- [x] `DispatchSubscriber._resolve_continuity`（`novaic-business`）：`entity_get(subagents, ...)` 同一次调用里多返一个 `last_scope_id` 字段；`_deliver_one_inner` + 聚合分支均把该字段映射进 `metadata["previous_scope_id"]`（不覆盖上游 metadata）
- [x] `HealthWorker._resolve_continuity`（`novaic-agent-runtime`）：同款改造，`_maybe_recover` 里在已有 handoff/historical 注入之后补 `previous_scope_id`
- [x] `SchedulerWorker._wake_metadata`（`novaic-agent-runtime`）：`agent_info` 从 `/internal/subagents/due-wake` 拿到 `last_scope_id` → metadata
- [x] Business `/internal/subagents/due-wake`（`novaic-business`）：返回体里把 `last_scope_id` 和 `historical_summary` 一并 expose（避免 scheduler 多一次 GET）
- [x] 空值语义：`last_scope_id` 为 None / 空串 → 整个 `previous_scope_id` 键从 metadata 省略（不塞 sentinel，Wave C 靠 key 缺失判冷启动）
- [x] `SPAWN_SUBAGENT`：以上三个 caller 都不经手子 agent spawn，自然不带 previous_scope_id；不需要额外 gate
- [x] 单测：`novaic-business/tests/test_pr45_dispatch_continuity.py` 新增 5 用例 / `novaic-agent-runtime/tests/test_pr43_previous_scope_transport.py` 新增 11 用例覆盖 resolve → metadata 映射、upstream override 保护、falsy drop

### C. Dispatch 透传 & session.init  *(landed 2026-04-25)*

- [x] `SessionRepository.dispatch`：`saga_context` 本身就是 `**metadata` spread —— 零代码确认 previous_scope_id 会直接出现在 saga ctx
- [x] `_build_session_init_payload`（`subagent_wake.py`）：仅当 `ctx["previous_scope_id"]` truthy 才写入 payload（落袋测试 + falsy parametrize）
- [x] `handle_session_init`（`runtime_handlers.py`）：`payload.get("previous_scope_id") or None` 读出后，立即作为 kwarg 传给 `bridge.create_scope`
- [x] `CortexBridge.create_scope`：新增 `previous_scope_id` kwarg；conditionally 写进 `/v1/scope/create` payload（送 None 也合法，送"缺席"是最干净的 canary 信号，所以选后者）+ 日志行加 `prev=<id|->`

### D. Cortex — 写 meta  *(landed 2026-04-25)*

- [x] `POST /v1/scope/create` 的 `ScopeCreateRequest` 新增 `previous_scope_id: str | None = None`（`_TenantMixin` 的 `extra='forbid'` 下必须显式声明，否则 422）
- [x] `Workspace.create_scope` 形参新增 `previous_scope_id`；**仅 root scope**（`parent_path is None`）才写进 `meta.json`，子 scope 即便带该参数也 silent drop（续链颗粒度在 root 级）
- [x] 单测（`novaic-cortex/tests/test_pr43_previous_scope_meta.py`）：root 写入、root 无参不写 sentinel、子 scope 忽略、Pydantic model 接受新字段 —— 4/4 通过

### E. Cortex — 读取 Tail  *(landed 2026-04-25)*

- [x] `Workspace.read_scope_tail(previous_scope_id, *, max_steps=20, max_tokens=8000, token_counter=None)`：
  - [x] 读 `/ro/scopes/{previous_scope_id}/context.jsonl` 作为原始 messages
  - [x] 读 `meta.json` 补 `archived_at`（来源优先级：`ended_at` > `archived_at` > `start_time`）
  - [x] 先按 `max_steps` 截断尾部，然后 `max_tokens` front-drop 直到 ≤ 预算；单条消息超预算时保留整条（不切开避免破坏 tool_call 链）
  - [x] soft-fail：read 异常 / 目录不存在 → `meta.found=False` + 空 messages，**不**抛异常污染 wake 关键路径
- [x] `POST /v1/scope/read_tail` 新路由 + `ScopeTailRequest` pydantic model（`previous_scope_id` + 两个 budget cap，`_TenantMixin` 继承 `extra='forbid'`）
- [x] 单测（`novaic-cortex/tests/test_pr43_read_scope_tail.py` — 7 用例）：happy path / missing archive soft-fail / max_steps 后截 / max_tokens front-drop / 单条超额保留 / `archived_at` 回填 / 请求 model 校验 —— 全通过

### F. Runtime — 注入 `<PREV_SCOPE_TAIL>`  *(landed 2026-04-25)*

- [x] `CortexBridge.read_scope_tail(previous_scope_id, *, max_steps, max_tokens)`：soft-fail 返回"空 found=False"结构；透明包装 `/v1/scope/read_tail`
- [x] `handle_session_init`（在 `_build_continuity_block_for_wake` 之后）调 `_build_prev_scope_tail_messages`，结果追加到 `initial_context`
- [x] 渲染策略（`_render_prev_tail_message`）：
  - [x] `[USER]` / `[AGENT]` 前缀；`tool` / `system` 角色丢弃（避免孤儿 tool_call_id + 双注入 continuity）
  - [x] assistant-only-tool_call 消息渲染为 `(tool_call: name1, name2)` 占位
  - [x] 多模态 content（list of parts）拍平到 text-only
  - [x] 单条 > 600 字符截断 + `…[truncated]` 标记
- [x] Block 外层格式：`<PREV_SCOPE_TAIL scope_id="X" truncated="0|1" archived_at="TS">\n[USER] ... \n[AGENT] ...\n</PREV_SCOPE_TAIL>`，`_message_type="WAKE_CONTINUITY"`（跟 PR-42 同一家族，便于统一 budget 裁剪）
- [x] 排序决策：注入点在 `HANDOFF_NOTES` / `HISTORICAL_SUMMARY` **之后** —— 把"系统 / agent 书写的摘要"放前，把"实证 transcript"放后，对齐给人做 briefing 的习惯
- [x] 单测（`novaic-agent-runtime/tests/test_pr43_prev_scope_tail_inject.py` — 17 用例）：happy path、truncated 旗标、冷启动跳过、spawn_subagent 门禁、kill-switch 短路、bridge 异常 soft-fail、非渲染消息空 block 不发、env cap 生效、bridge kwargs 透传、消息渲染细节 —— 全通过

### G. 配置 & 上限  *(landed 2026-04-25)*

- [x] env：`WAKE_PREV_SCOPE_TAIL_ENABLED=1`（默认开；`=0` 瞬时关闭注入）
- [x] env：`WAKE_PREV_SCOPE_TAIL_MAX_STEPS=20` / `WAKE_PREV_SCOPE_TAIL_MAX_TOKENS=6000`（默认值比 Cortex 侧 8k 更紧，因为 runtime 叠加了 handoff+historical 已用约 16KB）
- [x] env 变量统一经 `_prev_scope_tail_caps()` 读取，malformed 回退默认，永不炸 handler
- [x] soft-fail：Cortex 端不存在的 `previous_scope_id` → `meta.found=False` → runtime 直接不注入 block（wake 继续走 PR-42 text-layer）

## 测试 Checklist

- [x] 单测（runtime）—— producer/transport（Wave B）：4 × session_init payload + 5 × DispatchSubscriber resolve + 2 × HealthWorker resolve + mocked scheduler `_wake_metadata`（`tests/test_pr43_previous_scope_transport.py` × 11）
- [x] 单测（runtime）—— session.init 渲染（Wave F）：17 用例（`tests/test_pr43_prev_scope_tail_inject.py`）覆盖门禁、kill-switch、soft-fail、cap 透传、消息渲染
- [x] 单测（cortex）—— `read_scope_tail`（Wave E）：7 用例（`tests/test_pr43_read_scope_tail.py`）覆盖 happy / missing / max_steps / max_tokens / 单条超额 / `archived_at` / 请求模型
- [x] 单测（cortex）—— `meta.previous_scope_id` 写入（Wave D）：4 用例（`tests/test_pr43_previous_scope_meta.py`）
- [x] 单测（business）—— continuity resolve 扩展（Wave B）：`tests/test_pr45_dispatch_continuity.py` 17 用例全绿（其中 5 条新增 PR-43 Wave B 断言）
- [x] 集成端到端（closed by later architecture): PR-43's previous-scope tail smoke is archived because PR-69 retired this path from the main LLM context.
  - [x] agent 在 scope X 调用 `read_file / edit_file` 若干次 → `subagent_rest(rest_duration_minutes=1)` — historical scenario only.
  - [x] 等 SchedulerWorker 唤醒 — historical scenario only.
  - [x] 新 scope Y `meta.json` 含 `previous_scope_id=X` — historical scenario only.
  - [x] 首轮 think 的 LLM input 里能看到 X 末尾 K 步的 `<PREV_SCOPE_TAIL>` block — retired by PR-69.
  - [x] agent 行为验证：连续对话不复读同样的 grep（人工 sanity check）— superseded by agent-root DFS smoke.
- [x] 回归：`SPAWN_SUBAGENT` 触发类型在渲染层直接门禁挡掉（test_prev_scope_tail_spawn_subagent_trigger_skips_injection）
- [x] 回归：Cortex 读不到 prev archive → soft-fail 空 block；runtime 端 bridge 异常也 soft-fail（test_prev_scope_tail_bridge_exception_soft_fails + test_read_scope_tail_missing_archive_soft_fails）

## 可观测性 Checklist

- [x] metric `wake_prev_scope_tail_total{result=injected|empty|error}` counter（runtime）
- [x] log (cortex_bridge): `[CortexBridge] scope.created scope_id=Y path=... prev=X`（已含）
- [x] log (runtime session.init): `event=prev_scope_tail_injected prev=X steps=K/total truncated=0|1`
- [x] log (runtime session.init soft-fail): `event=prev_scope_tail_read_failed prev=X err=<ExcType>`
- [x] log (cortex): `[Workspace] read_scope_tail read_context failed prev=X exc=<ExcType>`（miss 时 warn）
- [x] histogram `prev_scope_tail_steps` / `prev_scope_tail_tokens` —— no longer needed; PR-69 retired the previous-tail path, current guardrails focus on agent-root DFS and folded summaries.

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) 的 R9 小节补完整形态描述 — superseded by agent-root scope docs and PR-69 retirement.
- [x] [docs/architecture/message-wake-principles.md](../../architecture/message-wake-principles.md) R9 对照表加"previous_scope_id" / "scope chain" 条目 — not added because the path is retired; this ticket itself remains the archaeology record.
- [x] [docs/cortex/context-timeline-and-dfs.md](../../cortex/context-timeline-and-dfs.md) 加"跨 scope 续链"小节 — not added to current docs because the path is retired.
- [x] [docs/cortex/session-meta-json.md](../../cortex/session-meta-json.md) meta 字段表加 `previous_scope_id` — not added to current docs because the field is no longer a current contract.
- [x] [docs/cortex/budget-compact-algorithm.md](../../cortex/budget-compact-algorithm.md) 加"PREV_SCOPE_TAIL 的预算优先级" discussion — not added because `<PREV_SCOPE_TAIL>` is no longer in the main path.
- [x] runbook：如何用 `previous_scope_id` 串起一次 debugging session — not created because this is not an operator path now.

## 验收命令

```bash
# 1) 端到端：制造 archive + wake
# 让 agent 在 scope X 跑几个 tool call 然后 rest(1min)
sleep 70

# 2) 查新 scope 的 meta
curl -s .../cortex/v1/scope/$NEW_SCOPE/meta | jq '.previous_scope_id, .input_message_ids'

# 3) 查 context 组装结果
curl -s .../cortex/v1/scope/$NEW_SCOPE/context?round=1 | jq '.messages[] | select(._message_type=="PREV_SCOPE_TAIL")' | head -20

# 4) 查 metric
curl -s .../metrics | rg 'prev_scope_tail'
```

### Prod deploy record  *(2026-04-22 21:33 CST)*

- **Deploy command**: `bash scripts/deploy-business.sh root@api.gradievo.com`（incremental，7 个 submodule + scripts/canary）
- **Schema migration**: `sqlite3 /opt/novaic/data/entangled.db ".schema subagents"` 确认 `last_scope_id TEXT, last_scope_archived_at TEXT` 两列均已落位（schema_push 自动加列，nullable → 无需数据迁移）
- **Cortex 新路由**: `/v1/scope/read_tail` 已出现在 `openapi.json` paths；手动 curl `previous_scope_id=nonexistent` 返回 `{"messages":[],"meta":{"found":false,...}}`（soft-fail 符合契约）
- **服务健康**: business / cortex / queue / device / entangled / gateway 全部 `/health` 绿；subscriber 正常 claim outbox；当日日志 `Traceback|ERROR` 零命中
- **功能入池**: 还需等待下一次 `subagent_rest` → `cortex_scope_end` 成功写入 `last_scope_id`，再下一次该 subagent 的 user_message / scheduled_wake 才会让 `<PREV_SCOPE_TAIL>` 首次注入；观察指标 `wake_prev_scope_tail_total{result=injected}` 预期 24h 内从 0 抬起

## 回滚

- Entangled schema 新字段保留（nullable，无副作用）
- Cortex assembly 增量功能由 env `WAKE_CONTINUITY_PREV_SCOPE=0` 瞬时关停
- 完整回滚：revert commit；已有的 `subagents.last_scope_id` 数据保留（下次开启即可用）

## 风险 / 讨论

1. **预算打穿**：prev scope 尾部步骤可能很长（一次大 edit 产出 20k token）。mitigation：`PREV_SCOPE_MAX_TOKENS` 硬上限 + `budget_priority` 是 compact 的首批驱逐对象。
2. **隐私 / 噪音**：prev scope 可能包含大量工具噪音（`grep` 结果一屏）。Mitigation：`read_scope_tail` 做智能过滤（只保留"有结果 / 有 diff / 有错误"的 step，丢掉空结果）。
3. **单跳 vs 多跳**：本 PR 只做单跳（Y → X）。多跳 chain 的复杂度（X → W → V）不值得，长时记忆由 recall 兜底。
4. **与 PR-42 的关系**：PR-42（handoff 文字）+ 本 PR（scope 尾部实体） = R9 完整形态。可以独立上线，互不依赖。建议：PR-42 先上做止损，PR-43 作为下一波。
5. **Scope 归档延迟**：`cortex_scope_end` 成功之前 agent 再次 wake（罕见），此时 last_scope_id 尚未写。降级策略：Assembler 查不到 last_scope_id → previous_scope_id = None，走 PR-42 的文字通道。

## 承诺登记

本 PR 把 **R9 — Wake Continuity** 从"文字承接"升级为"状态承接"，完整形态在 `docs/architecture/message-wake-principles.md` 中定义为：

> Sleeping → awake 转换点：
> 1. **文字层**（PR-42）：handoff_notes + historical_summary 注入新 scope
> 2. **状态层**（PR-43）：previous_scope_id 串链，新 scope 能访问上一次 scope 尾部 K 步
> 3. **全局层**（已有）：recall_messages 注入所有已归档 root scope 摘要

三层互补，可配合 budget compact 动态裁剪。

## 备注

- 本 PR 是"架构级"改动（Cortex engine），建议分两个 commit：
  - commit 1：runtime + business + entangled（写入 + 透传）—— 本身 noop（Cortex 收到参数但不消费）
  - commit 2：Cortex engine（消费 previous_scope_id + tail 读取）—— 打开开关
  - 这样 canary 能分步灰度。
- `read_scope_tail` 的实现可以参考 `scope.resolve_active_scope_path` 的逆向（它找 deepest open scope；我们要找 last N steps）。
- 未来可考虑把 `historical_summary` 的生成从 `subagent_rest` saga 移到"scope archive 后异步"，减少 rest 路径的关键路径时间。
