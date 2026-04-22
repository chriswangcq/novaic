# PR-45  Wake continuity 文字层"生产者-消费者"闭环（PR-42 amend）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（PR-42 端到端失效补洞） |
| **Milestone** | R9 文字层真·生效 |
| **承诺** | R9（wake 不丢上下文） + **R10 新增**（producer/consumer 契约显式登记） |
| **Status** | `[~]` — A/B/C/D/E landed; F (deploy + live verify) pending |
| **Depends on** | PR-42（消费者已就位） |
| **Blocks** | PR-43（scope chain 依赖文字层是可信的基线对比） |
| **估时** | 0.5d（MVP）+ 0.5d（`_exec_subagent_rest` 补全，Wave 1.5） |
| **Owner** | wangchaoqun |
| **PR 标题** | `fix(runtime+business): wake-continuity text layer end-to-end — close producer gap that silently dropped handoff/historical on user_message wakes` |

## 事件摘要

2026-04-22 用户报告"发消息了 dfs scope 还是没有加载"。排查后发现：

1. **PR-42 消费端在 prod 已部署**（`handle_session_init` + `_build_continuity_block_for_wake` + `subagent_wake.saga._build_session_init_payload` 都读 `ctx["handoff_notes"]`）。
2. **但生产端全空**：
   - `saga-ded55b05b388`（最新 user_message wake）的 saga context 只有 7 个字段：`agent_id, subagent_id, user_id, scope_id, trigger_type, model, message_ids`。**没有 `handoff_notes`，没有 `wake_reason`**。
   - `subagents.handoff_notes = NULL`、`subagents.historical_summary = NULL` for `main-415f6cfd`。
   - 诊断结论：PR-42 像"水龙头接好但总阀门没开"。

3. **进一步深挖**：
   - `subagent_rest` saga 有 `generate_simple_summary` step → `step_results.simple_summary`，但**从没写回 `subagents.historical_summary`**（只塞进 `cortex_scope_end.report` 和 `notify_parent.result`）。
   - `DispatchSubscriber`（user_message 主路径）→ `Assembler.assemble_and_dispatch_sync(metadata=payload.get("metadata") or {})` → `metadata` 仅承接 outbox `payload_json.metadata`，**没人查 subagent 行拿 handoff_notes/historical_summary**。
   - `SchedulerWorker._wake_metadata` 读了 `agent_info.handoff_notes`（唯一读者），但它只管 scheduled_wake。
   - `common/tools/definitions.py:494` 给 LLM 暴露 `subagent_rest(handoff_notes, rest_duration_minutes, wake_triggers)` 工具，**没有 `_exec_subagent_rest` executor**（`tool_handlers._EXECUTORS` 里没这一项）。LLM 调这个工具 → `Unknown tool` warning → handoff_notes 丢。

4. **表征**：每次醒来只有"空壳 system prompt + recall summary"，agent 失忆；PR-44 能补 chat_messages 回放但补不了"agent 自述 handoff + 系统压缩 historical_summary"这两路。

## 方案（MVP + 1.5 两刀）

### MVP（本 PR）— 自动可产出的两端，零依赖 agent 合作

把"系统自动产生"的东西先闭环，不等 agent 学会用 `subagent_rest(handoff_notes=...)`。

#### A. 生产者：`handle_subagent_set_sleeping` 落盘 historical_summary

`subagent_rest` saga 已经跑过 `generate_simple_summary`，`step_results.generate_simple_summary.simple_summary` 可取；之前只流向 `cortex_scope_end.report` / `notify_parent.result`，**没写回 `subagents.historical_summary`**。

在 `handle_subagent_set_sleeping` 中接收新 payload 字段 `historical_summary`（由 `_build_set_sleeping_payload` 从 `ctx.step_results` 取出），一起 `entity_update`：

```python
# subagent_rest.py
def _build_set_sleeping_payload(ctx):
    step_results = ctx.get("step_results", {})
    gen = step_results.get("generate_simple_summary", {}) or {}
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "historical_summary": gen.get("simple_summary") or None,
    }

# subagent_handlers.py::handle_subagent_set_sleeping
updates = {
    "status": "sleeping", "need_rest": 0,
    "_transition_reason": "rest",
    "_transition_actor": "runtime.subagent_handlers",
}
summary = payload.get("historical_summary")
if summary:
    updates["historical_summary"] = summary  # non-null only, additive not destructive
business_client.entity_update("subagents", ..., updates, ...)
```

**为什么不另开一步**：新开一个 saga step 要改 saga definition 文件 + 新增 topic + 新 handler，爆炸半径大。复用 `set_sleeping` 这步做"状态 + 续承 fields"一次性写盘，是"状态机终态伴随字段" pattern。

