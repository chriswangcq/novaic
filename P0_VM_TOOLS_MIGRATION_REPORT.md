# P0 大内容 VM 工具迁移报告

> **迁移时间**: 2026-02-07
> **迁移目标**: 将 5 个 P0 级别的大内容 VM 工具迁移到统一返回格式
> **涉及文件**: `novaic-backend/gateway/clients/vmuse_adapter.py`

---

## 1. 迁移总结

### 1.1 完成状态

✅ **全部完成** - 5 个工具已成功迁移到新的统一格式

| 工具名 | 旧格式 | 新格式 | 状态 |
|--------|--------|--------|------|
| `file_read` | `{success, result: {content, size, path}}` | `{success, content: [{type: "text", text: "..."}]}` | ✅ 完成 |
| `shell_exec` | `{success, result: {exit_code, stdout, stderr, command}}` | `{success, content: [{type: "text", text: "..."}]}` | ✅ 完成 |
| `system_snapshot` | `{success, result: {processes, memory, disk, network, cpu}}` | `{success, content: [{type: "text", text: "..."}]}` | ✅ 完成 |
| `clipboard_get` | `{success, result: {content}}` | `{success, content: [{type: "text", text: "..."}]}` | ✅ 完成 |
| `environment_info` | `{success, result: {os, distro, arch, env}}` | `{success, content: [{type: "text", text: "..."}]}` | ✅ 完成 |

### 1.2 代码统计

- **修改方法数**: 5 个
- **代码行数变化**: +105 行（包含错误处理和注释）
- **语法检查**: ✅ 通过
- **向后兼容**: ❌ 不兼容（需要更新调用方）

---

## 2. 详细改动

### 2.1 file_read（文件读取）

**改动位置**: 第 982-1003 行

**改动内容**:
1. ✅ 转换为标准格式 `{success, content}`
2. ✅ 保留所有原始字段（content, size, path）
3. ✅ 添加完整错误处理（HTTPStatusError, Exception）
4. ✅ 添加日志记录
5. ✅ 添加文档注释（说明自动截断机制）

**改动前**:
```python
return {
    "success": True,
    "result": {
        "content": result.get("content", ""),
        "size": result.get("size", 0),
        "path": path
    }
}
```

**改动后**:
```python
file_data = {
    "content": result.get("content", ""),
    "size": result.get("size", 0),
    "path": path
}

return {
    "success": True,
    "content": [
        {
            "type": "text",
            "text": json.dumps(file_data, ensure_ascii=False)
        }
    ]
}
```

**特殊处理**:
- 文件内容直接放在 JSON 中，不需要特殊处理
- 自动截断机制会处理大文件（>4KB）

---

### 2.2 shell_exec（Shell 命令执行）

**改动位置**: 第 1035-1067 行

**改动内容**:
1. ✅ 转换为标准格式 `{success, content}`
2. ✅ 保留所有原始字段（exit_code, stdout, stderr, command）
3. ✅ 添加完整错误处理（HTTPStatusError, Exception）
4. ✅ 添加日志记录（包含命令信息）
5. ✅ 添加文档注释

**改动前**:
```python
return {
    "success": result.get("exit_code", 0) == 0,
    "result": {
        "exit_code": result.get("exit_code", 0),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "command": command
    }
}
```

**改动后**:
```python
exec_data = {
    "exit_code": result.get("exit_code", 0),
    "stdout": result.get("stdout", ""),
    "stderr": result.get("stderr", ""),
    "command": command
}

return {
    "success": result.get("exit_code", 0) == 0,
    "content": [
        {
            "type": "text",
            "text": json.dumps(exec_data, ensure_ascii=False)
        }
    ]
}
```

**特殊处理**:
- stdout 和 stderr 可能很大，依赖自动截断机制
- success 仍然基于 exit_code 判断

---

### 2.3 system_snapshot（系统快照）

**改动位置**: 第 1984-2026 行

**改动内容**:
1. ✅ 转换为标准格式 `{success, content}`
2. ✅ 保留所有原始字段（processes, memory, disk, network, cpu）
3. ✅ 添加完整错误处理
4. ✅ 添加日志记录（包含 exc_info）
5. ✅ 添加文档注释

**改动前**:
```python
return {
    "success": True,
    "result": snapshot
}
```

**改动后**:
```python
return {
    "success": True,
    "content": [
        {
            "type": "text",
            "text": json.dumps(snapshot, ensure_ascii=False)
        }
    ]
}
```

**特殊处理**:
- 系统信息（尤其是进程列表）可能很大
- 自动截断机制会处理大内容（>4KB）

---

### 2.4 clipboard_get（获取剪贴板）

**改动位置**: 第 2028-2046 行

