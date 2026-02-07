# P0 工具迁移快速参考

> 快速查看 P0 级别大内容工具的迁移要点

---

## 迁移的工具

| 工具 | 位置 | 状态 |
|------|------|------|
| `task_query` | executor.py:700-760 | ✅ 已完成 |
| `web_fetch` | executor.py:591-626 | ✅ 已完成 |

---

## 新格式示例

### task_query 返回格式

#### 新格式任务（含图片）
```python
{
    "success": True,
    "content": [
        {
            "type": "text",
            "text": "Screenshot captured successfully"
        },
        {
            "type": "image",
            "data": "iVBORw0KGgoAAAANSUhEUg...",
            "mimeType": "image/png"
        }
    ]
}
```

#### 旧格式任务（自动转换）
```python
{
    "success": True,
    "content": [
        {
            "type": "text",
            "text": "{\"task_id\": \"xxx\", \"status\": \"completed\", \"result\": {...}}"
        }
    ]
}
```

#### 错误情况
```python
{
    "success": False,
    "error": "Task 'xxx' not found",
    "content": [
        {
            "type": "text",
            "text": "{\"success\": false, \"error\": \"Task 'xxx' not found\"}"
        }
    ]
}
```

### web_fetch 返回格式

#### 成功
```python
{
    "success": True,
    "content": [
        {
            "type": "text",
            "text": "{\"url\": \"https://example.com\", \"title\": \"Example\", \"content\": \"...\"}"
        }
    ]
}
```

#### 错误
```python
{
    "success": False,
    "error": "HTTP 404: Not Found",
    "content": [
        {
            "type": "text",
            "text": "{\"url\": \"https://example.com\", \"error\": \"HTTP 404: Not Found\", \"success\": false}"
        }
    ]
}
```

---

## 关键特性

### task_query

✅ **格式兼容性检测**
- 自动检测任务结果是新格式还是旧格式
- 新格式直接返回，保留图片等多模态数据
- 旧格式转换为 JSON 文本

✅ **多模态数据保留**
- 图片、视频等二进制数据完整保留
- 不做任何修改或转换

✅ **错误处理**
- 所有错误情况都返回新格式
- 包含 content 数组和 error 字段

### web_fetch

✅ **统一返回格式**
- 成功和失败都返回 `{success, content}` 格式
- content 是文本数组

✅ **依赖自动截断**
- web_fetch 的内容可能很大（最大 50KB）
- 自动截断机制会在 execute() 中处理

✅ **完整错误处理**
- 网络错误、HTTP 错误等都正确处理
- 返回详细的错误信息

---

## 自动截断机制

### 触发条件

| 内容大小 | 策略 | 说明 |
|---------|------|------|
| < 4KB | 不截断 | 完整返回 |
| 4KB - 10KB | `head_tail` | 保留首尾各 1.5KB |
| > 10KB | `reference_only` | 仅返回引用 + task_id |

### 重要提示

- ⚠️ **只截断文本内容**
- ✅ **图片、视频等二进制内容不截断**
- ✅ **自动保存完整内容到 TaskManager**
- ✅ **LLM 可以通过 task_query 获取完整内容**

### 示例：大内容被截断

```python
# web_fetch 返回大内容
{
    "success": True,
    "content": [
        {"type": "text", "text": "First 1.5KB..."},
        {
            "type": "text",
            "text": "... [middle text content removed] ...",
            "_truncated": True,
            "_truncation": {
                "strategy": "head_tail",
                "original_size": 8192,
                "task_id": "so_abc12345",
                "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
            }
        },
        {"type": "text", "text": "Last 1.5KB..."}
    ],
    "task_id": "so_abc12345"
}
```

---

## 测试命令

### 快速测试

```python
# 1. 测试 task_query（新格式）
result = await executor.execute("task_query", {"task_id": "some_task_id"})
assert result["success"] == True
assert "content" in result

# 2. 测试 web_fetch（小内容）
result = await executor.execute("web_fetch", {"url": "https://example.com"})
assert result["success"] == True
assert "content" in result

# 3. 测试 web_fetch（大内容）
result = await executor.execute("web_fetch", {
    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"
})
# 如果内容被截断，会有 task_id
if "task_id" in result:
    full = await executor.execute("task_query", {"task_id": result["task_id"]})
    assert full["success"] == True
```

### 语法检查

```bash
cd novaic-backend && python3 -m py_compile tools_server/executor.py
```

---

## 常见问题

### Q1: task_query 会丢失图片吗？

**A**: 不会。格式检测逻辑会保留新格式中的图片数据。

```python
# 如果任务结果已经是新格式（包含 content 数组），直接返回
if isinstance(task_result, dict) and "content" in task_result:
    return {
        "success": True,
        "content": task_result["content"]  # 图片数据保留
    }
```

### Q2: web_fetch 的大内容会被截断吗？

**A**: 会。自动截断机制会处理大于 4KB 的文本内容。

- 4KB-10KB: head_tail 策略（保留首尾）
- >10KB: reference_only 策略（仅返回引用）

完整内容会保存到 TaskManager，可以通过 task_query 获取。

### Q3: 自动截断会影响图片吗？

**A**: 不会。自动截断机制只截断文本内容，图片等二进制数据完整保留。

```python
# executor.py:_calculate_content_size()
def _calculate_content_size(self, content: List[Dict[str, Any]]) -> int:
    total = 0
    for item in content:
        if item.get("type") == "text":
            total += len(item.get("text", "").encode("utf-8"))
        # 图像、视频等不计入大小（不会被截断）
    return total
```

### Q4: 如何获取被截断的完整内容？

**A**: 使用 task_query 工具。

```python
# 1. 调用 web_fetch（返回截断版本）
result = await executor.execute("web_fetch", {"url": "large_page"})

# 2. 提取 task_id
truncation = next(item for item in result["content"] if item.get("_truncated"))
task_id = truncation["_truncation"]["task_id"]

# 3. 调用 task_query 获取完整内容
full_result = await executor.execute("task_query", {"task_id": task_id})
```

### Q5: 旧格式任务会被正确处理吗？

**A**: 会。task_query 会自动检测格式并转换。

```python
# 旧格式
{"result": {"key": "value"}}

# 自动转换为
{
    "success": True,
    "content": [
        {
            "type": "text",
            "text": "{\"task_id\": \"xxx\", \"result\": {\"key\": \"value\"}}"
        }
    ]
}
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `P0_LARGE_CONTENT_TOOLS_MIGRATION_REPORT.md` | 完整迁移报告 |
| `TOOL_RESULT_UNIFIED_PROTOCOL.md` | 统一协议设计 |
| `AUTO_TRUNCATE_IMPLEMENTATION_REPORT.md` | 自动截断实现 |

---

## 配置参考

### 自动截断配置 (common/config.py)

```python
# 是否启用自动截断
AUTO_TRUNCATE_ENABLED = True

# 截断阈值（只计算文本大小）
AUTO_TRUNCATE_THRESHOLD_SMALL = 4096   # 4KB
AUTO_TRUNCATE_THRESHOLD_LARGE = 10240  # 10KB

# 头尾保留大小
AUTO_TRUNCATE_HEAD_SIZE = 1536  # 1.5KB
AUTO_TRUNCATE_TAIL_SIZE = 1536  # 1.5KB

# 保存时长
AUTO_TRUNCATE_TTL_HOURS = 24  # 24小时
```

---

*最后更新：2026-02-07*