**为什么 additive**：`historical_summary` 非空即写，None 不覆盖已有值（允许 agent 或后台异步任务未来生成更长摘要时幂等更新）。

#### B. 消费者入口：`DispatchSubscriber._deliver_one_inner` 注入 metadata

user_message 主路径在 dispatch 前一次查 `subagents` 行，取出 `handoff_notes` + `historical_summary` 注入 metadata：

```python
# dispatch_subscriber.py::_deliver_one_inner — 在 assembler.assemble_sync 前
trigger = TriggerType.from_legacy(row["trigger_type"])
metadata = dict(payload.get("metadata") or {})
if trigger in _CONTINUITY_ELIGIBLE_TRIGGERS:
    continuity = self._resolve_continuity(
        agent_id=row["agent_id"], subagent_id=row.get("subagent_id"),
    )
    if continuity:
        metadata.setdefault("handoff_notes", continuity.get("handoff_notes"))
        metadata.setdefault("historical_summary", continuity.get("historical_summary"))
```

- `_CONTINUITY_ELIGIBLE_TRIGGERS = {USER_MESSAGE, SUBAGENT_SEND}`（SCHEDULED_WAKE 已由 scheduler 注入，保持不动；SPAWN_SUBAGENT 跳过）
- `_resolve_continuity`：复用 Business 内部 `store.get("subagents", ...)`。不做缓存（每个 outbox 行已经很便宜，相比 Cortex/Queue 的 HTTP 往返是鸡毛）。
- `setdefault` 不覆盖 upstream 已注入值（向前兼容 scheduler）。

#### C. HealthWorker（recovered 路径）同样的 2 行

`health_worker.py:_scan_unhandled_messages` 里调 `assembler.assemble_and_dispatch_sync`，同样加 metadata 注入（针对 `RECOVERED` trigger）。

#### D. 幂等消费：`handle_session_init` 消费后清 `handoff_notes`

`handoff_notes` 语义是"agent 给下一次 self 的指令"，**一次性消耗**。如果不清，agent 连续睡醒 3 次会在 3 个 scope 里看到同一条 note，产生"我好像在循环"的幻觉。

```python
# runtime_handlers.py::handle_session_init —— 在 _build_continuity_block_for_wake 成功返回后
if handoff_notes and trigger_type in WAKE_CONTINUITY_ENABLED_TRIGGERS:
    try:
        business_client.entity_update(
            "subagents", subagent_id,
            {"handoff_notes": None, "_transition_reason": "handoff_consumed",
             "_transition_actor": "runtime.session_init"},
            params={"agent_id": agent_id},
        )
    except Exception as e:
        logger.warning("[session.init] handoff clear soft-fail: %s", e)
```

`historical_summary` **不清**——它是累积摘要，跨 scope 一直叠加才有价值。

### Wave 1.5（同 PR 不同 commit，可独立）— `_exec_subagent_rest` 补全

让 LLM 真的能写 handoff_notes：

```python
# tool_handlers.py
def _exec_subagent_rest(args, deps):
    """Persist rest directive from agent. The actual sleep transition is
    owned by react_actions.decide_rest → subagent_rest saga; this tool
    only writes the *fields* (handoff_notes / wake_at / wake_triggers)
    onto the subagents row so rest saga reads them and downstream wakes
    surface them via PR-42+45 continuity block.
    """
    handoff_notes = args.get("handoff_notes")
    rest_minutes = args.get("rest_duration_minutes", 30)
    wake_triggers = args.get("wake_triggers")
    gw = deps["gateway_client"]
    agent_id = deps["agent_id"]
    subagent_id = deps["subagent_id"]
    updates = {"need_rest": 1}
    if handoff_notes is not None:
        updates["handoff_notes"] = handoff_notes
    if rest_minutes is not None:
        updates["rest_duration_minutes"] = rest_minutes
    if wake_triggers is not None:
        updates["wake_triggers"] = wake_triggers
    gw.entity_update("subagents", subagent_id, updates, params={"agent_id": agent_id})
    return {"ok": True, "handoff_persisted": bool(handoff_notes)}

_EXECUTORS["subagent_rest"] = _exec_subagent_rest
```

注：`need_rest=1` 是现有 react_actions 约定信号。`rest_duration_minutes` / `wake_triggers` 走 Business PATCH 通路，Business 侧 `subagent.py:342-361` 已经接受这些字段，zero 改动。

### 契约 CI 测试（PR-42 翻车根因的门禁）