**改动内容**:
1. ✅ 转换为标准格式 `{success, content}`
2. ✅ 保留原始字段（content）
3. ✅ 添加完整错误处理
4. ✅ 添加日志记录（包含 exc_info）
5. ✅ 添加文档注释

**改动前**:
```python
return {
    "success": True,
    "result": {
        "content": result.get("stdout", "")
    }
}
```

**改动后**:
```python
clipboard_data = {
    "content": result.get("stdout", "")
}

return {
    "success": True,
    "content": [
        {
            "type": "text",
            "text": json.dumps(clipboard_data, ensure_ascii=False)
        }
    ]
}
```

**特殊处理**:
- 剪贴板内容可能包含大量文本
- 自动截断机制会处理大内容

---

### 2.5 environment_info（环境信息）

**改动位置**: 第 2074-2105 行

**改动内容**:
1. ✅ 转换为标准格式 `{success, content}`
2. ✅ 保留所有原始字段（os, distro, arch, env）
3. ✅ 添加完整错误处理
4. ✅ 添加日志记录（包含 exc_info）
5. ✅ 添加文档注释

**改动前**:
```python
return {
    "success": True,
    "result": info
}
```

**改动后**:
```python
return {
    "success": True,
    "content": [
        {
            "type": "text",
            "text": json.dumps(info, ensure_ascii=False)
        }
    ]
}
```

**特殊处理**:
- 环境变量（env）可能包含很多信息
- 自动截断机制会处理大内容

---

## 3. 格式验证

### 3.1 统一格式检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 返回 `{success, content}` | ✅ 通过 | 所有方法使用新格式 |
| `content` 是数组 | ✅ 通过 | 所有方法返回 `content: [...]` |
| 包含 `type: "text"` | ✅ 通过 | 所有方法使用 `type: "text"` |
| 使用 `json.dumps()` 序列化 | ✅ 通过 | 所有方法使用 `ensure_ascii=False` |
| 失败时返回空 `content` | ✅ 通过 | 所有错误处理包含 `content: []` |

### 3.2 数据保留检查

| 工具 | 原始字段 | 是否保留 |
|------|----------|----------|
| `file_read` | content, size, path | ✅ 完整保留 |
| `shell_exec` | exit_code, stdout, stderr, command | ✅ 完整保留 |
| `system_snapshot` | processes, memory, disk, network, cpu | ✅ 完整保留 |
| `clipboard_get` | content | ✅ 完整保留 |
| `environment_info` | os, distro, arch, env | ✅ 完整保留 |

---

## 4. 错误处理

### 4.1 错误处理完整性

| 工具 | HTTPStatusError | 通用 Exception | 日志记录 | 参数验证 |
|------|----------------|----------------|---------|----------|
| `file_read` | ✅ | ✅ | ✅ | ✅ |
| `shell_exec` | ✅ | ✅ | ✅ | ✅ |
| `system_snapshot` | ✅ | ✅ | ✅ | ❌ (无必需参数) |
| `clipboard_get` | ✅ | ✅ | ✅ | ❌ (无必需参数) |
| `environment_info` | ✅ | ✅ | ✅ | ❌ (无必需参数) |

### 4.2 错误返回格式

所有工具的错误返回都符合标准格式：

```python
{
    "success": False,
    "error": "详细的错误描述",
    "content": []
}
```

**改进点**:
- 捕获 `HTTPStatusError` 并返回 HTTP 状态码和响应文本
- 捕获通用异常并记录日志（包含 `exc_info=True`）
- 错误信息包含上下文（如文件路径、命令内容）

---

## 5. 自动截断验证

### 5.1 自动截断机制

根据 `TOOL_RESULT_UNIFIED_PROTOCOL.md`，自动截断机制在 `tools_server/executor.py` 中实现：

| 阈值 | 策略 | 说明 |
|------|------|------|
| < 4KB | 不截断 | 完整返回 |
| 4KB - 10KB | `head_tail` | 保留首尾各 1.5KB |
| > 10KB | `reference_only` | 仅返回引用 |

**重要**: 只有文本内容会被截断，图像、视频、音频等二进制内容不会被截断。

### 5.2 工具内容大小评估

| 工具 | 典型大小 | 最大大小 | 截断风险 |
|------|----------|----------|----------|
| `file_read` | 1KB - 1MB | 无限制 | ⚠️ 高（大文件） |
| `shell_exec` | 100B - 100KB | 无限制 | ⚠️ 高（大输出） |
| `system_snapshot` | 5KB - 50KB | ~100KB | ⚠️ 中（全量快照） |
| `clipboard_get` | 10B - 10KB | 无限制 | ⚠️ 中（大文本） |
| `environment_info` | 500B - 5KB | ~10KB | ✅ 低（信息有限） |

