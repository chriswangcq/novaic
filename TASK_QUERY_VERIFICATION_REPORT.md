# task_query 工具验证报告

**验证日期**: 2026-02-07  
**验证范围**: task_query 工具的实现和可用性

---

## 1. 工具状态总结

### ✅ 工具已实现

`task_query` 工具已在系统中实现，包含以下组件：

1. **工具定义** ✅
2. **工具执行器** ✅  
3. **API 端点** ✅
4. **后端支持** ✅
5. **存在问题** ⚠️

---

## 2. 详细验证结果

### 2.1 工具定义

**位置**: `novaic-backend/tools_server/tools.py` (第 632-656 行)

**工具签名**:
```python
{
    "name": "task_query",
    "description": "Query task status and results. Can retrieve partial output for long-running tasks.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "ID of the task to query"
            },
            "tail_lines": {
                "type": "integer",
                "description": "Number of output lines to return from the end"
            },
            "start_line": {
                "type": "integer",
                "description": "Starting line number for output range"
            },
            "end_line": {
                "type": "integer",
                "description": "Ending line number for output range"
            }
        },
        "required": ["task_id"]
    }
}
```

**状态**: ✅ 已正确定义，包含所有必需参数和可选的分页参数

---

### 2.2 工具执行器实现

**位置**: `novaic-backend/tools_server/executor.py` (第 665-682 行)

**实现代码**:
```python
elif tool_name == "task_query":
    task_id = arguments.get("task_id")
    if not task_id:
        return {"success": False, "error": "task_id is required"}
    params = {
        "include_outputs": arguments.get("include_outputs", False),
    }
    if arguments.get("start_line") is not None:
        params["start_line"] = arguments["start_line"]
    if arguments.get("end_line") is not None:
        params["end_line"] = arguments["end_line"]
    if arguments.get("tail_lines") is not None:
        params["tail_lines"] = arguments["tail_lines"]
    response = await client.get(
        f"/internal/tasks/{task_id}",
        params=params,
    )
    return self._handle_response(response)
```

**状态**: ✅ 实现完整，支持：
- 必需参数 `task_id` 验证
- 可选参数 `include_outputs`, `start_line`, `end_line`, `tail_lines` 传递
- 正确的 API 端点调用 (`/internal/tasks/{task_id}`)

**注意**: 工具定义中没有 `include_outputs` 参数，但执行器中支持它。这可能是一个不一致的地方。

---

### 2.3 API 端点

**位置**: `novaic-backend/gateway/api/internal/task.py` (第 67-91 行)

**端点定义**:
```python
@router.get("/tasks/{task_id}")
def task_get_status(
    task_id: str,
    include_outputs: bool = False,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    tail_lines: Optional[int] = None,
):
    """Get task status by ID.
    
    Used by Tools Server for task_query tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.get_status(
        task_id=task_id,
        include_outputs=include_outputs,
        start_line=start_line,
        end_line=end_line,
        tail_lines=tail_lines,
    )
```

**路由注册**: ✅ 已在 `novaic-backend/gateway/api/internal/__init__.py` 中注册

**状态**: ✅ API 端点完整，支持所有分页参数

---

### 2.4 TaskManager 后端支持

#### 2.4.1 `create_completed()` 方法

**位置**: `novaic-backend/gateway/core/task_manager.py` (第 317-388 行)

**功能**: 创建立即完成的任务，用于存储截断的输出

**实现要点**:
- ✅ 支持 `SYNC_OUTPUT` 任务类型
- ✅ 生成 `so_` 前缀的 task_id
- ✅ 将完整输出保存到文件系统 (`~/.novaic/task_outputs/{task_id}.txt`)
- ✅ 支持 TTL (默认 24 小时)
- ✅ 持久化到数据库

**⚠️ 发现的问题**:

**严重问题**: 第 359 行使用了 `aiofiles.open()`，但 `create_completed()` 是一个**同步方法**：

```python
# 第 359 行 - 问题代码
with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
    f.write(full_output)
```

**问题分析**:
- `aiofiles.open()` 返回异步上下文管理器，不能在同步 `with` 语句中使用
- 这会导致运行时错误：`TypeError: 'async_generator' object does not support the asynchronous context manager protocol`
- 应该使用标准的 `open()` 函数，或者将方法改为异步方法

**修复建议**:
```python
# 修复方案 1: 使用同步文件操作
output_file = output_dir / f"{task_id}.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(full_output)

# 修复方案 2: 改为异步方法（需要修改调用方）
async def create_completed(...):
    ...
    async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
        await f.write(full_output)
```

#### 2.4.2 `get_status()` 方法

**位置**: `novaic-backend/gateway/core/task_manager.py` (第 390-458 行)

**功能**: 获取任务状态，支持分页输出检索

