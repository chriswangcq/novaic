# Context Assembly: DFS Step Tree

> **状态**: 已实现  
> **日期**: 2026-04-06  
> **范围**: `novaic-cortex/novaic_cortex/context_stack/` + Cortex API + agent-runtime 上下文拼装

---

## 一、核心思想

**上下文的原子单位是 step，不是 message。**

Scope 内部是一棵 step tree。`skill_begin` / `skill_end` 形成复合节点（子树），
其余工具调用（`shell`、`chat_reply` 等）是叶子节点。
拼装 LLM 上下文时，对 step tree 做 **DFS 遍历**，遇到**闭合**的复合节点输出其
summary/report 并**跳过子树**，遇到**打开**的复合节点**继续展开**。

这同一规则统一了两个场景：
- **Active context（当前对话）**: 闭合 skill → fold to report；打开 skill → 展开 steps
- **Recall（历史记忆）**: 归档 scope 全部闭合 → 每个 root scope 只输出 summary

---

## 二、数据模型

### 2.1 Scope 目录结构（已有，不变）

```
/ro/active/{scope_id}/                    ← Cortex 管理区 (agent 只读)
  meta.json              # {name, skill, phase, start_time, ...}
  summary.md             # 闭合时写入
  context.jsonl          # 系统/用户消息流 (system prompt, user messages)
  steps/
    _index.jsonl         # step 索引 (seq, type, id, status, tool, file)
    0000_tool_tc001.json # 叶子 step: shell
    0001_tool_tc002.json # 叶子 step: chat_reply
    0002_scope_skill-xyz/ # 复合 step: skill_begin 创建的子 scope
      meta.json          # {name, skill, phase: "archived", ...}
      summary.md         # skill_end report
      context.jsonl      # 子 scope 内的 system/user 消息
      steps/
        _index.jsonl
        0000_tool_tc003.json
        0001_tool_tc004.json
    0003_tool_tc005.json # 叶子 step: 回到父 scope

/ro/scopes/{scope_id}/                    ← 归档 scope (结构同上)
/rw/scratch/                              ← Agent 自由空间
```

### 2.2 Step 类型

| type    | 存储形式           | 叶子/复合 | 说明                                    |
|---------|--------------------|-----------|-----------------------------------------|
| `tool`  | `NNNN_tool_ID.json`| 叶子      | 工具调用+结果 (shell, chat_reply, sleep…)|
| `scope` | `NNNN_scope_ID/`   | 复合      | skill_begin 创建的子 scope 目录          |

### 2.3 StepNode 内存表示

```python
@dataclass
class StepNode:
    seq: int              # 在父 scope 中的顺序号
    step_type: str        # "tool" | "scope"
    step_id: str          # tool_call_id 或 child scope_id
    closed: bool          # scope 是否已闭合 (tool 永远 True)

    # 叶子 step (tool)
    tool_name: str = ""   # "shell", "chat_reply", ...
    tool_args: dict = {}  # 工具参数
    tool_result: str = "" # 工具返回内容

    # 复合 step (scope)
    scope_name: str = ""  # skill name
    scope_summary: str = ""  # skill_end report / summary.md
    children: list["StepNode"] = []  # 子 step tree

    # 公共
    timestamp: float = 0
```

---

## 三、DFS 遍历算法

### 3.1 核心规则

```
DFS(node):
  if node.type == "tool":
    yield tool_message(node)      # 叶子: 直接输出为 tool message
  elif node.type == "scope":
    if node.closed:
      yield fold_message(node)    # 闭合复合: 输出 summary, 跳过子树
    else:
      yield scope_header(node)    # 打开复合: 输出 scope header
      for child in node.children:
        yield* DFS(child)         # 递归展开子节点
```

### 3.2 消息生成规则

| Step 类型       | 状态   | 生成的 message                                                |
|-----------------|--------|---------------------------------------------------------------|
| tool (叶子)     | —      | `{role: "assistant", tool_calls: [...]}` + `{role: "tool", content: result}` |
| scope (复合)    | closed | `{role: "system", content: "[Skill '{name}' completed]\n{summary}"}` |
| scope (复合)    | open   | `{role: "system", content: "[Skill '{name}' active]"}` + 递归展开 children |

### 3.3 完整示例

**Step Tree:**
```
root scope (open)
  ├── step-0: tool shell("ls")        → result: "file1\nfile2"
  ├── step-1: scope web-dev (closed, report="Built landing page")
  │     ├── step-1.0: tool shell("mkdir app")
  │     ├── step-1.1: tool shell("vim index.html")
  │     └── step-1.2: (skill_end)
  ├── step-2: tool chat_reply("页面做好了")
  ├── step-3: scope debugging (open)
  │     ├── step-3.0: tool shell("cat error.log")
  │     └── (still active...)
```

**DFS 输出 messages[]:**
```
1. [assistant] tool_call: shell("ls")
2. [tool] "file1\nfile2"
3. [system] [Skill 'web-dev' completed]      ← closed, 不展开 1.0/1.1/1.2
            Built landing page
4. [assistant] tool_call: chat_reply("页面做好了")
5. [tool] {"success": true}
6. [system] [Skill 'debugging' active]       ← open, 继续展开
7.   [assistant] tool_call: shell("cat error.log")
8.   [tool] "Error: connection refused..."
```

### 3.4 Recall (归档 scope) 的 DFS

归档 scope 的 root 是 closed 状态：
```
DFS(archived_root):
  → node.closed == True
  → yield fold_message(archived_root)  # 只输出 summary.md，不展开任何子 step
```

因此每个归档 scope 产出恰好 **一条** system message。

---

## 四、与现有架构的集成

### 4.1 context.jsonl 的角色变化

