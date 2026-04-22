# PR-49  `subagent_rest` tool executor（PR-45 Wave 1.5：把 LLM 的 handoff_notes 接回来）

| 字段 | 值 |
| --- | --- |
| **Phase** | PR-45 Wave 1.5（R9 文字层 producer 端闭环） |
| **Milestone** | R9 text layer（完整 producer → consumer） |
| **承诺** | R9 + R8 |
| **Status** | `[~]` (2026-04-23 代码 + 12 单测完成；线上部署待验证) |
| **Depends on** | PR-45（consumer 端已就绪）、PR-28（subagent 状态机） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(runtime): implement subagent_rest tool executor; persist handoff_notes and trigger rest saga` |

## 事件摘要

PR-45 把消费端的 `subagents.handoff_notes` 读 → 注入 `<HANDOFF_NOTES>` 段链路全部打通。但**生产端仍然瘸腿**：

1. **saga 端已就绪**：PR-45 Wave 1A 让 `subagent_rest` saga 的 `generate_simple_summary` 结果写入 `subagents.historical_summary`。
2. **LLM 端仍空着**：LLM 可以看到 `subagent_rest` 工具定义（`common/tools/definitions.py`），参数表里明明有 `handoff_notes: string`、`rest_duration_minutes: int`、`wake_triggers: string[]`，但：

```python
# novaic-agent-runtime/task_queue/handlers/tool_handlers.py
TOOL_EXECUTORS = {
    "chat_reply":       _exec_chat_reply,
    "skill_begin":      _exec_skill_begin,
    "skill_end":        _exec_skill_end,
    # ... 其它工具 ...
    # ← subagent_rest 这里**根本没有**
}
```

LLM 真的调用 `subagent_rest(handoff_notes="下轮继续回复用户关于时间的问题")` 时：

- tool_handlers 找不到 executor；
- 走未知工具兜底（大概率吞错误或返回 "tool not found"）；
- LLM 的手写 handoff_notes **完全丢失**。

这是 PR-45 Wave 1B（读 subagents.handoff_notes）永远读到 NULL 的第一现场。叠加 PR-48（强制 rest）之前 LLM 也从不会自己调 rest，所以这条链路**从上线到今天没被走通过一次**。

## 方案

### A. 实现 `_exec_subagent_rest`

```python
# tool_handlers.py
def _exec_subagent_rest(args: dict, deps: dict) -> dict:
    """
    PR-49 (2026-04-XX) — LLM 请求主动休息，同时 handoff 给下次唤醒自己。

    参数（与 common/tools/definitions.py 的 subagent_rest 工具定义一致）：
      - handoff_notes (str, 可选但强烈建议)：给下次醒来的自己的便条
      - rest_duration_minutes (int, 可选，默认 None = 无时间唤醒)
      - wake_triggers (list[str], 可选，默认 ["USER_MESSAGE", "SUBAGENT_SEND"])

    副作用：
      1. 持久化 handoff_notes 到 subagents.handoff_notes（被 PR-45 Wave 1B 消费）
      2. 触发 subagent_rest saga（走 generate_simple_summary → set_sleeping）
      3. 当前 scope 进入 "waiting for saga to close" 状态，不再 think
    """
    agent_id = deps["agent_id"]
    subagent_id = deps["subagent_id"]
    scope_id = deps["scope_id"]
    business_client = deps["business_client"]
    queue_client = deps["queue_client"]

    handoff_notes = (args.get("handoff_notes") or "").strip() or None
    rest_duration = args.get("rest_duration_minutes")
    wake_triggers = args.get("wake_triggers") or ["USER_MESSAGE", "SUBAGENT_SEND"]

    # 1. 持久化 handoff_notes（即使后面 saga 失败，便条也不会丢）
    if handoff_notes:
        try:
            business_client.entity_update(
                "subagents",
                subagent_id,
                {
                    "handoff_notes": handoff_notes,
                    "_transition_reason": "rest_handoff",
                    "_transition_actor": "llm.tool.subagent_rest",
                },
                params={"agent_id": agent_id},
            )
            metric_inc("subagent_rest_handoff_persisted_total", result="ok")
        except Exception as exc:
            metric_inc("subagent_rest_handoff_persisted_total", result="error")
            logger.warning(
                "[tool.subagent_rest] handoff persist failed agent=%s subagent=%s err=%s",
                agent_id, subagent_id, type(exc).__name__,
            )
            # 不 raise——LLM 的核心意图是"休息"，便条失败仍可休息
    # 2. 触发 rest saga
    saga_id = queue_client.create_saga(
        "subagent_rest",
        agent_id=agent_id,
        subagent_id=subagent_id,
        scope_id=scope_id,
        handoff_notes=handoff_notes,              # saga ctx 透传
        wake_triggers=wake_triggers,
        rest_duration_minutes=rest_duration,
        actor="llm.tool.subagent_rest",
    )
    metric_inc("subagent_rest_tool_invoked_total", source="llm")

    return {
        "success": True,
        "saga_id": saga_id,
        "handoff_persisted": handoff_notes is not None,
        "wake_triggers": wake_triggers,
        "message": "Going to rest now. See you next wake.",
    }
