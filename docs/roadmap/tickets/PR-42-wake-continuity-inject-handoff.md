# PR-42  Wake 时把 `handoff_notes` / `historical_summary` 注入新 scope

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix / 新承诺 R9（Wake continuity — 短期止损） |
| **Milestone** | — |
| **承诺** | R9（新增，见下方"承诺登记"） |
| **Status** | `[x]` 实施完成（2026-04-21） |
| **Depends on** | PR-13（SchedulerWorker → Assembler）、PR-20（scope meta inputs） |
| **Blocks** | PR-43（scope 续链；本 PR 先用"注入"替代"续链"，是完备性的 80/20） |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(runtime): inject handoff_notes + historical_summary into new scope's initial context on wake` |

## 事件摘要

用户反馈："agent 苏醒时不带历史 scope，上下文设计得很糟糕。"

排查结论（见 `docs/roadmap/tickets/PR-41-...` 的姊妹 ticket 上下文）：

`subagent_rest` 工具允许 agent 睡眠前写入：
- `handoff_notes`：主动交接（"我正在修 X，下次醒来继续 Y"）
- `rest_duration_minutes`：自醒时间
- `wake_triggers`：唤醒条件

`SchedulerWorker` 定时唤醒时，通过 `_wake_metadata(...)` 把 `handoff_notes` 塞进 dispatch metadata；`SessionRepository.dispatch` 把 metadata 展开到 `saga_context`。**但** `subagent_wake._build_session_init_payload` **只提取** `scope_id / agent_id / subagent_id / user_id / trigger_type / initial_context / user_message / message_ids`，**`handoff_notes` 被 silently drop**。

`historical_summary` 字段在 `subagents` 表 schema 存在、Business PATCH 端点支持写入，但 `rg historical_summary novaic-agent-runtime/` **零读取**。

结果：agent 每次苏醒都从"只有 system prompt + Recall(已归档 root scope 的粗摘要)"开始，"我上次睡前想继续做什么"完全丢失。

## 根因

**设计意图断层**：`subagent_rest` tool schema 承诺了 "handoff_notes 会在下次苏醒时被带回来"，但实现链路在 saga payload build 层把它扔了。

涉及文件：
- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py::_build_session_init_payload`（不读 handoff_notes）
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py::handle_session_init`（即使 payload 带了也不消费）
- `novaic-agent-runtime/task_queue/workers/scheduler_worker.py:132` 确认 `handoff_notes` 已被放入 metadata（上游没问题）

## 方案

**最小改动：透传 + 注入**。不改 scope_id 策略（那是 PR-43 的事），只把已有但被丢弃的字段接起来。

### 1. saga payload 透传

`_build_session_init_payload`：

```python
def _build_session_init_payload(ctx):
    payload = {
        "scope_id": ctx["scope_id"],
        ...
    }
    ...
    # 新增：wake continuity payload（R9）
    if ctx.get("handoff_notes"):
        payload["handoff_notes"] = ctx["handoff_notes"]
    if ctx.get("wake_reason"):
        payload["wake_reason"] = ctx["wake_reason"]  # "scheduled" / "recovered" / ...
    return payload
```

`handoff_notes` / `wake_reason` 已经被 `scheduler_worker._wake_metadata` 和 `SessionRepository.dispatch` 送到 saga_context，这里只是把"取出来"这一步补上。

### 2. session.init 消费 handoff + historical_summary

`handle_session_init`：

```python
# 在 step 3 "Build initial context" 之后、step 4 "System Prompt" 之前
# —— 这样 system prompt 仍然是第 0 条；wake continuity 作为紧接其后的
# system 级别上下文，不污染 recall messages 的位置，便于后续 compact 策略辨识。

wake_reason = payload.get("wake_reason")
handoff_notes = payload.get("handoff_notes")

# historical_summary 从 subagent 实体拉（saga payload 不必再塞一遍，
# business_client 已是 handler 注入，避免 saga 层面对所有唤醒路径都 fetch）
historical_summary = None
if wake_reason in ("scheduled", "recovered", "user_message"):  # 即非首次 spawn
    try:
        sa = business_client.get_subagent(agent_id, subagent_id)
        historical_summary = (sa or {}).get("historical_summary")
    except Exception as e:
        print(f"[session.init] historical_summary fetch failed: {e}")

continuity_block: list[dict] = []
if handoff_notes:
    continuity_block.append({
        "role": "system",
        "content": f"<HANDOFF_NOTES>\n{handoff_notes}\n</HANDOFF_NOTES>",
        "_message_type": "WAKE_CONTINUITY",
    })
if historical_summary:
    continuity_block.append({
        "role": "system",
        "content": f"<HISTORICAL_SUMMARY>\n{historical_summary}\n</HISTORICAL_SUMMARY>",
        "_message_type": "WAKE_CONTINUITY",
    })

# 把 continuity_block 插在 initial_context 的 "recall_messages 之后"、
# "system prompt 之前" 的位置（step 4 会把 system_prompt 插到 index 0）
initial_context.extend(continuity_block)
```

