# No-Tool 处理重构：合成工具 → System Message 注入

> 状态: **设计稿**  
> 作者: AI Assistant + CQ  
> 日期: 2026-04-04  

---

## 1. 背景与动机

### 当前方案

当 LLM 返回纯文本（无 `tool_calls`）时，ReactThink saga 在两个位置注入合成 tool_calls：

1. **`_build_save_response_payload`**（Step 3）— 修改 assistant 消息，注入假 `subagent_send(warning)` + `sleep(1s)`
2. **`_decide_and_build_actions`**（Step 4）— 构建同样的假 tool_calls 传给 ReactActions

ReactActions 执行这些假工具时，`tool_handlers.py` 用 `tool_call_id` 前缀 `no-tool-` 检测到是合成调用，做 no-op 处理。

此外，LLM 有时会返回 `done`、`final`、`finish` 等不在工具列表中的工具名，当前将它们转换为 `subagent_rest` 执行。实际上这些工具不在我们的 11-tool 列表里，不应被识别和执行。

### 问题

| 问题 | 描述 |
|------|------|
| **Context 污染** | LLM 下一轮看到自己从未发出的 `tool_calls` + `tool_results`，可能导致模型困惑 |
| **复杂度高** | 合成 ID 生成、前缀匹配、no-op 分支、ReactActions 中 `result_id` 缺失兼容 |
| **不直观** | Warning 藏在 `subagent_send` 的 `arguments` 里，不是自然的对话消息 |
| **Moonshot hack** | 预注入 tool_calls 是为了让 tool_results 有对应的 `tool_call_id`，属于 API 兼容 workaround |
| **未知工具误执行** | `done/final/finish` 等不在工具列表中，不应转换为 `subagent_rest` 执行 |

---

## 2. 设计目标

1. **Context 零污染** — assistant 消息原样保存，不注入任何假 tool_calls
2. **Warning 自然** — 以 system message 注入 LLM 调用，不存入 DB
3. **Saga 只做编排** — 不构造假数据，不执行假工具
4. **未知工具 = 无工具** — tool_calls 中不在工具列表里的工具名一律剥离；剥离后无有效工具则视为 no-tool
5. **利用已有机制** — 使用 saga 框架的 `condition` 分支，不引入新抽象

---

## 3. 架构对比

### 3.1 当前流程（合成工具）

```
ReactThink:
  read_context → call_llm → save_response(注入假 tool_calls) → decide → trigger ReactActions
                                                                            │
ReactActions:                                                               ▼
  execute_tools(no-op send + sleep) → save_results(假 tool results) → check_continue → decide
                                                                                         │
                                                                      ┌──────────────────┤
                                                                      ▼                  ▼
                                                               ReactThink         RuntimeComplete
                                                            (LLM 看到假 tool_calls)
```

第 1 次 no-tool: 注入 `subagent_send(warning)` + `sleep(1s)` → ReactActions 执行 no-op → 下一轮  
第 2 次 no-tool: 注入 `subagent_rest` → ReactActions 执行 → `need_rest=1` → RuntimeComplete

### 3.2 新流程（system message 注入）

```
ReactThink:
  read_context → call_llm → save_response(原样) → decide
                                                    │
                                  ┌─────────────────┼─────────────────┐
                                  ▼                 ▼                 ▼
                          5a: trigger         5b: trigger        5c: trigger
                          ReactActions        ReactThink         RuntimeComplete
                          (有 tool_calls)     (retry, +warning)  (连续无工具)

下一轮 ReactThink (retry):
  read_context → call_llm(messages 末尾注入 system warning，不落库) → ...
```

第 1 次 no-tool: 原样保存 → 跳过 ReactActions → 直接触发下一轮 ReactThink  
第 2 次 no-tool: 原样保存 → 跳过 ReactActions → 直接触发 RuntimeComplete  
Warning: 在 `_build_llm_call_payload` 中瞬态注入，仅存在于本次 LLM API 调用的 messages 中

---

## 4. 详细变更清单

### 4.1 `react_think.py` — 核心变更

#### 4.1.1 `_build_save_response_payload`（Step 3）

**删除** 所有合成 tool_calls 注入逻辑。**新增**幻影工具剥离逻辑。