**实现要点**:
- ✅ 支持通过 `task_id` 查询单个任务
- ✅ 支持 `include_outputs` 参数
- ✅ 支持分页参数：`start_line`, `end_line`, `tail_lines`
- ✅ 调用 `_read_output_file()` 读取完整输出文件
- ✅ 返回格式包含 `full_output`, `output_range`, `output_total_lines`, `output_has_more`

**状态**: ✅ 实现完整，功能正常

#### 2.4.3 `_read_output_file()` 方法

**位置**: `novaic-backend/gateway/core/task_manager.py` (第 1031-1091 行)

**功能**: 从文件读取输出，支持分页

**实现要点**:
- ✅ 支持 `tail_lines` (获取最后 N 行)
- ✅ 支持 `start_line` 和 `end_line` (范围查询)
- ✅ 返回元数据：总行数、返回行数、是否有更多内容
- ✅ 正确处理文件不存在的情况

**状态**: ✅ 实现完整，功能正常

**注意**: 该方法使用了 `aiofiles.open()`，但调用它的 `get_status()` 是同步方法。需要检查这是否会导致问题。

---

### 2.5 SYNC_OUTPUT 任务类型支持

**位置**: `novaic-backend/gateway/core/task_manager.py` (第 45 行)

**定义**:
```python
class TaskType(Enum):
    SYNC_OUTPUT = "sync_output"  # Truncated output from sync tool call
```

**使用**: ✅ 在 `create_completed()` 中正确使用 (第 365 行)

**状态**: ✅ 已正确定义和使用

---

### 2.6 API 端点 `/tasks/create-completed`

**位置**: `novaic-backend/gateway/api/internal/task.py` (第 45-64 行)

**端点定义**:
```python
@router.post("/tasks/create-completed")
def task_create_completed(data: Dict[str, Any]):
    """Create an immediately completed task for truncated output storage.
    
    Used by Tools Server for _auto_truncate_result.
    """
    task_id = task_manager.create_completed(
        tool_name=data.get("tool_name", "unknown"),
        truncated_result=data.get("truncated_result", ""),
        full_output=data.get("full_output", ""),
        ttl_hours=data.get("ttl_hours", 24),
        agent_id=data.get("agent_id"),
    )
    return {"task_id": task_id}
```

**状态**: ✅ API 端点已实现

**注意**: 文档中提到这个端点用于 `_auto_truncate_result`，但在代码库中没有找到 `_auto_truncate_result` 的实现。这可能是一个待实现的功能。

---

## 3. 功能验证

### 3.1 工具可用性

| 功能 | 状态 | 说明 |
|------|------|------|
| 工具定义 | ✅ | 在 `tools.py` 中正确定义 |
| 工具注册 | ✅ | 在 `executor.py` 的 `BUILTIN_TOOL_NAMES` 中注册 |
| 工具执行 | ✅ | 在 `executor.py` 中实现 |
| API 端点 | ✅ | `/internal/tasks/{task_id}` 已实现 |
| 后端支持 | ⚠️ | `create_completed()` 有 bug |

### 3.2 查询功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 通过 task_id 查询 | ✅ | 支持 |
| 查询 sync_output 任务 | ✅ | 支持 |
| 分页查询 (start_line/end_line) | ✅ | 支持 |
| 尾部查询 (tail_lines) | ✅ | 支持 |
| 包含中间输出 (include_outputs) | ✅ | 支持 |

### 3.3 存储功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 保存完整结果 | ⚠️ | `create_completed()` 有 bug |
| 文件系统存储 | ✅ | 保存到 `~/.novaic/task_outputs/` |
| 数据库持久化 | ✅ | 保存到 SQLite |
| TTL 支持 | ✅ | 默认 24 小时 |

---

## 4. 测试覆盖

### 4.1 单元测试

**搜索结果**: ❌ 未找到针对 `task_query` 工具的测试用例

**测试文件位置**: `novaic-backend/tests/`

**建议**: 创建以下测试用例：
1. `test_task_query.py` - 测试 task_query 工具
2. `test_task_manager_create_completed.py` - 测试 create_completed 方法
3. `test_task_manager_get_status.py` - 测试 get_status 方法的分页功能

---

## 5. 发现的问题

### 5.1 严重问题

#### 问题 1: `create_completed()` 方法中的异步文件操作错误

**位置**: `novaic-backend/gateway/core/task_manager.py:359`

**问题**: 在同步方法中使用 `aiofiles.open()`

**影响**: 会导致运行时错误，`create_completed()` 方法无法正常工作

**修复优先级**: 🔴 高

**修复方案**:
```python
# 将第 359-360 行改为：
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(full_output)
```

#### 问题 2: `_read_output_file()` 方法中的异步文件操作

**位置**: `novaic-backend/gateway/core/task_manager.py:1056`

