# PR-43  Scope 续链（`previous_scope_id`）—— wake 后能回溯上一次 scope 的尾部上下文

| 字段 | 值 |
| --- | --- |
| **Phase** | R9 加强版（wake continuity 的"完整形态"） |
| **Milestone** | — |
| **承诺** | R9（见 PR-42）+ R4（context 可追溯） |
| **Status** | `[Wave A ✓ (2026-04-24), Wave B/C 待开]` |
| **Depends on** | PR-20（scope meta inputs）、PR-29（scope 状态机）、PR-39（context assembly DFS） |
| **Blocks** | — |
| **估时** | 2–3 d（含 Cortex engine 配合） |
| **Owner** | __（需 cortex 线 + runtime 线协同） |
| **PR 标题** | `feat(cortex+runtime): scope chaining — new scope records previous_scope_id and context assembly back-references last N steps` |

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

- [ ] PR-20 scope meta.input_message_ids 已生效
- [ ] PR-29 Scope 状态机已稳定（archive 动作可被 hook）
- [ ] PR-39 context assembly DFS 已生效（engine.py 已有组装主循环）
- [ ] PR-42 已先行（confirm R9 承诺文档已落）
- [ ] 与 cortex 线对齐 assembly 插入点、tail 读取 API 的签名

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

### B. Assembler resolve previous_scope_id

- [ ] 在 `DispatchAssembler.assemble` 里，针对 `trigger_source in {SCHEDULED_WAKE, RECOVERED, USER_MESSAGE, SUBAGENT_SEND}` 且 subagent_id 已知时：
  - [ ] 查 `subagents.last_scope_id`（复用 `AgentOwnershipResolver` TTL 缓存模式，或新增 `LastScopeResolver`）
  - [ ] 注入 `metadata["previous_scope_id"]`
- [ ] `SPAWN_SUBAGENT` / 无 subagent_id 的路径不 resolve
- [ ] Business 新增 `GET /internal/agents/{agent_id}/subagents/{sub_id}/last_scope` → `{scope_id, archived_at}` / 404

### C. Dispatch 透传

- [ ] `SessionRepository.dispatch`：saga_context 含 `previous_scope_id`（已经是 `**metadata` spread，零代码改动确认）
- [ ] `_build_session_init_payload`：透传 `previous_scope_id` 到 payload

### D. session.init 传给 Cortex

- [ ] `handle_session_init`：`bridge.create_scope(scope_id=..., name=..., previous_scope_id=payload.get("previous_scope_id"))`
- [ ] 单测：payload 带 prev → create_scope 调用带参；不带 → None

### E. Cortex — 写 meta

- [ ] `create_scope` 路由接受 `previous_scope_id` 可选参
- [ ] `workspace.create_scope` 写进 `meta.json`
- [ ] 单测：meta.json 含 previous_scope_id
- [ ] 状态机（PR-29）：previous_scope_id 是 executing 阶段的 constant，不参与 transition

### F. Cortex — 读取插入

- [ ] `read_scope_tail(scope_path, *, max_steps, max_tokens)` 新 API
  - [ ] 逆序读 `steps/_index.jsonl` 最后 K 条
  - [ ] 按 step type（tool_call / llm_message / sub_scope_ref）渲染成 messages
  - [ ] 对 sub_scope_ref：仅渲染名字 + 摘要，不递归 DFS
  - [ ] 超 `max_tokens` 提前截断；token 估算复用现有 tokenizer helper
- [ ] `context_stack/engine.py` assembly 主循环：
  - [ ] 读当前 scope meta；若 previous_scope_id 存在 → 在组装完当前 + 子 scope DFS 之后，若 budget 还剩 > `PREV_SCOPE_MIN_BUDGET` → 调 `read_scope_tail`
  - [ ] 结果放在 system_prompt 之后、当前 scope context 之前
  - [ ] 每条消息加 `_message_type="PREV_SCOPE_TAIL"`、包装 `<PREV_SCOPE_TAIL scope=X from=TS>`

### G. 配置 & 上限

- [ ] env：`PREV_SCOPE_MAX_STEPS=20`, `PREV_SCOPE_MAX_TOKENS=8000`, `PREV_SCOPE_MIN_BUDGET=4000`
- [ ] 默认开启；可通过 `WAKE_CONTINUITY_PREV_SCOPE=0` 整体禁用做灰度
- [ ] 如果 prev scope 不存在（已物理删除）→ log WARN + 降级到 PR-42 的"只有 handoff"

## 测试 Checklist

- [ ] 单测（runtime）：Assembler 对 SCHEDULED_WAKE + 已有 last_scope_id → metadata 含 previous_scope_id
- [ ] 单测（cortex）：`read_scope_tail` 返回对的 step + 截断 + token 估算
- [ ] 单测（cortex）：assembly 主循环接受 previous_scope_id → 输出含 `<PREV_SCOPE_TAIL>` wrapper
- [ ] 集成端到端：
  - [ ] agent 在 scope X 调用 `read_file / edit_file` 若干次 → `subagent_rest(rest_duration_minutes=1)`
  - [ ] 等 SchedulerWorker 唤醒
  - [ ] 新 scope Y `meta.json` 含 `previous_scope_id=X`
  - [ ] 首轮 think 的 LLM input 里能看到 X 末尾 K 步的 tool call + tool result
  - [ ] agent 行为验证：连续对话不复读同样的 grep（人工 sanity check）
- [ ] 回归：`SPAWN_SUBAGENT` 新生子 agent → previous_scope_id 为 None，不触发 read_scope_tail
- [ ] 回归：prev scope 已物理删除（模拟）→ WARN log + 走降级路径

## 可观测性 Checklist

- [ ] metric `prev_scope_tail_injected_total{result=ok|missing|skipped_budget}` counter
- [ ] metric `prev_scope_tail_steps` histogram（实际注入了多少步）
- [ ] metric `prev_scope_tail_tokens` histogram
- [ ] log (session.init): `prev_scope linked=X archived_at=TS`
- [ ] log (cortex assembly): `prev_scope_tail steps=K tokens=T budget_left=B`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) 的 R9 小节补完整形态描述
- [ ] [docs/architecture/message-wake-principles.md](../../architecture/message-wake-principles.md) R9 对照表加"previous_scope_id" / "scope chain" 条目
- [ ] [docs/cortex/context-timeline-and-dfs.md](../../cortex/context-timeline-and-dfs.md) 加"跨 scope 续链"小节
- [ ] [docs/cortex/session-meta-json.md](../../cortex/session-meta-json.md) meta 字段表加 `previous_scope_id`
- [ ] [docs/cortex/budget-compact-algorithm.md](../../cortex/budget-compact-algorithm.md) 加"PREV_SCOPE_TAIL 的预算优先级" discussion
- [ ] runbook：如何用 `previous_scope_id` 串起一次 debugging session

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