```python
# BEFORE (删除整段)
if not message.get("tool_calls"):
    if no_tool_retry_count < 1:
        message["tool_calls"] = [...]   # 假 subagent_send + sleep
    else:
        message["tool_calls"] = [...]   # 假 subagent_rest

# AFTER — 剥离幻影工具，保留真实工具
```

变更后的函数职责：
1. 从 LLM response 提取 message
2. 处理 LLM error（`[LLM Error]`）和空响应（`[No response from LLM]`）
3. **过滤未知工具**：从 `tool_calls` 中移除不在工具列表里的工具名
4. 如果过滤后 `tool_calls` 为空，**删除** `tool_calls` 字段（变为纯文本 assistant 消息）
5. 存入 DB

```python
def _get_known_tool_names(ctx):
    """从 ctx["tools"]（传给 LLM 的工具 schema 列表）中提取合法工具名"""
    tools = ctx.get("tools") or []
    return {t.get("function", {}).get("name") or t.get("name", "") for t in tools}


def _build_save_response_payload(ctx, prev_result):
    """Step 3: 保存 LLM 响应
    
    关键变更：
    1. 不再注入合成 tool_calls
    2. 过滤不在工具列表中的 tool_calls（如 done/final/finish 等）
       过滤后若无有效工具，assistant 消息变为纯文本（无 tool_calls）
    """
    # ... 提取 message（error / empty 处理不变）...

    # 过滤未知工具
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        known = _get_known_tool_names(ctx)
        real_calls = [tc for tc in tool_calls 
                      if tc.get("function", {}).get("name") in known]
        if real_calls:
            message["tool_calls"] = real_calls
        else:
            message.pop("tool_calls", None)  # 全是未知工具 → 纯文本消息

    return {
        "runtime_id": ctx["runtime_id"],
        "message": message,
        "message_type": "llm_response",
        "round_id": f"round-{ctx.get('round_num', 1)}",
        "idempotency_key": f"{ctx['runtime_id']}-round{ctx.get('round_num', 1)}-response",
    }
```

**工具列表来源**：`ctx["tools"]` 是 saga 创建时传入的工具 schema 列表（与发给 LLM 的一致）。从中提取 `name` 字段得到合法工具名集合。如果未来增减工具，过滤逻辑自动适应，无需维护额外的白名单/黑名单。

**为什么在 save_response 中过滤？**

assistant 消息存入 DB 后，后续 LLM 调用会读取它。如果保留未知工具的 `tool_calls` 但不保存对应 `tool` role 结果，会违反 Moonshot 等 API 的格式要求（每个 `tool_call_id` 必须有对应 tool result）。因此必须在落库前过滤。

#### 4.1.2 `_build_llm_call_payload`（Step 2）— 注入 system warning

```python
def _build_llm_call_payload(ctx, prev_result):
    """Step 2: 调用 LLM（使用 Step 1 的结果）
    
    关键：如果 context 末尾是无 tool_calls 的 assistant 消息，
    说明上一轮 LLM 未调用工具。瞬态注入 system warning 到 messages，
    仅用于本次 LLM 调用，不写入 DB。
    """
    context = prev_result.get("context", [])
    messages = list(context)  # shallow copy，不修改原 context
    
    # 检测：末尾是无 tool_calls 的 assistant 消息 → 注入 warning
    if (messages 
        and messages[-1].get("role") == "assistant" 
        and not messages[-1].get("tool_calls")):
        messages.append({
            "role": "system",
            "content": NO_TOOL_WARNING,
        })
    
    return {
        "runtime_id": ctx["runtime_id"],
        "round_id": f"round-{ctx.get('round_num', 1)}",
        "messages": messages,
        "model": ctx.get("model", "gpt-4o"),
        "tools": ctx.get("tools", []),
        "agent_id": ctx.get("agent_id"),
        "subagent_id": ctx.get("subagent_id"),
    }
```

**注意**：`messages` 是 shallow copy，warning 只存在于传给 LLM 的 payload 中。`prev_result["context"]` 不受影响。

> **LLM 兼容性**：如果某些 LLM API（如 Moonshot）不支持对话中间的 `role: system`，可改为 `role: user` + `[系统提醒]` 前缀。当前使用的 GPT-4o 和 Moonshot v1 都支持 mid-conversation system messages。

