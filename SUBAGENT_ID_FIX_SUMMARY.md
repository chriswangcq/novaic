# Subagent ID 一致性修复总结

## 问题描述

在之前的实现中，`think` 和 `tool` 事件在执行日志中的 `subagent_id` 不一致：
- **Think 事件**：正确使用了从 saga context 传递的 `subagent_id`
- **Tool 事件**：从 runtime API 实时查询 `subagent_id`，可能与 think 事件不一致

这导致前端执行日志无法正确按 subagent 分组显示，用户体验不佳。

## 解决方案

采用**推荐方案 A**：在 Saga 层传递 `subagent_id`，确保同一轮的 think 和 tool 事件使用相同的 `subagent_id`。

## 修改内容

### 1. ReactActions Saga (`react_actions.py`)

**位置**：`_build_tool_execute_tasks` 函数（第 30-51 行）

**修改**：
- 从 saga context 获取 `subagent_id`（默认值为 "main"）
- 将 `subagent_id` 添加到每个 `tool.execute` 任务的 payload 中

```python
def _build_tool_execute_tasks(ctx):
    """构建并行 tool.execute 任务"""
    tool_calls = ctx.get("tool_calls", [])
    runtime_id = ctx["runtime_id"]
    round_num = ctx.get("round_num", 1)
    agent_id = ctx.get("agent_id")
    subagent_id = ctx.get("subagent_id", "main")  # ✅ 新增
    
    return [
        {
            "topic": TaskTopics.TOOL_EXECUTE,
            "payload": {
                "runtime_id": runtime_id,
                "agent_id": agent_id,
                "subagent_id": subagent_id,  # ✅ 新增
                "round_id": f"round-{round_num}",
                "tool_call_id": tc.get("id"),
                "tool_name": tc.get("function", {}).get("name"),
                "arguments": tc.get("function", {}).get("arguments", "{}"),
            },
        }
        for tc in tool_calls
    ]
```

### 2. Tool Handler (`tool_handlers.py`)

**位置**：`handle_tool_execute` 函数开头（第 44-71 行）

**修改**：
- 优先从 payload 获取 `subagent_id`
- 如果 payload 中没有，从 runtime API 获取（向后兼容）
- 添加日志记录，便于调试

```python
# ✅ 修改：优先从 payload 获取
agent_id = payload.get("agent_id")
subagent_id = payload.get("subagent_id")  # 优先从 payload 获取

# 解析 arguments
if isinstance(arguments, str):
    try:
        arguments = json.loads(arguments)
    except json.JSONDecodeError:
        pass

# 如果 payload 中没有，从 runtime 获取（兼容旧逻辑）
if not subagent_id or not agent_id:
    from ..client import GatewayInternalClient
    import logging
    
    gateway_url = ctx.get("gateway_url")
    client = ctx.get("gateway_client") or GatewayInternalClient(gateway_url)
    
    try:
        runtime = client.get_runtime(runtime_id)
        if not runtime:
            logging.warning(
                f"[tool_handlers] Runtime not found: {runtime_id}, "
                f"using defaults (agent_id={agent_id}, subagent_id={subagent_id or 'main'})"
            )
            subagent_id = subagent_id or "main"
        else:
            if not subagent_id:
                subagent_id = runtime.get("subagent_id", "main")
            if not agent_id:
                agent_id = runtime.get("agent_id")
    except Exception as e:
        logging.error(
            f"[tool_handlers] Failed to get runtime {runtime_id}: {e}, "
            f"using defaults (agent_id={agent_id}, subagent_id={subagent_id or 'main'})"
        )
        subagent_id = subagent_id or "main"
else:
    # Payload 中已有完整信息，记录日志（可选）
    import logging
    logging.debug(f"[tool_handlers] Using subagent_id from payload: {subagent_id}")
```

### 3. 单元测试

**文件**：`tests/unit/task_queue/test_subagent_id_consistency.py`（新建）

创建了两个测试用例：
1. `test_react_actions_passes_subagent_id`：验证 saga 正确传递 subagent_id
2. `test_react_actions_uses_default_subagent_id`：验证默认值为 "main"

**测试结果**：✅ 所有测试通过

### 4. 验证脚本

**文件**：`scripts/verify_subagent_id_fix.sql`（新建）

提供了 SQL 查询脚本，用于在数据库中验证修复效果：
- 查看最近的 think 和 tool 事件
- 检查同一个 runtime 的事件是否有一致的 subagent_id
- 查找可能的不一致情况

## 兼容性说明

### 向前兼容
- 旧的执行日志数据不会改变
- 新的对话会正确记录一致的 `subagent_id`

### 向后兼容
- Tool handler 保持向后兼容性
- 如果 payload 中没有 `subagent_id`（旧版本 saga），仍会从 runtime API 获取
- 不会破坏现有功能

## 验证步骤

### 1. 单元测试（已完成）

```bash
cd novaic-backend
PYTHONPATH=/Users/wangchaoqun/novaic/novaic-backend python tests/unit/task_queue/test_subagent_id_consistency.py
```

结果：✅ 所有测试通过

### 2. 代码检查（已完成）

- ✅ 无 linter 错误
- ✅ 语法检查通过

### 3. 数据库验证（待用户执行）

启动应用后，创建新的对话并执行工具调用，然后运行：

```bash
sqlite3 <your-database-path> < novaic-backend/scripts/verify_subagent_id_fix.sql
```

预期结果：
- 同一个 runtime 的 think 和 tool 事件有相同的 `subagent_id`
- 执行日志按 subagent 正确分组显示

### 4. 前端验证（待用户执行）

1. 启动应用
2. 创建新的对话
3. 发送需要调用工具的消息（如 "帮我查看当前目录"）
4. 打开执行日志
5. 验证同一轮的 think 和 tool 事件显示在同一个 subagent 下
6. 检查事件时间线是否连贯

## 修改文件清单

- ✅ `novaic-backend/task_queue/sagas/react_actions.py`
- ✅ `novaic-backend/task_queue/handlers/tool_handlers.py`
- ✅ `novaic-backend/tests/unit/task_queue/test_subagent_id_consistency.py`（新建）
- ✅ `novaic-backend/scripts/verify_subagent_id_fix.sql`（新建）
- ✅ `SUBAGENT_ID_FIX_SUMMARY.md`（本文件）

## 成功标志

修复成功的标志：
- ✅ 单元测试全部通过
- ✅ 无 linter 错误
- ⏳ 新创建的对话中，think 和 tool 事件的 `subagent_id` 一致（待验证）
- ⏳ 前端执行日志按 subagent 正确分组显示（待验证）
- ⏳ 没有引入新的错误或回归（待验证）

## 后续建议

1. **监控日志**：观察 tool_handlers 中的日志，确认大部分请求都从 payload 获取 subagent_id
2. **数据清理**（可选）：如果旧数据影响用户体验，可以考虑：
   - 重新计算旧执行日志的 subagent_id
   - 或者在前端添加过滤，只显示修复后的数据
3. **文档更新**：更新 saga 开发文档，说明传递 subagent_id 的最佳实践

## 技术债务

- 考虑在其他 saga 中也采用类似的模式（在 saga 层传递完整的上下文信息）
- 评估是否需要在所有 handler 中优先从 payload 获取参数，减少对 runtime API 的依赖

## 日期

- 修复日期：2026-02-05
- 作者：AI Assistant (Claude Sonnet 4.5)