新增 `scripts/ci/lint_wake_continuity_contract.sh`：
- 验证 `subagent_rest._build_set_sleeping_payload` 输出字段集合 ⊇ `handle_subagent_set_sleeping` 读的字段集合（生产者写什么消费者读什么一致）
- 验证 `_build_session_init_payload` 输出的 key 集合 ⊇ `handle_session_init`「处理的 payload 字段」集合
- 验证 `DispatchAssembler.metadata` 流向：dispatch_subscriber 放的 key → session_repo spread → \_build\_session\_init\_payload 读 → handle\_session\_init 读

MVP 版就做最后一条（`metadata` 流向 trace），一个 python 脚本 grep + AST 即可。精度不完美但能抓 PR-42 这个级别的"一端静默丢弃"。

### 环境 kill-switch

- `WAKE_CONTINUITY_TEXT=0` → `_build_continuity_block_for_wake` 整体短路（早已在 PR-42 预留了 enable_triggers，本 PR 再加一个显式总开关）
- `WAKE_CONTINUITY_HANDOFF_CLEAR=0` → 不清 handoff_notes（调试时有用）

## 范围

### runtime 侧
- `novaic-agent-runtime/task_queue/sagas/subagent_rest.py`（`_build_set_sleeping_payload` 读 step_results）
- `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py`（`handle_subagent_set_sleeping` 写 historical_summary）
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`（`handle_session_init` 消费后清 handoff_notes）
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`（Wave 1.5: `_exec_subagent_rest`）
- `novaic-agent-runtime/task_queue/workers/health_worker.py`（recovered metadata 注入）

### business 侧
- `novaic-business/business/subscribers/dispatch_subscriber.py`（`_deliver_one_inner` metadata 注入）
- 新增 `_CONTINUITY_ELIGIBLE_TRIGGERS` + 私有方法 `_resolve_continuity`

### 测试
- `novaic-agent-runtime/tests/test_subagent_rest_saga.py`：`_build_set_sleeping_payload` 从 step_results 提取 summary
- `novaic-agent-runtime/tests/test_subagent_handlers.py`：`handle_subagent_set_sleeping` 在 payload 带 summary 时写盘，不带时不写
- `novaic-agent-runtime/tests/test_session_init_handoff_clear.py`：消费后调用 entity_update 清空（+ kill switch 时不清）
- `novaic-business/tests/test_dispatch_subscriber_continuity.py`：USER_MESSAGE trigger metadata 被注入；SPAWN_SUBAGENT 不注入
- 契约 lint 通过

### 部署
- `./deploy services`（novaic-agent-runtime）
- `./deploy business`（dispatch_subscriber.py）
- 迁移：无

## 实施 Checklist

### A. 生产者
- [x] `subagent_rest._build_set_sleeping_payload` 读 `ctx.step_results.generate_simple_summary.simple_summary`
- [x] `handle_subagent_set_sleeping` 接收 `historical_summary`，非空时写入 `entity_update`
- [x] 单测：payload 带/不带 summary、空串 vs None
  - `novaic-agent-runtime/tests/test_pr45_continuity_wiring.py::test_set_sleeping_payload_*`
  - `novaic-agent-runtime/tests/test_pr45_continuity_wiring.py::test_handle_subagent_set_sleeping_*`

### B. 消费者入口
- [x] `dispatch_subscriber._resolve_continuity` 查 subagents 行（Entangled `/v1/entities/subagents/{id}` via 已有 outbox_client，service-token auth 复用）
- [x] `_deliver_one_inner` 对 USER_MESSAGE / SUBAGENT_SEND 注入 metadata，不覆盖上游已有值（`setdefault` 语义 + `None` 值不写）
- [x] 单测：注入成功 / trigger 不匹配跳过 / 上游值优先 / resolver 失败软失败 / kill switch 禁用
  - `novaic-business/tests/test_pr45_dispatch_continuity.py`

### C. health_worker（recovered 路径）
- [x] `_maybe_recover` 在 `assemble_and_dispatch_sync` 前注入 metadata（Business `/internal/entities/subagents/{id}`，走 `_get_business_client()`）
- [ ] 单测：RECOVERED trigger 注入（低风险——与 1B 结构同构，推迟到 live verify 后根据实际观测补，避免二遍造轮）

### D. 幂等消费
- [x] `handle_session_init`：PR-42 block 成功产出 handoff_notes 行时，调 entity_update 清空 `subagents.handoff_notes`
- [x] kill switch `WAKE_CONTINUITY_HANDOFF_CLEAR=0`
- [x] 单测：消费触发 clear / 被禁用时不 clear / clear 失败不挂起 session.init / spawn_subagent 不清
  - `novaic-agent-runtime/tests/test_pr45_continuity_wiring.py::test_handoff_*`

### E. 契约 lint
- [ ] `scripts/ci/lint_wake_continuity_contract.sh` 实现 metadata 流向 trace（延后——MVP 以单元测试覆盖同样的"生产者写什么消费者读什么一致"不变量，CI lint 作为 Wave 2 的加固层）
- [ ] `.github/workflows/lint.yml` 加 step