#### 4.1.3 `_decide_and_build_actions`（Step 4）— 简化决策

决策函数基于 Step 3 **保存后**的 message 判断，此时未知工具已被过滤。

```python
def _decide_and_build_actions(ctx, results):
    """决策并构建分支路由

    返回布尔标志供 condition lambda 使用。
    
    重要：condition_ctx = {**prev_result, **context, "step_results": ...}
    context 中的同名 key 会覆盖 prev_result，因此使用 context 中不存在的
    独立 flag（has_tool_calls / should_retry / should_terminate）。
    
    注意：此处拿到的是 LLM 原始 response 中的 tool_calls，
    需要再次过滤未知工具（与 save_response 保持一致）。
    """
    call_llm_result = results.get("call_llm", {})
    response = call_llm_result.get("response", {})
    message = response.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls", [])
    
    runtime_id = ctx["runtime_id"]
    round_num = ctx.get("round_num", 1)
    no_tool_retry_count = ctx.get("no_tool_retry_count", 0)
    
    # 过滤不在工具列表中的 tool_calls（与 save_response 保持一致）
    known = _get_known_tool_names(ctx)
    tool_calls = [tc for tc in tool_calls 
                  if tc.get("function", {}).get("name") in known]
    
    if tool_calls:
        return {
            "has_tool_calls": True,
            "should_retry": False,
            "should_terminate": False,
            "tool_calls": tool_calls,
            "no_tool_retry_count": 0,
        }
    
    if no_tool_retry_count < 1:
        # 首次无工具：允许重试
        return {
            "has_tool_calls": False,
            "should_retry": True,
            "should_terminate": False,
            "tool_calls": [],
            "no_tool_retry_count": 1,
        }
    
    # 连续无工具：终止
    return {
        "has_tool_calls": False,
        "should_retry": False,
        "should_terminate": True,
        "tool_calls": [],
        "no_tool_retry_count": no_tool_retry_count,
    }
```

**关键：`condition_ctx` 覆盖陷阱**

saga 框架评估 condition 时构建的 context 为：

```python
condition_ctx = {**prev_result, **context, "step_results": step_results}
```

`context`（saga 创建时的 context）中的 key 会 **覆盖** `prev_result`（决策输出）中的同名 key。  
saga context 中已有 `no_tool_retry_count`、`runtime_id` 等字段，因此决策输出必须使用 **独立的 flag 名称**：

| Flag | 来源 | context 中是否存在 | 安全？ |
|------|------|-------------------|--------|
| `has_tool_calls` | 决策输出 | 否 | ✅ |
| `should_retry` | 决策输出 | 否 | ✅ |
| `should_terminate` | 决策输出 | 否 | ✅ |
| `no_tool_retry_count` | 决策输出 | ⚠️ 是（saga context 有） | ❌ 会被覆盖 |

因此 condition lambda **不能**用 `d.get("no_tool_retry_count")` 判断，必须用专用 flag。

#### 4.1.4 删除 `_normalize_tool_calls` 和 `REST_TOOL_ALIASES`

```python
# 删除
REST_TOOL_ALIASES = {"done", "final", "finish", "complete", "rest", "runtime_reset"}

# 删除
def _normalize_tool_calls(tool_calls, runtime_id, round_num):
    """将 done/final 等转换为 subagent_rest"""
    ...
```

**替代**：不在工具列表中的 tool_calls 在 `_build_save_response_payload` 和 `_decide_and_build_actions` 中用 `_get_known_tool_names(ctx)` 统一过滤。不维护任何硬编码的工具名黑名单/白名单，完全由运行时工具列表驱动。

```python
# 新增（辅助函数）
def _get_known_tool_names(ctx):
    """从 ctx["tools"] 中提取合法工具名集合"""
    tools = ctx.get("tools") or []
    return {t.get("function", {}).get("name") or t.get("name", "") for t in tools}
```

#### 4.1.5 新增 `_build_trigger_retry_think`