| 之前 | 之后 |
|------|------|
| context.jsonl 是消息权威源 | context.jsonl 存放 **非 step 消息** (system prompt, user messages, recall) |
| prepare_llm_context 读 context.jsonl | prepare_for_llm = context.jsonl 消息 + DFS(step tree) 合并 |
| tool 结果存 context.jsonl | tool 结果存 steps/ (已有)，不再重复写入 context.jsonl |

**context.jsonl 保留的内容：**
- System prompt (第一条)
- Recall memory messages
- User messages (来自 Gateway)
- Stack snapshot messages (ContextEngine 写入)

**context.jsonl 不再包含的内容：**
- Assistant messages with tool_calls (由 step tree 重建)
- Tool result messages (由 step tree 重建)
- skill_begin/skill_end 的 tool call/result (由 step tree 结构隐含)

### 4.2 写入流（react_think → react_actions）

**react_think (LLM 调用后):**
1. LLM 返回 assistant message (可能含 tool_calls)
2. 写入 context.jsonl: assistant message (含 tool_calls 信息)
3. → 交给 react_actions

**react_actions (工具执行后):**
1. 并行执行所有 tool_calls
2. 每个 tool result → `workspace.write_step(scope_path, step_data)`
3. **不再** 把 tool result 写入 context.jsonl
4. 如果是 `skill_begin` → `workspace.create_scope(parent_path=scope_path)`
5. 如果是 `skill_end` → `workspace.complete_child_scope(scope_path, report)`

### 4.3 读取流（prepare_for_llm）

```python
async def prepare_for_llm(scope_id):
    scope_path = f"/ro/active/{scope_id}"

    # 1. 读 context.jsonl (system prompt + user messages + recall)
    base_messages = await workspace.read_context(scope_path)

    # 2. 构建 step tree
    tree = await StepTreeBuilder.build(workspace, scope_path)

    # 3. DFS 遍历生成 step messages
    step_messages = tree.render_dfs()

    # 4. 合并: base_messages + step_messages
    # 交错策略: assistant message 在 context.jsonl 中有序号，
    # step messages 按 seq 插入到对应位置
    messages = merge_context_and_steps(base_messages, step_messages)

    # 5. Budget compact (Phase B)
    messages = budget_compact(messages, config)

    return messages
```

### 4.4 assistant message 的处理

LLM 返回的 assistant message 包含 tool_calls，这些需要和 step tree 的 tool results
配对。方案：

**assistant message 写入 context.jsonl + round_num 标记：**
```json
{"role": "assistant", "content": "...", "tool_calls": [...], "_round": 3}
```

**step index 也记录 round_num：**
```json
{"seq": 5, "type": "tool", "id": "tc001", "tool": "shell", "round": 3}
```

prepare_for_llm 时：
1. 读 context.jsonl，按 _round 分组
2. 每个 round 的 assistant message 后面，插入该 round 的 step messages (DFS)
3. user messages 插在 assistant 之前

---

## 五、Recall 与历史记忆

### 5.1 session_init 中的 Recall

```python
# handle_session_init:
recall_messages = []
for archived_scope in all_archived_root_scopes:
    summary = read_summary(archived_scope)
    recall_messages.append({
        "role": "system",
        "content": f"[Memory: {scope_label}]\n{summary}",
        "_metadata": {"origin": "recall", "scope_id": sid},
    })

# 写入 context.jsonl
context = [system_prompt] + recall_messages
bridge.append_context_batch(scope_id, context)
```

### 5.2 如果需要展开历史 scope 的 steps

Agent 可通过 `novaic read /ro/scopes/{sid}/steps/_index.jsonl` 自行浏览。
系统只注入 summary level 的 fold message，不自动展开。

---

## 六、文件改动清单

### Cortex 侧 (novaic-cortex)

| 文件 | 改动 |
|------|------|
| `context_stack/step_tree.py` | **新建**: StepNode, StepTree, StepTreeBuilder, DFS renderer |
| `context_stack/engine.py` | **重写**: prepare_messages_for_llm 基于 step tree |
| `api.py` | **更新**: /v1/context/prepare_for_llm 走 step tree |
| `workspace.py` | **确认**: write_step, list_steps, create_scope 已满足 |

### Agent-Runtime 侧 (novaic-agent-runtime)

| 文件 | 改动 |
|------|------|
| `sagas/react_actions.py` | **更新**: save_results 改为 write_step (不写 context.jsonl) |
| `sagas/react_think.py` | **更新**: assistant message 写入时附带 _round |
| `handlers/cortex_handlers.py` | **更新**: prepare_llm_context 走新路径 |
| `handlers/tool_handlers.py` | **更新**: skill_begin → create_scope, skill_end → complete_child_scope |
| `handlers/context_handlers.py` | **更新**: context_append 不再接收 tool results |

---

## 七、迁移策略

1. **Phase 1**: 实现 StepTreeBuilder + DFS renderer，prepare_for_llm 优先从 step tree 读取
2. **Phase 2**: react_actions 改为 write_step，不再写 context.jsonl tool results
3. **Phase 3**: 清理 context.jsonl 中的冗余 tool result 数据

Phase 1 和 Phase 2 可以同时进行，因为 step tree 构建已经能处理两种数据源。

---

## 八、关键约束

1. **DFS 序 = 时间序**: step 的 seq 编号保证 DFS 遍历顺序与执行时间顺序一致
2. **闭合判定**: scope type step 的 `meta.json.phase == "archived"` 表示闭合
3. **summary 来源**: 闭合 scope 的 fold 内容来自 `summary.md`（由 skill_end report 写入）
4. **tool result 不重复**: 同一 tool result 只存一处（steps/ 目录），不同时存 context.jsonl
5. **context.jsonl 瘦身**: 只保留 system prompt, user messages, recall messages, assistant messages