```

### B. 注册到 `TOOL_EXECUTORS`

```python
TOOL_EXECUTORS = {
    "chat_reply":       _exec_chat_reply,
    "skill_begin":      _exec_skill_begin,
    "skill_end":        _exec_skill_end,
    "subagent_rest":    _exec_subagent_rest,   # ← 新增
    # ... 其它工具 ...
}
```

### C. 与 PR-48 Turn Finalizer 的协作

- LLM 主动调 `subagent_rest` → 本 executor 触发 saga、写 `handoff_notes`；PR-48 的 `_should_finalize_turn` 看到 "last_tool == subagent_rest" 不会再触发 REPLY_NO_FOLLOWUP finalize（天然 idempotent）。
- LLM 不调 → PR-48 兜底，saga 启动时 `handoff_notes=None`，`subagents.handoff_notes` 不被 set（`isinstance(summary, str) and summary.strip()` 判空分支）；下次唤醒 `<HANDOFF_NOTES>` 段不渲染，但 `<HISTORICAL_SUMMARY>` 仍可用（由 saga `generate_simple_summary` 兜底）。

两条路径都能闭合 R9 承诺，区别只是 "LLM 自述便条 vs 自动摘要兜底"。

### D. 幂等 & 错误路径

1. **重复调用**：LLM 在一轮里调两次 `subagent_rest` 应当幂等。saga 创建时用 `idempotency_key=f"rest:{scope_id}"`，Queue Service 识别到重复直接返回已创建的 saga_id。
2. **scope 已 sleeping**：`business_client.entity_update` 可能被 subagent 状态机（PR-28）拒（只有 `running → sleeping` 合法）。executor 捕获并返回 `success=True, already_sleeping=True`——LLM 不需要知道细节。
3. **handoff_notes 太长**：按 PR-42 的 `WAKE_CONTINUITY_MAX_BYTES` 在消费端截断；生产端不额外校验（宽松写入，消费端 fail-safe）。
4. **rest_duration_minutes 未实现**：当前系统没有"时间到自动 wake"机制。executor 仍接受该参数但记 `metric_inc("subagent_rest_unused_param_total", param="rest_duration")`——避免未来实现时忘了这里。

## 范围

### runtime
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`：加 `_exec_subagent_rest` + 注册
- `novaic-agent-runtime/tests/test_tool_subagent_rest.py`（新）

### common
- 确认 `novaic-common/common/tools/definitions.py::subagent_rest` 的参数 schema（只读，不改）

### 文档
- `docs/architecture/agent-pipeline.md`：补 "LLM 主动休息" 路径
- `docs/roadmap/tickets/PR-45-...md`：Wave 1.5 checklist 打勾

## 实施 Checklist

### A. executor
- [ ] `_exec_subagent_rest` 按上述规格实现
- [ ] 注册进 `TOOL_EXECUTORS`
- [ ] metric `subagent_rest_handoff_persisted_total{result}`
- [ ] metric `subagent_rest_tool_invoked_total{source}`
- [ ] handoff_notes 空/None 分支不写 DB 也不 raise

### B. 单测
- [ ] 带 handoff_notes → 写入 subagents.handoff_notes + 触发 saga
- [ ] 空 handoff_notes → 不写 subagents，但仍触发 saga
- [ ] business_client 写入失败 → 仍触发 saga（soft-fail）
- [ ] 重复调用同 scope → 第二次返回同一 saga_id（idempotent）
- [ ] 未知参数（e.g., LLM 多传 "foo=bar"）→ 忽略，返回 success
- [ ] LLM 调用时 scope 已经 sleeping → 返回 `success, already_sleeping=True`