```python
def _build_trigger_retry_think(ctx, decision):
    """无 tool_calls + 可重试 → 直接触发下一轮 ReactThink（跳过 ReactActions）"""
    next_round = ctx.get("round_num", 1) + 1
    return {
        "saga_type": "react_think",
        "context": {
            "runtime_id": ctx["runtime_id"],
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "user_id": ctx.get("user_id", ""),
            "round_num": next_round,
            "no_tool_retry_count": 1,
            "model": ctx.get("model", "gpt-4o"),
            "tools": ctx.get("tools", []),
        },
        "idempotency_key": f"react-think-retry-{ctx['runtime_id']}-round{next_round}",
    }
```

#### 4.1.6 新增 `_build_trigger_terminate`

```python
def _build_trigger_terminate(ctx, decision):
    """连续无 tool_calls → 触发 RuntimeComplete（跳过 ReactActions）"""
    return {
        "saga_type": "runtime_complete",
        "context": {
            "runtime_id": ctx["runtime_id"],
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "user_id": ctx.get("user_id", ""),
        },
        "idempotency_key": f"runtime-complete-{ctx['runtime_id']}",
    }
```

**无需调用 rest API**：当前方案中 `subagent_rest` 设置 `need_rest=1` 只是为了让 ReactActions 的 `check_continue` 步骤识别"应该终止"。跳过 ReactActions 后不再需要这个信号。RuntimeComplete saga 的 `set_subagent_sleeping`（Step 4a）直接处理 subagent 终态。

#### 4.1.7 `round_num` 递增与幂等键安全性

当前架构中 `round_num` 由 ReactActions 递增（`_build_trigger_next_think_payload` 中 `next_round = round_num + 1`）。ReactThink 自身不递增。

跳过 ReactActions 的 retry 路径必须自己递增 `round_num`，否则两轮 ReactThink 会共享同一个 `save_response` 幂等键 `{runtime_id}-round{N}-response`，导致第二轮的 LLM 响应无法写入 DB。

**`_build_trigger_retry_think` 中 `next_round = round_num + 1` 是必须的。**

幂等键不会冲突的完整论证：

```
RT(round=1) — LLM 无工具:
  save_response  → "{id}-round1-response"
  trigger_retry  → "react-think-retry-{id}-round2"     ← 前缀 "retry-"

RT(round=2) — LLM 调用 shell:
  save_response  → "{id}-round2-response"               ← ≠ round1
  trigger_actions → "react-actions-{id}-round2"

RA(round=2):
  tool results   → "{id}-round2-{tool_call_id}"
  trigger_next   → "react-think-{id}-round3"            ← 前缀无 "retry-"
```

三类触发的幂等键前缀互不相同：
- 正常: `react-think-{id}-round{N}`
- 重试: `react-think-retry-{id}-round{N}`
- 终止: `runtime-complete-{id}`

且 5a/5b/5c 三分支 condition 互斥，同一 round 只会走一个。

#### 4.1.8 Saga 定义改造

```python
# 现在
# Step 5: 触发 ReactActions（总是执行）
REACT_THINK_SAGA.add_task_step(
    name="trigger_actions",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_actions_from_decision,
)

# 改为三个条件分支
# Step 5a: 有 tool_calls → 触发 ReactActions（正常路径）
REACT_THINK_SAGA.add_task_step(
    name="trigger_actions",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_actions_from_decision,
    condition=lambda d: d.get("has_tool_calls", False),
)

# Step 5b: 无 tool_calls + 可重试 → 直接触发下一轮 ReactThink
REACT_THINK_SAGA.add_task_step(
    name="trigger_retry_think",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_retry_think,
    condition=lambda d: d.get("should_retry", False),
)

# Step 5c: 连续无 tool_calls → 触发 RuntimeComplete
REACT_THINK_SAGA.add_task_step(
    name="trigger_terminate",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_terminate,
    condition=lambda d: d.get("should_terminate", False),
)
```

DAG 拓扑变化：

```
before:                              after:
  read_context                         read_context
       ↓                                    ↓
  call_llm                             call_llm
       ↓                                    ↓
  save_response                        save_response
       ↓                                    ↓
  decide_actions                       decide_actions
       ↓                               ┌────┼────┐
  trigger_actions                       ↓    ↓    ↓
  (always → react_actions)          5a: RA  5b: RT  5c: RC
                                   (tools) (retry) (terminate)
```