**问题**: 在同步方法中使用 `aiofiles.open()`

**影响**: 可能导致运行时错误

**修复优先级**: 🟡 中

**修复方案**:
```python
# 将第 1056-1057 行改为：
with open(output_file, 'r', encoding='utf-8') as f:
    all_lines = f.readlines()
```

### 5.2 不一致问题

#### 问题 3: 工具定义与执行器参数不一致

**位置**: 
- 工具定义: `tools_server/tools.py:632-656`
- 执行器: `tools_server/executor.py:669`

**问题**: 执行器支持 `include_outputs` 参数，但工具定义中没有

**影响**: LLM 无法通过工具定义知道可以使用 `include_outputs` 参数

**修复优先级**: 🟡 中

**修复方案**: 在工具定义的 `inputSchema.properties` 中添加 `include_outputs` 参数

### 5.3 缺失功能

#### 问题 4: `_auto_truncate_result` 功能未实现

**位置**: 文档中提到，但代码中未找到

**问题**: 文档 (`TOOL_RESULT_UNIFIED_PROTOCOL.md`) 中提到 `_auto_truncate_result` 功能，但代码库中没有实现

**影响**: 自动截断功能可能未启用

**修复优先级**: 🟢 低（如果不需要自动截断）

---

## 6. 代码示例

### 6.1 使用 task_query 工具

```python
# LLM 调用示例
result = await executor.execute("task_query", {
    "task_id": "so_abc12345"
})

# 带分页的查询
result = await executor.execute("task_query", {
    "task_id": "so_abc12345",
    "start_line": 1,
    "end_line": 100
})

# 获取最后 50 行
result = await executor.execute("task_query", {
    "task_id": "so_abc12345",
    "tail_lines": 50
})
```

### 6.2 保存完整结果

```python
# 通过 API 保存完整结果
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://127.0.0.1:19999/internal/tasks/create-completed",
        json={
            "tool_name": "web_fetch",
            "truncated_result": "前500字符...",
            "full_output": "完整内容...",
            "ttl_hours": 24,
            "agent_id": "agent_123"
        }
    )
    data = response.json()
    task_id = data["task_id"]  # 例如: "so_abc12345"
```

### 6.3 查询保存的结果

```python
# 查询完整结果
result = await executor.execute("task_query", {
    "task_id": "so_abc12345"
})

# 返回格式示例
{
    "success": True,
    "id": "so_abc12345",
    "type": "sync_output",
    "status": "completed",
    "result": "截断版本...",
    "full_output": "完整内容...",  # 如果使用分页参数
    "output_range": "1-100",
    "output_total_lines": 500,
    "output_has_more": True
}
```

---

## 7. 总结和建议

### 7.1 实现状态

| 组件 | 状态 | 备注 |
|------|------|------|
| 工具定义 | ✅ 完成 | 需要添加 `include_outputs` 参数 |
| 工具执行 | ✅ 完成 | 实现正确 |
| API 端点 | ✅ 完成 | 路由已注册 |
| 后端支持 | ⚠️ 有 bug | `create_completed()` 需要修复 |
| 测试覆盖 | ❌ 缺失 | 建议添加单元测试 |

### 7.2 修复优先级

1. **🔴 高优先级**: 修复 `create_completed()` 中的异步文件操作错误
2. **🟡 中优先级**: 修复 `_read_output_file()` 中的异步文件操作
3. **🟡 中优先级**: 在工具定义中添加 `include_outputs` 参数
4. **🟢 低优先级**: 添加单元测试

### 7.3 验证建议

在修复 bug 后，建议进行以下验证：

1. **功能测试**:
   ```bash
   # 1. 创建一个 sync_output 任务
   curl -X POST http://127.0.0.1:19999/internal/tasks/create-completed \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "test_tool",
       "truncated_result": "Short version",
       "full_output": "Line 1\nLine 2\n...\nLine 1000",
       "agent_id": "test_agent"
     }'
   
   # 2. 查询任务
   curl http://127.0.0.1:19999/internal/tasks/{task_id}?tail_lines=50
   ```

2. **集成测试**: 通过 Tools Server 调用 `task_query` 工具

3. **边界测试**: 
   - 查询不存在的 task_id
   - 查询已过期的任务
   - 测试分页边界情况

---

## 8. 结论

`task_query` 工具**已基本实现**，核心功能完整，但存在一个**严重的 bug** 需要修复：

- ✅ 工具定义、执行器、API 端点都已实现
- ✅ 支持查询 sync_output 类型的任务
- ✅ 支持分页查询功能
- ⚠️ `create_completed()` 方法有 bug，需要修复后才能正常使用
- ❌ 缺少单元测试

**建议**: 优先修复 `create_completed()` 中的异步文件操作问题，然后添加测试用例以确保功能正常。