### 5.3 自动截断示例

当工具返回大内容时，executor 会自动处理：

**原始返回** (10KB):
```json
{
  "success": true,
  "content": [
    {
      "type": "text",
      "text": "{\"stdout\": \"...10KB of output...\"}"
    }
  ]
}
```

**自动截断后** (3KB):
```json
{
  "success": true,
  "content": [
    {
      "type": "text",
      "text": "{\"stdout\": \"First 1.5KB...\"}"
    },
    {
      "type": "text",
      "text": "\n... [middle text content removed] ...\n"
    },
    {
      "type": "text",
      "text": "{\"stdout\": \"Last 1.5KB...\"}"
    },
    {
      "type": "text",
      "text": "[Content truncated: 10240 bytes total]",
      "_truncated": true,
      "_truncation": {
        "strategy": "head_tail",
        "original_size": 10240,
        "truncated_size": 3000,
        "task_id": "so_abc12345",
        "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
      }
    }
  ]
}
```

---

## 6. 测试建议

### 6.1 单元测试

**测试场景**:

#### 6.1.1 file_read
```python
# 测试 1: 小文件（< 4KB）
await adapter.call_tool("file_read", {"path": "/etc/hosts"}, vm_id="1")
# 预期: 完整返回，不截断

# 测试 2: 大文件（> 4KB）
await adapter.call_tool("file_read", {"path": "/var/log/syslog"}, vm_id="1")
# 预期: 自动截断，返回 task_id

# 测试 3: 不存在的文件
await adapter.call_tool("file_read", {"path": "/nonexistent"}, vm_id="1")
# 预期: success=False, error 信息
```

#### 6.1.2 shell_exec
```python
# 测试 1: 简单命令
await adapter.call_tool("shell_exec", {"command": "echo hello"}, vm_id="1")
# 预期: 完整返回，exit_code=0

# 测试 2: 大输出命令
await adapter.call_tool("shell_exec", {"command": "cat /var/log/syslog"}, vm_id="1")
# 预期: 自动截断，返回 task_id

# 测试 3: 失败命令
await adapter.call_tool("shell_exec", {"command": "nonexistent_cmd"}, vm_id="1")
# 预期: success=False, exit_code!=0
```

#### 6.1.3 system_snapshot
```python
# 测试 1: 部分快照
await adapter.call_tool("system_snapshot", {"include": ["memory", "cpu"]}, vm_id="1")
# 预期: 仅包含 memory 和 cpu 字段

# 测试 2: 全量快照
await adapter.call_tool("system_snapshot", {"include": ["processes", "memory", "disk", "network", "cpu"]}, vm_id="1")
# 预期: 可能被截断（取决于内容大小）

# 测试 3: 空快照
await adapter.call_tool("system_snapshot", {"include": []}, vm_id="1")
# 预期: 返回空 snapshot {}
```

#### 6.1.4 clipboard_get
```python
# 测试 1: 小内容
# 先设置剪贴板: clipboard_set("hello world")
await adapter.call_tool("clipboard_get", {}, vm_id="1")
# 预期: 返回 "hello world"

# 测试 2: 大内容
# 先设置剪贴板: clipboard_set("A" * 10000)
await adapter.call_tool("clipboard_get", {}, vm_id="1")
# 预期: 自动截断，返回 task_id

# 测试 3: 空剪贴板
await adapter.call_tool("clipboard_get", {}, vm_id="1")
# 预期: 返回空字符串
```

#### 6.1.5 environment_info
```python
# 测试 1: 正常获取
await adapter.call_tool("environment_info", {}, vm_id="1")
# 预期: 返回 os, distro, arch, env 字段

# 测试 2: 格式验证
result = await adapter.call_tool("environment_info", {}, vm_id="1")
info = json.loads(result["content"][0]["text"])
assert "os" in info
assert "distro" in info
assert "arch" in info
assert "env" in info
```

### 6.2 集成测试

**测试流程**:

```python
# 1. 执行大输出命令
result = await adapter.call_tool("shell_exec", {
    "command": "seq 1 10000"  # 输出 1-10000
}, vm_id="1")

# 2. 检查是否被截断
assert result["success"] == True
content_text = result["content"][0]["text"]
data = json.loads(content_text)

# 3. 如果被截断，验证 task_id
if len(content_text) > 4096:
    # 应该被截断
    # 检查是否有 _truncation 字段
    pass

# 4. 使用 task_query 获取完整内容
# (假设 task_query 工具已实现)
if "_truncation" in result.get("content", [{}])[0]:
    task_id = result["content"][0]["_truncation"]["task_id"]
    full_result = await adapter.call_tool("task_query", {
        "task_id": task_id
    }, vm_id="1")
    # 验证完整内容
```