---

### 4.2 `tool_handlers.py` — 清理合成工具逻辑

#### 删除内容

1. **`_SYNTHETIC_SLEEP` 常量** — 不再需要（`sleep` 仍在 `_LIFECYCLE_TOOLS` 中处理真实调用）
2. **`_SYNTHETIC_REST` 常量** — 不再需要（幻影工具已在 saga 层剥离，不会到达 tool_handlers）
3. **rest 别名转换逻辑**（`if tool_name in _SYNTHETIC_REST`）— 删除  
4. **`no-tool-` 前缀检测逻辑**（`if tool_name == "subagent_send" and tool_call_id.startswith("no-tool-")`）— 删除

#### 保留内容

- `_LIFECYCLE_TOOLS` — 保留，处理 LLM 发出的真实生命周期工具调用
- `_CORTEX_TOOLS` — 保留
- `_handle_lifecycle_tool` — 保留全部
- `subagent_rest` 在 `_LIFECYCLE_TOOLS` 中 — 保留（LLM 仍可能主动调用 `subagent_rest`）

#### 变更后入口逻辑

```python
@register_handler(TaskTopics.TOOL_EXECUTE)
def handle_tool_execute(payload, ctx):
    # ... 字段校验 + 解析 ...

    # ── 1. Agent 生命周期工具 → Gateway API ──
    if tool_name in _LIFECYCLE_TOOLS:
        ...

    # ── 2. Cortex 工具: shell / skill_begin / skill_end ──
    if tool_name in _CORTEX_TOOLS:
        ...

    # ── 3. 未知工具 → 错误 ──
    ...
```

从 4 个分支简化为 3 个（删除合成工具分支）。

#### 未知工具不再到达 tool_handlers

不在工具列表中的工具名在 `react_think.py` 的 `_build_save_response_payload` 和 `_decide_and_build_actions` 中已被过滤。它们不会出现在 ReactActions 的 `tool_calls` 中，因此 tool_handlers 无需识别它们。

如果 LLM 返回 `[shell("ls"), done()]`，saga 层过滤 `done` 后只传递 `[shell("ls")]` 给 ReactActions。

---

### 4.3 `react_actions.py` — 清理合成工具结果处理

#### `_build_save_results_tasks` 中的无 `result_id` 分支

```python
# 现在
if result_id:
    message = {"role": "tool", "tool_call_id": ..., "result_id": result_id}
else:
    # 无 result_id（合成工具如 no-tool-warn）→ 直接存 content
    content = json.dumps({"success": True})
    message = {"role": "tool", "tool_call_id": ..., "content": content}
```

`else` 分支只为合成工具存在。重构后可以简化：**所有真实工具执行都应返回 `result_id`**。如果没有 `result_id`，视为异常并记录 warning。

```python
if not result_id:
    logger.warning(f"[react_actions] Tool {tool_call_id} returned no result_id, skipping save")
    continue
message = {"role": "tool", "tool_call_id": ..., "result_id": result_id}
```

---

### 4.4 `system_prompt.py` — 更新 warning 注释

```python
# BEFORE
# 无工具调用时的警告文案（用于 subagent_send 自发送，给 LLM 一次纠正机会）

# AFTER
# 无工具调用时的警告文案（作为 system message 瞬态注入 LLM 调用，不存入 DB）
```

`NO_TOOL_WARNING` 的内容不变，只更新注释。

---

## 5. 数据流对比

### 5.1 第 1 次 no-tool：Context 中的消息

**Before（合成工具）**:
```
[
  {"role": "user", "content": "你好"},
  {"role": "assistant", "content": "...", "tool_calls": [           ← 被修改
    {"id": "no-tool-warn-xxx", "function": {"name": "subagent_send", ...}},
    {"id": "no-tool-sleep-xxx", "function": {"name": "sleep", ...}}
  ]},
  {"role": "tool", "tool_call_id": "no-tool-warn-xxx", "content": "{\"success\":true}"},  ← 假结果
  {"role": "tool", "tool_call_id": "no-tool-sleep-xxx", "content": "{\"success\":true}"}, ← 假结果
  {"role": "assistant", "content": "...", "tool_calls": [...]},  ← 下一轮
]
```

