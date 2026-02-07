# P0 VM 工具迁移快速参考

> **状态**: ✅ 已完成 | **日期**: 2026-02-07

---

## 已迁移工具列表

| # | 工具名 | 风险等级 | 状态 |
|---|--------|----------|------|
| 1 | `file_read` | 🔴 高（大文件） | ✅ 完成 |
| 2 | `shell_exec` | 🔴 高（大输出） | ✅ 完成 |
| 3 | `system_snapshot` | 🟡 中（全量快照） | ✅ 完成 |
| 4 | `clipboard_get` | 🟡 中（大文本） | ✅ 完成 |
| 5 | `environment_info` | 🟢 低（信息有限） | ✅ 完成 |

---

## 新格式示例

### 成功返回

```python
{
    "success": True,
    "content": [
        {
            "type": "text",
            "text": json.dumps({
                "field1": "value1",
                "field2": "value2"
            }, ensure_ascii=False)
        }
    ]
}
```

### 失败返回

```python
{
    "success": False,
    "error": "详细的错误描述",
    "content": []
}
```

---

## 自动截断机制

| 阈值 | 策略 | 返回内容 |
|------|------|----------|
| < 4KB | 不截断 | 完整内容 |
| 4KB - 10KB | `head_tail` | 首尾各 1.5KB + task_id |
| > 10KB | `reference_only` | 仅 task_id |

**重要**: 只有**文本**内容会被截断，图像、视频不会被截断。

---

## 调用示例

### file_read

```python
# 读取小文件
result = await adapter.call_tool("file_read", {
    "path": "/etc/hosts"
}, vm_id="1")

# 解析结果
data = json.loads(result["content"][0]["text"])
print(data["content"])  # 文件内容
print(data["size"])     # 文件大小
print(data["path"])     # 文件路径
```

### shell_exec

```python
# 执行命令
result = await adapter.call_tool("shell_exec", {
    "command": "ls -la"
}, vm_id="1")

# 解析结果
data = json.loads(result["content"][0]["text"])
print(data["stdout"])    # 标准输出
print(data["stderr"])    # 标准错误
print(data["exit_code"]) # 退出码
```

### system_snapshot

```python
# 获取系统快照
result = await adapter.call_tool("system_snapshot", {
    "include": ["memory", "cpu"]
}, vm_id="1")

# 解析结果
data = json.loads(result["content"][0]["text"])
print(data["memory"])  # 内存信息
print(data["cpu"])     # CPU 信息
```

---

## 错误处理

所有工具都遵循统一的错误处理模式：

```python
try:
    result = await adapter.call_tool("tool_name", {...}, vm_id="1")
    
    if not result["success"]:
        print(f"Error: {result['error']}")
        return
    
    # 解析成功结果
    data = json.loads(result["content"][0]["text"])
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## 测试命令

```bash
# 语法检查
cd novaic-backend
python -m py_compile gateway/clients/vmuse_adapter.py

# 运行测试（待实现）
pytest tests/test_vmuse_adapter.py -v

# 集成测试（待实现）
pytest tests/integration/test_vm_tools.py -v
```

---

## 下一步

1. **实现自动截断机制** (`executor.py`)
2. **更新 multimodal 提取** (`multimodal.py`)
3. **运行集成测试**
4. **监控生产环境**

---

详细报告: `P0_VM_TOOLS_MIGRATION_REPORT.md`
