# 自动截断机制 - 快速参考

## 🎯 核心功能

在 `tools_server/executor.py` 中实现了自动截断机制，用于处理长工具结果。

## 📦 实现的方法

### 1. `_handle_long_result()` - 主处理函数 (888-971行)

**策略**：
- **< 4KB**: 不处理
- **4KB - 10KB**: head_tail (首尾各 1.5KB)
- **> 10KB**: reference_only (仅引用)

### 2. `_calculate_content_size()` - 计算大小 (973-990行)

**重要**: 只计算文本大小，**图像/视频不计入**

```python
for item in content:
    if item.get("type") == "text":
        total += len(item.get("text", "").encode("utf-8"))
    # 图像、视频等不计入（不会被截断）
```

### 3. `_truncate_head_tail()` - 截断文本 (992-1108行)

**重要**: 只截断文本，**图像/视频完整保留**

- 保留头部 1.5KB
- 添加省略标记
- 保留尾部 1.5KB
- UTF-8 边界安全处理

### 4. `_save_full_result()` - 保存完整内容 (1110-1159行)

- 调用 `/internal/tasks/create-completed` API
- 返回 task_id
- 失败时生成临时 ID (`so_temp_*`)

## 🔧 配置项

在 `common/config.py` 中：

```python
AUTO_TRUNCATE_ENABLED = true              # 总开关
AUTO_TRUNCATE_THRESHOLD_SMALL = 4096      # 4KB
AUTO_TRUNCATE_THRESHOLD_LARGE = 10240     # 10KB
AUTO_TRUNCATE_HEAD_SIZE = 1536            # 1.5KB
AUTO_TRUNCATE_TAIL_SIZE = 1536            # 1.5KB
AUTO_TRUNCATE_TTL_HOURS = 24              # 24小时
```

## 📊 截断结果格式

### head_tail 策略 (4-10KB)

```json
{
  "success": true,
  "content": [
    {"type": "text", "text": "头部内容..."},
    {"type": "text", "text": "\n... [middle text content removed] ...\n"},
    {"type": "text", "text": "...尾部内容"},
    {
      "type": "text",
      "text": "[Content truncated: 8192 bytes total, showing head+tail]",
      "_truncated": true,
      "_truncation": {
        "strategy": "head_tail",
        "original_size": 8192,
        "truncated_size": 3000,
        "task_id": "so_abc12345",
        "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
      }
    }
  ],
  "task_id": "so_abc12345"
}
```

### reference_only 策略 (>10KB)

```json
{
  "success": true,
  "content": [
    {
      "type": "text",
      "text": "Output is very large (15360 bytes). Full content saved to task.",
      "_truncated": true,
      "_truncation": {
        "strategy": "reference_only",
        "original_size": 15360,
        "task_id": "so_abc12345",
        "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
      }
    }
  ],
  "task_id": "so_abc12345"
}
```

## 🔑 关键设计

### ✅ 图像不截断

```python
# 计算大小时
if item.get("type") == "text":
    total += len(text)
# 图像不计入

# 截断时
if item.get("type") == "text":
    # 截断文本
else:
    # 图像完整保留
    result.append(item)
```

### ✅ UTF-8 安全

```python
try:
    truncated_text = truncated_bytes.decode("utf-8")
except UnicodeDecodeError:
    # 回退到安全的解码点
    while len(truncated_bytes) > 0:
        try:
            truncated_text = truncated_bytes.decode("utf-8")
            break
        except UnicodeDecodeError:
            truncated_bytes = truncated_bytes[:-1]
```

## 🧪 测试要点

### 测试 1: 小文本不截断
```python
result = {"content": [{"type": "text", "text": "A" * 1000}]}
# 应原样返回，不添加 _truncated
```

### 测试 2: 中等文本 head_tail
```python
result = {"content": [{"type": "text", "text": "A" * 5000}]}
# 应包含 head + "..." + tail + 截断信息
```

### 测试 3: 大文本 reference_only
```python
result = {"content": [{"type": "text", "text": "A" * 15000}]}
# 应只返回引用，不包含原文本
```

### 测试 4: 图文混合
```python
result = {
    "content": [
        {"type": "text", "text": "A" * 10000},
        {"type": "image", "data": "base64...", "mimeType": "image/png"}
    ]
}
# 文本被截断，图像完整保留
```

### 测试 5: task_query 查询
```python
result = await executor.execute("tool_name", {})
task_id = result["task_id"]
full = await executor.execute("task_query", {"task_id": task_id})
# 应返回完整内容
```

## 📝 集成检查清单

- [x] 修改 `execute()` 方法
- [x] 实现 4 个核心函数
- [x] 添加必要的导入
- [x] 语法检查通过
- [x] Linter 检查通过
- [ ] 单元测试
- [ ] 集成测试
- [ ] 验证 Gateway API
- [ ] 更新 System Prompt

## 🚀 使用示例

### 禁用自动截断

```bash
export AUTO_TRUNCATE_ENABLED=false
```

### 调整阈值

```bash
export AUTO_TRUNCATE_THRESHOLD_SMALL=8192   # 8KB
export AUTO_TRUNCATE_THRESHOLD_LARGE=20480  # 20KB
```

### 调整保留大小

```bash
export AUTO_TRUNCATE_HEAD_SIZE=2048  # 2KB
export AUTO_TRUNCATE_TAIL_SIZE=2048  # 2KB
```

## 📌 待办事项

### 优先级 P0
- [ ] 添加单元测试
- [ ] 验证 Gateway API (`/internal/tasks/create-completed`)
- [ ] 测试 task_query 工具

### 优先级 P1
- [ ] 更新 System Prompt
- [ ] 添加监控指标
- [ ] 端到端测试

### 优先级 P2
- [ ] 图像压缩集成
- [ ] 智能摘要策略
- [ ] 性能优化

## 🔗 相关文档

- **设计文档**: `TOOL_RESULT_UNIFIED_PROTOCOL.md` 第 4 节
- **实施报告**: `AUTO_TRUNCATE_IMPLEMENTATION_REPORT.md`
- **配置文件**: `novaic-backend/common/config.py`
- **实现文件**: `novaic-backend/tools_server/executor.py`

---

**最后更新**: 2026-02-07