### 3. 不做什么（范围收敛）

- **不改** `SessionRepository.dispatch` 的 `scope_id = uuid.uuid4()` → PR-43
- **不引入** previous scope 的 `context.jsonl` 读取 → PR-43
- **不改** `recall_messages()` 的行为（它按 PR-20/cortex/recall.md 的设计服务于跨 session 长期记忆）
- **不读** chat_messages 历史（那是 PR-44）

### 4. trigger_type 门控

`continuity_block` 只在"非首次 spawn"时注入：

| trigger_type | 注入 handoff / historical_summary？ | 原因 |
|---|---|---|
| `SPAWN_SUBAGENT` | **否** | 刚刚创建，没有"上次" |
| `SCHEDULED_WAKE` | 是 | 主要场景 |
| `RECOVERED` | 是 | orphan 恢复也应携带交接 |
| `USER_MESSAGE`（sleep 后用户来消息） | 是 | sleep 期间用户续对话，需要 handoff |
| `SUBAGENT_SEND` | 是 | 父 agent 回来给子 agent 发东西 |
| `SYSTEM_WAKE` | 是 | 与 SCHEDULED 同 |

**注入判据**：`wake_reason != "spawn"` 且 `historical_summary` / `handoff_notes` 非空。

## 范围

- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py::_build_session_init_payload`（+2 字段透传）
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py::handle_session_init`（新增 continuity block 构造）
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`（可能新增 helper，视注入点而定）
- 必要时：`common/business_client.py` 的 `get_subagent` 合约确认（应已存在）

## 前置 Checklist

- [x] PR-13 SchedulerWorker 已经走 Assembler（生产 `[x]`），`handoff_notes` 在 dispatch metadata 里
- [x] Queue Service `SessionRepository.dispatch` 会把 metadata spread 进 saga_context（`session_repo.py:116 / :284 / :404` 三处 spread）
- [x] `business_client.entity_get("subagents", subagent_id, params={"agent_id": ...})` 返回体含 `historical_summary`（`helpers._subagent_to_dict` 透出）

## 实施 Checklist（2026-04-21 实施）

### 1. Payload 透传 ✔

- [x] `_build_session_init_payload`：`handoff_notes` / `wake_reason` 透传（`subagent_wake.py:40-60`）
- [x] 单测 `test_saga_payload_forwards_handoff_notes_and_wake_reason` / `test_saga_payload_omits_handoff_fields_when_absent` / `test_saga_payload_omits_empty_handoff_notes`
- [x] 其他 saga 不受影响（只读自己的 ctx 字段；未改动它们的 payload builder）

### 2. session.init 消费 ✔

- [x] `runtime_handlers.py` 新增：
  - `_build_wake_continuity_messages(...)`：纯函数构造 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` system message 列表
  - `_fetch_historical_summary(...)`：经 `entity_get("subagents", ...)` 读，异常软失败
  - `_build_continuity_block_for_wake(...)`：orchestrator，处理 fetch short-circuit + metrics + log
  - `_continuity_kind_label(...)`：`both | handoff | historical | none` 标签
- [x] `handle_session_init` step 3b：在 recall_messages 后、system_prompt `insert(0,…)` 前 `extend` 注入，最终顺序 `[SYSTEM_PROMPT, HANDOFF, HISTORICAL, recall…]`
- [x] `context_parts` 计数一致；`initial_context` 已由 caller 提供时（sub-subagent bootstrap）短路不叠加
- [x] `SPAWN_SUBAGENT` 路径不 fetch subagent —— orchestrator 中 `if trigger_type in WAKE_CONTINUITY_ENABLED_TRIGGERS:` 短路，builder 里再加一层门控 fail-closed
- [x] 单测（`tests/test_wake_continuity_injection.py` 29 cases）：
  - 注入顺序（scheduled_wake + handoff → `[SYSTEM, HANDOFF]`）
  - `historical_summary` 通过 entity_get 返回（scheduled_wake + handoff + historical → `[SYSTEM, HANDOFF, HISTORICAL]`）
  - `spawn_subagent + handoff_notes="leaked parent state"` → 无 WAKE_CONTINUITY
  - caller 传 `initial_context` → 无 WAKE_CONTINUITY
  - 两字段都空 → 仅 SYSTEM_PROMPT
  - Business 500 软失败 → saga 仍 success，handoff 仍注入
  - `WAKE_CONTINUITY_ENABLED_TRIGGERS` 参数化回归
  - 未知 trigger fail-closed

