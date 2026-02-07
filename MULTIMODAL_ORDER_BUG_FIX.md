# 多模态消息顺序 Bug 修复

## 🐛 问题描述

当多个工具调用结果中包含图片时，LLM API 调用失败，报错：

```
tool_call_ids did not have response messages: shell_exec:1, browser_navigate:2
```

## 🔍 根本原因

### OpenAI/Moonshot API 要求

1. **assistant message with `tool_calls` 必须紧接着所有对应的 tool results**
2. **不能在 tool results 中间插入其他消息（如 user message）**

### 原有实现的问题

`task_queue/utils/context.py::process_multimodal_messages` 的原实现：

- 每个 tool result 处理完后，**立即**添加图片 user message
- 导致 tool results 不连续

**错误的消息顺序：**

```
[3] assistant: tool_calls=['screenshot:0', 'shell_exec:1', 'browser_navigate:2']
[4] tool: screenshot:0
[5] user: [图片]  ← ❌ 这里打断了！
[6] tool: shell_exec:1
[7] tool: browser_navigate:2
```

**API 看到的结构：**

- `[3]` assistant with tool_calls
- `[4]` tool result: `screenshot:0` ✓
- `[5]` user message ← API 认为 tool results 到此结束
- `[6]` tool result: `shell_exec:1` ← API 认为这个不属于 `[3]`
- `[7]` tool result: `browser_navigate:2` ← API 认为这个也不属于 `[3]`

结果：API 报错缺少 `shell_exec:1` 和 `browser_navigate:2` 的响应

## ✅ 修复方案

### 策略

**收集图片，延迟添加到所有 tool results 之后**

### 修改代码

修改 `novaic-backend/task_queue/utils/context.py::process_multimodal_messages`：

**关键改动：**

1. **添加 `pending_images` 列表**：收集待添加的图片 user messages
2. **延迟添加图片**：遇到非 tool result 消息时，先把收集的图片添加进来
3. **处理末尾**：循环结束后，添加剩余的图片

```python
def process_multimodal_messages(
    messages: List[Dict[str, Any]], 
    provider: str = "openai"
) -> List[Dict[str, Any]]:
    if not HAS_MULTIMODAL:
        return messages
    
    processed = []
    pending_images = []  # 🔑 收集待添加的图片
    
    for i, msg in enumerate(messages):
        role = msg.get("role")
        
        if role in ("tool_result", "tool"):
            # ... 提取图片逻辑 ...
            
            if images:
                # 🔑 收集图片，但不立即添加
                pending_images.append({
                    "role": "user",
                    "content": img_content,
                })
        else:
            # 非 tool result 消息
            # 🔑 如果有待添加的图片，先把它们添加进来
            if pending_images:
                processed.extend(pending_images)
                pending_images = []
            
            processed.append(msg)
    
    # 🔑 处理末尾剩余的图片
    if pending_images:
        processed.extend(pending_images)
    
    return processed
```

### 修复后的消息顺序

**正确的顺序：**

```
[3] assistant: tool_calls=['screenshot:0', 'shell_exec:1', 'browser_navigate:2']
[4] tool: screenshot:0      ↓
[5] tool: shell_exec:1      ├─ 所有 tool results 连续！
[6] tool: browser_navigate:2 ↓
[7] user: [图片]  ← ✅ 图片在所有 tool results 之后
```

**API 看到的结构：**

- `[3]` assistant with tool_calls
- `[4]` tool result: `screenshot:0` ✓
- `[5]` tool result: `shell_exec:1` ✓
- `[6]` tool result: `browser_navigate:2` ✓
- `[7]` user message with image

结果：✅ API 接受

## 🧪 测试验证

### 单元测试

创建了 `test_multimodal_order_fix.py` 验证：

1. ✅ 多个 tool results（包含图片）保持连续
2. ✅ 图片 user messages 在所有 tool results 之后
3. ✅ 符合 OpenAI/Moonshot API 要求

**测试结果：**

```
======================================================================
测试：多个 tool results（包含图片）
======================================================================
Expected tool_call_ids: ['screenshot:0', 'shell_exec:1', 'browser_navigate:2']
Found tool_call_ids: ['screenshot:0', 'shell_exec:1', 'browser_navigate:2']
✅ 所有 tool results 连续且完整
✅ 图片 user message 在所有 tool results 之后（索引 5）

======================================================================
✅ 所有测试通过
```

### 数据库验证

验证了实际 runtime (`rt-d9a3a1450475`)：

```
[3] Assistant with tool_calls:
  - screenshot:0
  - shell_exec:1
  - browser_navigate:2

后续消息:
  [4] tool: screenshot:0
  [5] tool: shell_exec:1
  [6] tool: browser_navigate:2
  [7] user
       └─ (图片 user message)

验证结果:
  ✅ 完整且连续
```

## 📊 影响范围

### 修复的问题

1. ✅ **多工具调用 + 图片**：修复了多个工具调用中有图片时的顺序问题
2. ✅ **LLM API 兼容性**：符合 OpenAI/Anthropic/Moonshot API 规范
3. ✅ **单工具调用**：对单工具调用场景无影响（已测试）

### 未解决的问题

根据之前的调查报告 (`MULTIMODAL_CONTEXT_EXPLOSION_INVESTIGATION.md`)，仍存在：

1. **多轮对话的上下文爆炸**：每轮 LLM 调用都会重新处理所有历史图片
2. **建议方案**：
   - **短期**：限制历史图片数量（`max_recent_images=5`）
   - **长期**：外部图片存储 + 引用机制

## 🎯 总结

### 修复内容

- **文件**：`novaic-backend/task_queue/utils/context.py`
- **函数**：`process_multimodal_messages`
- **改动**：延迟添加图片 user messages，保证 tool results 连续性

### 关键点

1. **OpenAI/Moonshot API 严格要求消息顺序**
2. **tool results 必须连续，不能被其他消息打断**
3. **图片提取是正确的，只是添加时机错了**

### 后续工作

1. ✅ 修复消息顺序问题（已完成）
2. 🔜 解决多轮对话的上下文爆炸问题
3. 🔜 实现外部图片存储机制

---

**修复日期**: 2026-02-07  
**影响版本**: 所有使用多工具调用 + 图片的场景  
**测试状态**: ✅ 通过