**After（system message 注入）**:

DB 中存储的 context：
```
[
  {"role": "user", "content": "你好"},
  {"role": "assistant", "content": "..."},       ← 原样保存，无 tool_calls
  {"role": "assistant", "content": "...", ...},   ← 下一轮 LLM 响应
]
```

传给 LLM 的 messages（瞬态，不落库）：
```
[
  {"role": "user", "content": "你好"},
  {"role": "assistant", "content": "..."},
  {"role": "system", "content": "[系统] 你上一轮未调用任何工具..."},  ← 瞬态注入
]
```

### 5.2 第 2 次 no-tool：直接终止

**Before**: ReactActions 执行合成 `subagent_rest` → `need_rest=1` → RuntimeComplete  
**After**: ReactThink 直接触发 RuntimeComplete，不经过 ReactActions

---

## 6. 边界情况

### 6.1 用户在两轮之间发送新消息

- `context_read` handler 会将新的 user message append 到 context
- `_build_llm_call_payload` 检测到 `context[-1].role == "user"`（不是 assistant）
- **不会注入 warning** — 正确行为，新用户消息应正常处理

### 6.2 LLM Error 后的 no-tool

- `_build_save_response_payload` 生成 `{"role": "assistant", "content": "[LLM Error] ..."}`
- 无 `tool_calls` → 触发 retry 或 terminate
- Warning 注入到下一轮 → LLM 有机会恢复
- 合理行为，与当前一致

### 6.3 LLM 主动调用 `subagent_rest`（真实终止）

- `subagent_rest` 是真实工具（在 11-tool 模型中），不在 `PHANTOM_TOOL_NAMES` 中
- `_decide_and_build_actions` 检测到 `tool_calls` 非空 → `has_tool_calls=True`
- 走正常 ReactActions 路径
- `tool_handlers` 执行真实 `subagent_rest`
- 不受本次重构影响

### 6.4 LLM 返回不在工具列表中的工具名

**场景 A**：LLM 只返回未知工具（如 `[done()]`、`[browse("url")]`）

- `_build_save_response_payload` 过滤掉不在 `ctx["tools"]` 中的工具 → `tool_calls` 为空 → 删除 `tool_calls` 字段
- assistant 消息保存为纯文本
- `_decide_and_build_actions` 过滤后无有效工具 → `has_tool_calls=False`
- 走 no-tool 路径（retry 或 terminate）

**场景 B**：LLM 返回已知工具 + 未知工具混合（如 `[shell("ls"), done()]`）

- `_build_save_response_payload` 过滤掉 `done` → `tool_calls = [shell("ls")]`
- assistant 消息保存时只含 `shell`
- `_decide_and_build_actions` 过滤后有有效工具 → `has_tool_calls=True`
- ReactActions 只执行 `shell("ls")`，保存对应 tool result
- Context 结构完整（assistant.tool_calls 与 tool results 一一对应）

### 6.5 Moonshot API 对消息格式的要求

- Moonshot 要求：每个 `tool_calls` 中的 `tool_call_id` 必须有对应的 `tool` role 消息
- 重构后：assistant 消息无 `tool_calls` → 无 tool role 消息 → **完全合法**
- 只有当 assistant 消息有 `tool_calls` 时，才会进入 ReactActions 保存 tool results

### 6.6 `system` role 在对话中间的 LLM 兼容性

| LLM | 支持 mid-conversation system? |
|-----|------|
| GPT-4o / GPT-4.1 | ✅ |
| Claude | ✅ |
| Moonshot v1 | ✅（文档确认） |
| DeepSeek | ✅ |

如果未来遇到不支持的模型，可将 `role: system` 改为 `role: user` + `[系统提醒]` 前缀。改动局限于 `_build_llm_call_payload` 一个函数。

---

## 7. 影响范围

### 修改文件