### 3. Business client ✔

- [x] 复用现有 `entity_get("subagents", subagent_id, params={"agent_id": agent_id})`（runtime `BusinessClient.entity_get` 已存在）
- [x] Business `/internal/entities/subagents/{id}` 走 `EntityStore.get("subagents", ...)` 直接读 row，字段含 `historical_summary`（schema）与 `handoff_notes`（同字段也可以，PR-42 只读 historical）
- [x] 不新增命名 helper —— 沿用 PR-20 已有的 entity CRUD 通道避免多条读路径

### 4. 长度限制 ✔

- [x] 模块常量 `WAKE_CONTINUITY_MAX_BYTES = 8 * 1024`
- [x] `_cap_continuity_text(value, kind)`：UTF-8 字节前缀裁剪 + `errors="ignore"` 保证合法 UTF-8 + 尾部 `\n…[truncated]` 标记
- [x] 超限触发 `WARN event=wake_continuity_truncate kind=... orig_bytes=... capped_bytes=...` + `metric_inc("wake_continuity_truncated_total", kind=...)`
- [x] 单测：`test_cap_preserves_small_text_unchanged` / `test_cap_truncates_large_text_with_marker` / `test_cap_handles_utf8_boundary` / `test_handler_truncates_oversized_handoff`
- [x] 原始 `subagents.handoff_notes` / `.historical_summary` 未被修改（只在注入路径截断；审计价值不丢）

## 测试 Checklist

- [x] 单测：`_build_session_init_payload` 透传（3 cases）
- [x] 单测：`_build_wake_continuity_messages` trigger 矩阵 + 截断 + 顺序（15+ cases）
- [x] 单测：`handle_session_init` 集成（9 cases 覆盖 inject / skip / fallback / truncate / fetch 短路）
- [x] 全量回归：Entangled 114 passed / novaic-business 74 passed / novaic-agent-runtime 101 passed（含新增 29）
- [ ] 集成（端到端，staging 部署后）：设 `rest_duration_minutes=1` + `handoff_notes="debugging X"` → 等 ~65s → 新 scope `context.jsonl` 含 `<HANDOFF_NOTES>` 段
- [ ] 回归（端到端）：`spawn_subagent` 路径下新 SubAgent 的 `context.jsonl` 不含 WAKE_CONTINUITY

## 可观测性 Checklist ✔

- [x] Metric `wake_continuity_injected_total{kind=handoff|historical|both|none, trigger_type}` —— 每次 wake 一次计数（包括 `kind=none`，便于减法少一步）
- [x] Metric `wake_continuity_truncated_total{kind=handoff_notes|historical_summary}` —— 截断次数
- [x] Log: `event=wake_continuity kind=... trigger=... handoff_bytes=... historical_bytes=... agent_id=... subagent_id=...`（仅非空时打）
- [x] Log: `event=wake_continuity_truncate kind=... orig_bytes=... capped_bytes=...`（WARN）
- [x] Log: `event=wake_continuity_fetch_failed agent_id=... subagent_id=... err=...`（WARN，Business 读失败）

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) Phase 6 小节已包含 `R9` 承诺 + P6-2 描述
- [x] 本工单 Status → `[x]`
- [ ] [docs/architecture/message-wake-principles.md](../../architecture/message-wake-principles.md) §承诺表加 R9（后续批量更新时处理）
- [ ] `docs/cortex/session-meta-json.md` 如有 wake 章节需补（当前无 wake 章节，免跟）
- [ ] runbook：`docs/runbooks/troubleshooting.md` 加 "wake 后 agent 看不到上次上下文" 排查路径（部署后补）

## 验收命令