### F. 环境 flag
- [x] `WAKE_CONTINUITY_TEXT=0` 整体短路（DispatchSubscriber `_wake_continuity_text_enabled()` + HealthWorker `_maybe_recover` 同一环境变量）
- [x] `WAKE_CONTINUITY_HANDOFF_CLEAR=0`（D 节）
- [ ] ops runbook 更新（待部署验证后补）

### G. Wave 1.5（可并入同 PR）
- [ ] `_exec_subagent_rest` executor
- [ ] 单测：tool 调用 → `entity_update(need_rest=1, handoff_notes=...)` 正确
- [ ] 文档（agent 工具使用指南）提一次

## 验收

### 本地
```bash
cd novaic-agent-runtime && ./run_tests.sh tests/test_subagent_rest_saga.py tests/test_subagent_handlers.py tests/test_session_init_handoff_clear.py
cd novaic-business && ./run_tests.sh tests/test_dispatch_subscriber_continuity.py
./scripts/ci/lint_wake_continuity_contract.sh
```

### 端到端（staging）
```bash
# 1. 发一条 USER_MESSAGE
# 2. agent 回复后自动 rest（当前行为）
# 3. 查 subagents 行
sqlite3 entangled.db "SELECT historical_summary, handoff_notes FROM subagents WHERE subagent_id='main-X';"
# 预期：historical_summary 非空（PR-45 A 生效），handoff_notes 可能为空（MVP 不管 Wave 1.5）

# 4. 再发一条消息触发新 wake
# 5. 查新 scope context，应有 <HISTORICAL_SUMMARY> 段（PR-45 B+consumer 生效）
curl ... /v1/scope/NEW_SCOPE/context | jq '.messages[] | select(._message_type=="HISTORICAL_SUMMARY")'

# 6. 确认 handoff_notes 被清（如 Wave 1.5 已上，agent 前一轮 rest 写了 handoff）
sqlite3 entangled.db "SELECT handoff_notes FROM subagents WHERE ..." # None 或空
```

## 部署 Checklist（必走）

1. 代码合入父仓 main（含 novaic-agent-runtime、novaic-business submodule bump）
2. `./deploy business` + `./deploy services`
3. 线上证据 ≥ 2 段：
   - 日志 grep `event=wake_continuity kind=historical` 或 `kind=both`（今天 prod 为 0）
   - SQL check：wake 后 `subagents.historical_summary IS NOT NULL` 比例 > 0
4. 无迁移脚本

## 风险 / 讨论

1. **historical_summary 可能撑爆 token 预算**：PR-42 已有 `WAKE_CONTINUITY_MAX_BYTES=8KB` 截断；本 PR 不改。
2. **handoff_notes 清空 race**：session.init 在 scope 创建早期调 entity_update；如果同一时刻有另一路 PATCH 写了新的 handoff_notes（极罕见），会被清掉。缓解：`update_with_condition`（只在值等于消费时读到的那个值才清）——MVP 不做，观察 1 周。
3. **契约 lint 精度有限**：MVP 版只能抓 key 名漂移，抓不了语义变化（同名但含义变了）。合理折衷。
4. **Wave 1.5 的 `_exec_subagent_rest` 与 react_actions.decide_rest 的决策主权冲突**：当前设计下，`_exec_subagent_rest` 只**记录 intent**（写 subagents 字段 + `need_rest=1`），实际 rest 入口仍由下一次 decide_rest 走正常 saga。这样避免 tool call 和 saga decision 争抢，也解释了 Wave 1.5 为什么叫"compatible patch"。

## 承诺登记

- **R9 文字层** 从 PR-42 的"消费端就绪"升级为"端到端通路"。历史总结自动累积、交接笔记一次性消费。
- **R10（新增）**：Producer/Consumer Field Contract — 跨包的 data carrier field 必须有 CI 契约测试。登记到 `docs/architecture/message-wake-principles.md §六契约表`（本 PR 起草条目，PR-43 继续扩展 `previous_scope_id` 条目）。

## 备注

- PR-45 解锁 PR-43 的基线：等 prod 能稳定 grep 到 `event=wake_continuity kind=historical` 再上 PR-43 的 `<PREV_SCOPE_TAIL>`。否则两层一起开，日志会很难定位哪层在起作用。
- `subagents.handoff_notes` 已在 schema 里，不需要迁移；`historical_summary` 同理。
- Wave 1.5 的 `_exec_subagent_rest` 虽是"1 个 executor"，但可能暴露出 agent prompt 根本不知道该调它的系统性问题——那是 prompt engineering 范畴，不是本 PR。