| 文件 | 变更类型 | 描述 |
|------|---------|------|
| `novaic-agent-runtime/task_queue/sagas/react_think.py` | **重构** | 删除合成 tool_calls，新增三分支 + warning 注入 |
| `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` | **清理** | 删除 `_SYNTHETIC_REST`、`_SYNTHETIC_SLEEP`、`no-tool-` 检测 |
| `novaic-agent-runtime/task_queue/sagas/react_actions.py` | **清理** | 简化 `_build_save_results_tasks` 中无 `result_id` 分支 |
| `novaic-agent-runtime/task_queue/utils/system_prompt.py` | **注释** | 更新 `NO_TOOL_WARNING` 注释 |

### 不修改

| 文件 | 原因 |
|------|------|
| `saga.py` | 框架层不需要改动，`condition` 分支已支持 |
| `task_worker_sync.py` | 框架层不需要改动 |
| `runtime_complete.py` | 终止流程不变 |
| `context_handlers.py` | context 读写逻辑不变 |
| `novaic-cortex/` | Cortex 层不涉及 |
| `novaic-gateway/` | Gateway 层不涉及 |

---

## 8. 测试计划

### 8.1 手动测试

| 场景 | 操作 | 预期 |
|------|------|------|
| 正常对话 | 发送消息，LLM 调用 `chat_reply` | 正常回复，不触发 warning |
| 第 1 次 no-tool | 让 LLM 返回纯文本 | Context 中无假 tool_calls；下一轮 LLM 看到 system warning |
| Warning 后恢复 | 第 1 次 no-tool → LLM 纠正 → 调用工具 | 正常执行，retry count 重置 |
| 连续 2 次 no-tool | 让 LLM 连续返回纯文本 | RuntimeComplete 触发，agent 进入 sleeping |
| 用户插入消息 | 第 1 次 no-tool → 用户发新消息 → 下一轮 | 无 warning 注入，正常处理用户消息 |
| 主动 rest | LLM 调用 `subagent_rest` | 正常走 ReactActions → RuntimeComplete |
| 纯未知工具 | LLM 返回 `[done()]` | 过滤后视为 no-tool，走 retry 路径 |
| 混合工具 | LLM 返回 `[shell("ls"), finish()]` | 过滤 `finish`，只执行 `shell("ls")` |

### 8.2 日志验证

```bash
# 未知工具过滤: 应看到
[react_think] Filtered unknown tools: done, finish (N remaining known tools)

# 第 1 次 no-tool: 应看到
[react_think] No tool_calls, retry_count=0, triggering retry think

# 下一轮: 应看到
[react_think] Injecting NO_TOOL_WARNING system message (transient)

# 第 2 次 no-tool: 应看到
[react_think] No tool_calls, retry_count=1, triggering terminate

# 不应再看到
[tool_handlers] Synthetic no-op send: no-tool-*
[tool_handlers] Synthetic rest alias: done → subagent_rest
```

---

## 9. 实施步骤

```
Step 1: 修改 react_think.py
  ├── 1a. 新增 _get_known_tool_names()，删除 REST_TOOL_ALIASES
  ├── 1b. 重写 _build_save_response_payload（删除合成注入，新增未知工具过滤）
  ├── 1c. 修改 _build_llm_call_payload（添加 system warning 注入）
  ├── 1d. 重写 _decide_and_build_actions（过滤未知工具，返回布尔 flag）
  ├── 1e. 删除 _normalize_tool_calls（不再需要别名转换）
  ├── 1f. 新增 _build_trigger_retry_think
  ├── 1g. 新增 _build_trigger_terminate
  └── 1h. 修改 saga 定义（三分支）

Step 2: 清理 tool_handlers.py
  ├── 2a. 删除 _SYNTHETIC_SLEEP, _SYNTHETIC_REST
  ├── 2b. 删除 rest 别名转换
  └── 2c. 删除 no-tool- 前缀检测

Step 3: 清理 react_actions.py
  └── 3a. 简化 _build_save_results_tasks（删除无 result_id 兼容分支）

Step 4: 更新 system_prompt.py 注释

Step 5: 本地测试 → 部署 → 线上验证
```

---

## 10. 回滚方案

所有改动限于 `novaic-agent-runtime` 仓库，回滚方式：

```bash
cd novaic-agent-runtime
git revert <commit-hash>
# 重新部署
```

合成工具逻辑是自包含的（不依赖外部状态），回滚后立即生效，无数据迁移需求。