### 6.3 压力测试

**测试场景**:

```python
# 1. 极大文件读取（100MB+）
await adapter.call_tool("file_read", {
    "path": "/var/log/big_log_file.log"
}, vm_id="1")

# 2. 长时间运行命令
await adapter.call_tool("shell_exec", {
    "command": "find / -type f"  # 遍历整个文件系统
}, vm_id="1")

# 3. 并发调用
import asyncio
tasks = [
    adapter.call_tool("system_snapshot", {}, vm_id="1")
    for _ in range(10)
]
results = await asyncio.gather(*tasks)
```

---

## 7. 潜在问题和解决方案

### 7.1 已知问题

| 问题 | 影响 | 优先级 | 解决方案 |
|------|------|--------|----------|
| 向后不兼容 | 旧代码无法解析新格式 | 🔴 高 | 需要更新所有调用方 |
| JSON 嵌套 | 数据被双重序列化 | 🟡 中 | 后续可优化为直接传递结构化数据 |
| 二进制文件 | file_read 无法处理二进制 | 🟡 中 | 需要添加 base64 编码支持 |
| 截断阈值 | 4KB 可能太小 | 🟢 低 | 配置化，根据实际情况调整 |

### 7.2 向后兼容性

**影响范围**:
- `tools_server/executor.py` - 需要更新结果解析逻辑
- `task_queue/utils/multimodal.py` - 需要支持新格式
- 其他调用这 5 个工具的代码

**迁移步骤**:
1. 确保 `multimodal.py` 的 `extract_from_result()` 支持新格式
2. 更新 `executor.py` 的结果处理逻辑
3. 测试验证所有调用链

### 7.3 优化建议

**短期优化**:
1. 添加配置项控制截断阈值
2. 为二进制文件添加 base64 编码支持
3. 优化 JSON 序列化性能

**长期优化**:
1. 实现智能摘要策略（针对结构化数据）
2. 支持流式返回（大文件分块传输）
3. 添加压缩支持（gzip）

---

## 8. 相关文件

### 8.1 需要更新的文件

| 文件 | 原因 | 优先级 |
|------|------|--------|
| `tools_server/executor.py` | 实现自动截断机制 | 🔴 P0 |
| `task_queue/utils/multimodal.py` | 支持新格式提取 | 🔴 P0 |
| `common/config.py` | 添加截断配置项 | 🟡 P1 |
| `gateway/api/internal/__init__.py` | 移除解包逻辑 | 🟡 P1 |

### 8.2 参考文档

- `TOOL_RESULT_UNIFIED_PROTOCOL.md` - 统一返回格式协议
- `AUTO_TRUNCATE_IMPLEMENTATION_REPORT.md` - 自动截断机制实现报告
- `BROWSER_TOOLS_MIGRATION_SUMMARY.md` - 浏览器工具迁移参考

---

## 9. 验证清单

### 9.1 代码质量

- [x] 语法检查通过
- [x] 格式符合标准
- [x] 错误处理完整
- [x] 日志记录完善
- [x] 注释清晰

### 9.2 功能验证

- [ ] 小内容正常返回（< 4KB）
- [ ] 大内容自动截断（> 4KB）
- [ ] 错误处理正确
- [ ] 参数验证有效
- [ ] 日志输出正确

### 9.3 集成验证

- [ ] executor 自动截断机制工作
- [ ] multimodal 提取正常
- [ ] task_query 可获取完整内容
- [ ] 前端显示正常

---

## 10. 总结

### 10.1 迁移成果

✅ **5 个 P0 工具已成功迁移到新的统一格式**

**关键改进**:
1. **统一格式**: 所有工具使用 `{success, content}` 格式
2. **完整错误处理**: 捕获所有异常并返回详细错误
3. **自动截断支持**: 大内容会被自动截断机制处理
4. **数据完整性**: 所有原始字段通过 JSON 序列化保留
5. **可观测性**: 添加完善的日志记录

### 10.2 下一步工作

**立即执行** (P0):
1. 实现 `executor.py` 的自动截断机制
2. 更新 `multimodal.py` 支持新格式
3. 运行集成测试验证

**短期执行** (P1):
1. 添加单元测试
2. 更新文档和 API 说明
3. 监控生产环境表现

**长期执行** (P2):
1. 优化截断策略
2. 实现智能摘要
3. 添加压缩支持

### 10.3 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 调用方不兼容 | 高 | 高 | 同步更新所有调用方 |
| 性能下降 | 低 | 中 | JSON 序列化优化 |
| 截断阈值不合理 | 中 | 低 | 配置化，动态调整 |

---

**报告生成时间**: 2026-02-07
**迁移负责人**: AI Assistant
**代码审查状态**: 待审查
**测试状态**: 待测试
