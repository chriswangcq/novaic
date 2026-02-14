# Saga 与 SubAgent 调试经验

> 基于 2026-02-13 SubAgent 通信机制调试与 subagent_report 工具开发的实战经验总结

## 目录

1. [消息驱动架构调试方法](#1-消息驱动架构调试方法)
2. [Watchdog 消息处理排查](#2-watchdog-消息处理排查)
3. [SubAgent 通信机制](#3-subagent-通信机制)
4. [工具开发最佳实践](#4-工具开发最佳实践)
5. [端到端测试方法](#5-端到端测试方法)

---

## 1. 消息驱动架构调试方法

### 核心数据流

```
用户消息 → chat_messages (status=sending)
    ↓
Watchdog 检测 → 创建 message_process Saga
    ↓
message_process → route_message → get_or_create_runtime
    ↓
runtime_start Saga → react_think → react_actions (循环)
    ↓
runtime_complete → notify_parent (如果是 Sub SubAgent)
    ↓
SUBAGENT_COMPLETED 消息 → Watchdog → 唤醒 Parent
```

### 调试关键点

**消息状态流转**：
```
sending → sent (被 Watchdog 处理后)
```

**如果消息卡在 `sending`**：
- Watchdog 没有运行
- Watchdog 不识别该消息类型

**如果消息是 `sent` 但没有 Saga**：
- Watchdog 处理了消息但跳过了（Unknown message type）
- Saga 创建失败

### 常用调试命令

```bash
DB_PATH="/Users/wangchaoqun/Library/Application Support/com.novaic.app/novaic.db"
QUEUE_DB="/Users/wangchaoqun/Library/Application Support/com.novaic.app/queue.db"

# 查看消息状态
sqlite3 "$DB_PATH" "SELECT id, type, status, read FROM chat_messages ORDER BY created_at DESC LIMIT 10;"

# 查看 Saga 状态
sqlite3 "$QUEUE_DB" "SELECT id, saga_type, status, current_step FROM tq_sagas ORDER BY created_at DESC LIMIT 10;"

# 查看 SubAgent 状态
sqlite3 "$DB_PATH" "SELECT subagent_id, type, status, substr(result, 1, 100) FROM subagents ORDER BY created_at DESC LIMIT 5;"

# 查看 Runtime 状态
sqlite3 "$DB_PATH" "SELECT runtime_id, subagent_id, status FROM agent_runtimes ORDER BY created_at DESC LIMIT 5;"

# 查看 Watchdog 日志
tail -50 /tmp/watchdog.log
```

---

## 2. Watchdog 消息处理排查

### 问题案例：SUBAGENT_COMPLETED 消息不触发唤醒

**现象**：
- Sub SubAgent 完成后发送了 SUBAGENT_COMPLETED 消息
- 消息状态变成 `sent`
- 但 Main Agent 没有被唤醒

**诊断步骤**：

#### 步骤 1：检查消息状态
```bash
sqlite3 "$DB_PATH" "SELECT id, type, status FROM chat_messages WHERE type = 'SUBAGENT_COMPLETED' ORDER BY created_at DESC LIMIT 3;"
```

如果状态是 `sent`，说明 Watchdog 处理了消息。

#### 步骤 2：检查 Watchdog 日志
```bash
tail -100 /tmp/watchdog.log | grep -i "SUBAGENT_COMPLETED"
```

**关键日志**：
```
[watchdog] Found message xxx (type=SUBAGENT_COMPLETED, agent=xxx)
[watchdog] Unknown message type, skipping: SUBAGENT_COMPLETED  ← 问题！
```

#### 步骤 3：检查 Watchdog 代码

文件：`task_queue/workers/watchdog.py`

```python
def _create_saga_for_message(self, message):
    msg_type = message.get("type")
    
    if msg_type == "USER_MESSAGE":
        self._create_message_process_saga(...)
    elif msg_type == "SYSTEM_WAKE":
        self._create_message_process_saga(...)
    elif msg_type == "SPAWN_SUBAGENT":
        self._create_spawn_subagent_saga(...)
    # ❌ 缺少 SUBAGENT_COMPLETED 处理
    else:
        self._log(f"Unknown message type, skipping: {msg_type}")
```

**根因**：Watchdog 没有处理 `SUBAGENT_COMPLETED` 消息类型。

#### 步骤 4：修复

添加 `SUBAGENT_COMPLETED` 处理：

```python
elif msg_type == "SUBAGENT_COMPLETED":
    self._create_subagent_completed_saga(msg_id, agent_id, metadata)
```

### 教训

**新增消息类型时的 Checklist**：
- [ ] 在 Watchdog 中添加消息类型处理
- [ ] 在 `create_message` API 中设置正确的初始状态（`sending` vs `sent`）
- [ ] 测试完整的消息流转

### 消息初始状态设计

```python
# 需要 Watchdog 处理的消息类型 → status="sending"
watchdog_types = {"USER_MESSAGE", "SYSTEM_WAKE", "SPAWN_SUBAGENT", "SUBAGENT_COMPLETED"}

# Agent 回复等 → status="sent"（直接跳过 Watchdog）
other_types = {"AGENT_REPLY", "AGENT_ASK", "AGENT_NOTIFY"}
```

---

## 3. SubAgent 通信机制

### 架构概述

```
Main SubAgent (main-xxx)
    ↓ subagent_spawn
Sub SubAgent (sub-xxx)
    ↓ 执行任务
    ↓ subagent_report (主动汇报结果)
    ↓ runtime_complete
    ↓ notify_parent
SUBAGENT_COMPLETED 消息
    ↓ Watchdog
Main SubAgent 被唤醒
    ↓ subagent_query
获取 Sub 的结果
```

### 关键组件

| 组件 | 职责 |
|------|------|
| `subagent_spawn` | Main 创建 Sub，传入任务描述 |
| `subagent_report` | Sub 主动汇报执行结果 |
| `subagent_query` | Main 查询 Sub 的状态和结果 |
| `runtime_complete` | Sub 完成时触发，发送通知 |
| `SUBAGENT_COMPLETED` | 通知消息，触发 Main 唤醒 |

### Result 写入机制

**旧方案**（自动写入）：
```
runtime_complete Saga
    ↓ generate_simple_summary
    ↓ set_subagent_completed (写入 result)
```

问题：result 是系统生成的摘要，不是 Agent 主动汇报的内容。

**新方案**（工具调用）：
```
Sub SubAgent 执行任务
    ↓ subagent_report 工具 (主动写入 result)
    ↓ runtime_complete
    ↓ set_subagent_completed (不覆盖已有 result)
```

优势：
- Agent 可以控制汇报内容
- 结果更有针对性
- 保留兜底逻辑（如果没调用 subagent_report，仍用 simple_summary）

---

## 4. 工具开发最佳实践

### 案例：subagent_report 工具

#### 需求分析

**目标**：让 Sub SubAgent 主动汇报执行结果，而不是依赖系统自动生成。

**设计决策**：

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 调用者限制 | 仅 Sub SubAgent | Main 没有 result 概念 |
| 写入方式 | 覆盖 | result 是最终结论，不需要追加 |
| 是否触发通知 | 否 | 通知由 runtime_complete 统一处理 |
| 兜底逻辑 | 保留 | 如果 Agent 没调用，仍用 simple_summary |

#### 实现步骤

**1. Gateway 层**

添加 Repository 方法：
```python
# gateway/db/repositories/subagent.py
def update_result(self, subagent_id: str, agent_id: str, result: str):
    """Update SubAgent result without changing status."""
    now = utc_now_iso()
    with self.db.get_connection("agent", resource_id=agent_id) as conn:
        conn.execute("""
            UPDATE subagents 
            SET result = ?, updated_at = ?
            WHERE subagent_id = ? AND agent_id = ?
        """, (result, now, subagent_id, agent_id))
        conn.commit()
```

添加 API 端点：
```python
# gateway/api/internal/runtime.py
@router.post("/rt/{runtime_id}/subagent/report")
def rt_subagent_report(runtime_id: str, data: Dict[str, Any]):
    # 1. 解析 runtime_id 获取 agent_id, subagent_id
    # 2. 校验是 Sub SubAgent
    # 3. 调用 repo.update_result()
```

**2. Tools Server 层**

添加工具 schema：
```python
# tools_server/tools.py
{
    "name": "subagent_report",
    "description": "Report the execution result of current SubAgent task.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "result": {
                "type": "string",
                "description": "The execution result to report"
            }
        },
        "required": ["result"]
    }
}
```

实现执行逻辑：
```python
# tools_server/executor.py
elif tool_name == "subagent_report":
    # 校验是 Sub SubAgent
    if not self.subagent_id or not self.subagent_id.startswith("sub-"):
        return {"success": False, "error": "Only available for Sub SubAgents"}
    
    result = arguments.get("result")
    response = await client.post(
        f"/internal/rt/{self.runtime_id}/subagent/report",
        json={"result": result}
    )
    return self._handle_response(response)
```

**3. System Prompt**

在 Sub SubAgent 的 prompt 中添加指引：
```python
# task_queue/utils/system_prompt.py
if subagent_id and subagent_id.startswith("sub-"):
    prompt += """
## 子任务执行要求

你是一个子 Agent，正在执行父 Agent 分配的任务。

**重要**：在完成任务前，你必须调用 `subagent_report` 工具来汇报你的执行结果。

汇报内容应包括：
- 任务执行的关键发现
- 最终结论或答案
- 如有必要，说明遇到的问题或限制
"""
```

**4. 兜底逻辑**

修改 `set_subagent_completed` API，不覆盖已有 result：
```python
# gateway/api/internal/subagent.py
def set_subagent_completed(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    # 检查是否已有 result
    existing = repo.get_by_id(subagent_id, agent_id)
    if existing and existing.result:
        # 已有 result（来自 subagent_report），不覆盖
        result_to_use = existing.result
    else:
        # 使用 payload 中的 result（兜底）
        result_to_use = data.get("result")
    
    repo.set_completed(subagent_id, agent_id, result=result_to_use)
```

---

## 5. 端到端测试方法

### 测试流程

```bash
# 1. 清理测试数据
DB_PATH="/Users/wangchaoqun/Library/Application Support/com.novaic.app/novaic.db"
QUEUE_DB="/Users/wangchaoqun/Library/Application Support/com.novaic.app/queue.db"

sqlite3 "$QUEUE_DB" "DELETE FROM tq_sagas; DELETE FROM tq_tasks;"
sqlite3 "$DB_PATH" "UPDATE agent_runtimes SET status = 'completed' WHERE status = 'active';"
sqlite3 "$DB_PATH" "UPDATE subagents SET status = 'sleeping' WHERE status IN ('awake', 'completed');"

# 2. 重启服务
pkill -f "main_gateway.py"
pkill -f "main_watchdog.py"
pkill -f "tools_server"
# 然后重新启动

# 3. 发送测试消息
curl -s -X POST "http://localhost:19999/internal/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "xxx",
    "type": "USER_MESSAGE",
    "content": "请创建一个子任务来计算 1+1，使用 subagent_spawn 工具"
  }'

# 4. 监控执行
watch -n 2 'sqlite3 "$QUEUE_DB" "SELECT saga_type, status FROM tq_sagas ORDER BY created_at DESC LIMIT 10;"'

# 5. 验证结果
sqlite3 "$DB_PATH" "SELECT subagent_id, status, substr(result, 1, 200) FROM subagents WHERE type = 'sub' ORDER BY created_at DESC LIMIT 1;"
```

### 验证点

| 验证项 | 命令 | 预期结果 |
|--------|------|----------|
| Sub 调用 subagent_report | 查看 Runtime context | 有 tool_call: subagent_report |
| result 正确写入 | 查看 subagents.result | 包含 Agent 汇报的内容 |
| Main 收到通知 | 查看 SUBAGENT_COMPLETED 消息 | status=sent, read=1 |
| Main 调用 query | 查看 Main Runtime context | 有 tool_call: subagent_query |

### 常见问题排查

| 问题 | 可能原因 | 排查方法 |
|------|---------|---------|
| Sub 没调用 subagent_report | System prompt 没传递 subagent_id | 检查 build_system_prompt 调用 |
| result 是 simple_summary | subagent_report 调用失败 | 查看 Sub Runtime context |
| Main 没被唤醒 | Watchdog 不处理 SUBAGENT_COMPLETED | 查看 Watchdog 日志 |
| Main 没读到结果 | subagent_query 失败 | 查看 Main Runtime context |

---

## 总结

### 调试核心原则

1. **追踪消息流转**：消息状态（sending → sent）是关键线索
2. **检查 Watchdog 日志**：Unknown message type 是常见问题
3. **验证 Saga 创建**：消息处理后应该有对应的 Saga
4. **查看 Runtime context**：tool_call 和 tool_result 记录了执行过程

### 新增消息类型 Checklist

- [ ] Watchdog 添加消息类型处理
- [ ] create_message API 设置正确的初始状态
- [ ] 测试消息 → Saga → 执行的完整流程

### 工具开发 Checklist

- [ ] Gateway API 端点
- [ ] Repository 方法
- [ ] Tools Server schema
- [ ] Tools Server executor
- [ ] System Prompt 指引（如需要）
- [ ] 端到端测试

---

*最后更新：2026-02-13*
*案例：SubAgent 通信机制调试与 subagent_report 工具开发*