```bash
# 1) 构造：设 agent_id=A，让其 subagent_rest(handoff_notes="X", rest_duration_minutes=1)
# 2) 等 65 秒 + 5 秒调度 slack
sleep 70

# 3) 找最新 scope
SUBAGENT_ID=$(curl -s .../internal/agents/A/subagents | jq -r '.[0].id')
LAST_SCOPE=$(curl -s .../internal/agents/A/subagents/$SUBAGENT_ID | jq -r '.last_scope_id // .scope_id')

# 4) 查 context.jsonl
curl -s .../cortex/v1/scope/$LAST_SCOPE/context | jq '.messages[] | select(._message_type=="WAKE_CONTINUITY")'
# → 应能看到 HANDOFF_NOTES 块

# 5) 查 metric
curl -s .../metrics | rg 'wake_continuity_injected_total'
```

## 部署 Checklist（必走，不部署不算完成）

- [ ] **本地代码已合入 main**：`git log --oneline origin/main | rg PR-42`
- [ ] **runtime 子模块已 bump** 并推到父仓库远端
- [ ] **已 deploy**：父仓库根 `./deploy runtime`（rsync runtime + 远端 `start.sh --stop && start.sh`）
- [ ] **线上证据 1 — saga 透传**：`ssh api.gradievo.com 'grep -E "session\\.init.*handoff_notes" /opt/novaic/logs/runtime*.log | tail -5'` 新 wake 的 payload 含 `handoff_notes`
- [ ] **线上证据 2 — Cortex 写盘**：任一新 wake 的 scope 里 `context.jsonl` 含 `_message_type=WAKE_CONTINUITY` 记录（curl 验收命令第 4 步）
- [ ] **线上证据 3 — 指标**：`curl -s https://api.gradievo.com/metrics | rg 'wake_continuity_injected_total'` 计数器 > 0
- [ ] 把上述三段 paste 进 PR 关单评论

## 回滚

- 两处改动都在 runtime 侧，git revert 即可
- 回滚后 handoff_notes 再次被忽略（回到现状），不影响其他路径
- **不**需要回滚 schema / DB 数据

## 承诺登记

**新增 R9 — Wake Continuity**（建议加入 `docs/architecture/message-wake-principles.md`）：

> 一个 sleeping → awake 转换点必定有"非空的短时记忆承接"：
> - 写入侧：`subagent_rest` 工具承诺的 `handoff_notes` 必定持久化到 `subagents` 实体
> - 读取侧：`session.init` 在非首次 spawn 的 wake 路径上，必定把 `handoff_notes` + `historical_summary` 注入新 scope 的 `initial_context`
> - 可观测：`wake_continuity_injected_total{kind}` 能分辨每次 wake 到底注入了什么

本 R9 不回答"如何续接前一次 scope 的完整历史"（那是 PR-43 + R9 加强版的任务），只承诺"agent 能看到它自己写的睡前 note"。

## 备注

- `handoff_notes` 是 **agent 自描述的交接**；`historical_summary` 是 **系统生成的累计总结**（`subagent_rest` saga 中的 `generate_simple_summary` 产出）。两者互补：前者是最新、最具体；后者是更长时段的压缩。
- 不在本 PR 做的后续动作：
  - PR-43：scope 续链 —— 让新 scope 能回溯上一次 scope 的最近 N 步 step，补齐"代码上下文 / 工具结果"这种非文字摘要能承载的信息。
  - PR-44：IM 流回放 —— 解决"sleep 期间多条用户消息的上下文恢复"。
- `handoff_notes` 建议加"生成时间戳"注释到 prompt 里（`<HANDOFF_NOTES at=2026-04-21T12:58Z>`），帮 LLM 判断新鲜度。


---

## 2026-04-23 postscript (superseded by PR-55)

**Status: dead code, removed**.

PR-42 wired Business `continuity_resolve` → Runtime `session.init` →
prompt `<HANDOFF_NOTES>` block. The producer side never existed:
`subagent_rest` is **not** an LLM-callable tool (see
`novaic-cortex/.../tool_schemas.py::BUILTIN_TOOL_SCHEMAS`), so no
agent ever wrote to `subagents.handoff_notes`. The consumer side
therefore always rendered empty. PR-55 removed:

- the `<HANDOFF_NOTES>` block construction in the runtime prompt,
- the `handoff_notes` fetch in Business `_resolve_continuity`,
- the `handoff_notes` forwarding in `subagent_wake` / scheduler
  `_wake_metadata`,
- all associated tests.

The `subagents.handoff_notes` column is left in place as a tolerant
legacy column (no live reader/writer); see
[`PR-55-phantom-summary-pipeline-cleanup.md`](./PR-55-phantom-summary-pipeline-cleanup.md).
R9's text-layer now collapses to `<PREV_SCOPE_TAIL>` only; the
state-layer anchor (`subagents.last_scope_id`) remains the live
cross-scope continuity channel.