### C. 集成回归
- [ ] PR-45 `test_pr45_continuity_wiring.py` 绿
- [ ] PR-48 `test_turn_finalizer.py` 绿

### D. 线上打标
- [ ] `actor="llm.tool.subagent_rest"` 在 `subagent_state_transitions` 表可被查询统计（PR-31）

## 验收

### 本地
```bash
cd novaic-agent-runtime && ./run_tests.sh tests/test_tool_subagent_rest.py tests/test_pr45_continuity_wiring.py tests/test_turn_finalizer.py
```

### 线上
```bash
# 1. 发 user_message 等 LLM chat_reply
# 2. 看日志 —— LLM 理想路径应该是：
#    think → chat_reply → think → subagent_rest(handoff_notes="...")
grep 'tool.subagent_rest' /opt/novaic/data/logs/runtime-*.log | tail -5

# 3. 查 subagents 表
ssh prod sqlite3 /opt/novaic/data/entangled.db \
  "SELECT subagent_id, handoff_notes, historical_summary, status \
   FROM subagents WHERE agent_id='<aid>' ORDER BY updated_at DESC LIMIT 3;"
# 预期：
#   status='sleeping'
#   handoff_notes 非空（LLM 写的便条）
#   historical_summary 非空（saga 里 generate_simple_summary 写的）

# 4. 再发一条新消息，看 <HANDOFF_NOTES> 是否出现在新 scope 的 initial_context
grep 'event=continuity_injected' /opt/novaic/data/logs/runtime-*.log | tail -3
grep '<HANDOFF_NOTES>' /opt/novaic/data/logs/runtime-*.log | tail -3
```

## 部署 Checklist（必走）

1. 代码合入父仓 main
2. `./deploy runtime`
3. 线上证据 ≥ 3 段：
   - `subagent_rest_tool_invoked_total{source="llm"}` 近 1h ≥ 1
   - `subagent_rest_handoff_persisted_total{result="ok"}` 近 1h ≥ 1
   - 新 USER_MESSAGE 触发的 session.init 日志命中 `<HANDOFF_NOTES>` 段（非 null、非 empty）
4. 负向：`subagent_rest_handoff_persisted_total{result="error"}` 近 1h 低于 ok 的 5%（偶发允许）

## 风险 / 讨论

1. **LLM 调 subagent_rest 的频率**：完全依赖 prompt 约定。即使 prompt 不改，PR-48 兜底也能让 `historical_summary` 生成；本 PR 只是把"LLM 手写便条"这条增益通道打通。
2. **handoff_notes 里被 LLM 塞敏感信息**：当前没有 PII 过滤。短期接受——便条是 agent → agent 自流转，不直接 echo 给用户。中期如果需要可以在 consumer 端（PR-42 注入点）加脱敏层。
3. **rest_duration_minutes 暂未实现**：LLM 可能觉得它起作用（其实不）。加上 `subagent_rest_unused_param_total` metric 让未来实现时知道哪里需要补；prompt 层也可以直接删掉这个参数以免误导。
4. **subagent_rest 被 LLM 误用于"我不想回复这个用户"**：prompt 层应要求 LLM 先 chat_reply 再 rest。runtime 侧不防。
5. **handoff_notes 不被清除**：PR-45 Wave 1C 的 `WAKE_CONTINUITY_HANDOFF_CLEAR` 会在下次 wake 消费后清空。这里的写入和那里的清空形成完整的"一次性便条"生命周期：LLM 写 → 下次醒来读 → 立即清。

## 承诺登记

- **R9**：文字层 producer → consumer 两端都通。`<HANDOFF_NOTES>` 段能够真的装东西而不是永远空字符串。
- **R8**：LLM 走 tool 触发状态机 transition 是 R8 "状态机单一入口" 的核心路径，之前 `subagent_rest` 的 LLM 入口半截工程（定义了没实现）违反了这条承诺，本 PR 补齐。

## 备注

- 强烈建议本 PR 和 PR-48 一起上线；独立上线 PR-49 的话，需要 prompt 端同步提醒 LLM 调用 `subagent_rest`，否则本 executor 形同虚设。
- tool definitions 里 `rest_duration_minutes` 如果想删，另开 schema 变更 PR；本 PR 保守保留该字段（向后兼容）。
