# 多模态上下文爆炸问题 - Bug 报告

## 🎯 问题定位

**结论：这不是 Bug，而是架构设计问题**

## 📊 调查数据

### Runtime 数据验证
- **Runtime ID**: rt-9b23e58b3bbc
- **原始 Context**: 696,393 bytes (8 条消息)
- **处理后 Context**: 696,382 bytes (9 条消息)
- **大小减少**: **-11 bytes (0.0%)**

### 图片数据流向

```
tool result (661,772 bytes 图片)
    ↓ process_multimodal_messages()
    ├─ tool result: 图片替换为占位符 (~200 bytes)
    └─ 新增 user message: 包含完整图片 (661,919 bytes)
    ↓
结果: 总大小几乎不变
```

## 🔍 根本原因

### 1. process_multimodal_messages 没有 Bug

**验证结果：✅ 功能正常**

- ✅ 正确检测图片 (`has_images`)
- ✅ 正确提取图片 (`extract_from_result`)
- ✅ 正确清理 tool result（替换为占位符）
- ✅ 正确创建 user message（符合 LLM API 规范）

**代码位置：**
```
novaic-backend/task_queue/utils/context.py
├─ process_multimodal_messages (L175-261) ✓ 正常工作
└─ multimodal.py
   ├─ has_images (L209-259) ✓ 正常工作
   └─ extract_from_result (L112-206) ✓ 正常工作
```

### 2. 真正的问题：图片数据循环

**数据流：**

```
第1轮: screenshot (600KB)
    ↓ 保存到数据库（原始数据）
    ↓ LLM 调用时处理
    └→ 发送给 LLM (600KB)

第2轮: screenshot (600KB)
    ↓ Context = [round1_image + round2_image]
    ↓ 两次处理
    └→ 发送给 LLM (1.2MB)

第3轮: screenshot (600KB)
    ↓ Context = [round1_image + round2_image + round3_image]
    ↓ 三次处理
    └→ 发送给 LLM (1.8MB)
    
... 线性增长
```

### 3. 问题出在保存策略

**当前设计（有问题）：**

```python
# gateway/api/internal/runtime.py::append_message_to_context
# 第 408-410 行
# 注意：不在这里处理图片分离！
# 保持原始 tool result（包含完整图片数据）
# 图片提取由 task_queue/utils/context.py:process_multimodal_messages 在 LLM 调用时处理

context.append(message_with_meta)  # ❌ 包含完整图片
repo.update_context(runtime_id, context)
```

**问题：**
- 数据库保存完整图片
- 每次 LLM 调用时，从数据库读取完整 context
- `process_multimodal_messages` 处理**所有历史图片**
- 发送给 LLM 的消息包含**所有历史图片**

## 🐛 Bug 位置

**不是 Bug，是设计缺陷**

| 组件 | 状态 | 说明 |
|------|------|------|
| `process_multimodal_messages` | ✅ 正常 | 按设计工作 |
| `has_images` | ✅ 正常 | 正确检测图片 |
| `extract_from_result` | ✅ 正常 | 正确提取图片 |
| `append_message_to_context` | ⚠️ 设计问题 | 保存完整图片到数据库 |

## 📝 修复方案

### 方案 A：保存时清理图片（简单但会丢失数据）

**位置：** `gateway/api/internal/runtime.py::append_message_to_context`

```python
from task_queue.utils import multimodal

def append_message_to_context(runtime_id, message, data):
    # 如果是 tool result，清理图片数据
    if message.get("role") in ("tool", "tool_result"):
        content = message.get("content", "")
        try:
            result = json.loads(content) if isinstance(content, str) else content
            
            if isinstance(result, dict):
                # 处理嵌套的 result 字段
                if "result" in result and isinstance(result["result"], dict):
                    inner_result = result["result"]
                    if multimodal.has_images(inner_result):
                        clean_inner = json.loads(multimodal.result_to_text_only(inner_result))
                        result["result"] = clean_inner
                        message["content"] = json.dumps(result)
                elif multimodal.has_images(result):
                    message["content"] = multimodal.result_to_text_only(result)
        except Exception as e:
            logger.warning(f"Failed to clean images: {e}")
    
    # 保存清理后的消息
    context.append(message_with_meta)
    repo.update_context(runtime_id, context)
```

**优点：**
- ✅ 实现简单
- ✅ 立即生效
- ✅ 数据库大小大幅减少

**缺点：**
- ❌ **图片数据永久丢失**
- ❌ **LLM 看不到图片** - 功能完全失效！

### 方案 B：限制历史图片数量（推荐短期方案）

**位置：** `task_queue/utils/context.py::process_multimodal_messages`

```python
def process_multimodal_messages(
    messages: List[Dict[str, Any]], 
    provider: str = "openai",
    max_recent_images: int = 5  # 新参数：只保留最近 N 个图片
) -> List[Dict[str, Any]]:
    """
    处理消息中的多模态内容，限制历史图片数量
    """
    processed = []
    image_count = 0
    
    # 倒序扫描，找出最近的 N 个包含图片的消息
    recent_image_indices = set()
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("role") in ("tool_result", "tool"):
            content = msg.get("content", "")
            try:
                result = json.loads(content) if isinstance(content, str) else content
            except:
                continue
            
            if isinstance(result, dict) and "result" in result:
                inner_result = result["result"]
            else:
                inner_result = result
            
            if isinstance(inner_result, dict) and multimodal.has_images(inner_result):
                if image_count < max_recent_images:
                    recent_image_indices.add(i)
                    image_count += 1
    
    # 正序处理消息
    for i, msg in enumerate(messages):
        role = msg.get("role")
        
        if role in ("tool_result", "tool"):
            content = msg.get("content", "")
            try:
                result = json.loads(content) if isinstance(content, str) else content
            except:
                processed.append(msg)
                continue
            
            if isinstance(result, dict) and "result" in result:
                inner_result = result["result"]
            else:
                inner_result = result
            
            if isinstance(inner_result, dict) and multimodal.has_images(inner_result):
                if i in recent_image_indices:
                    # 处理图片（提取 + 创建 user message）
                    _, images = multimodal.extract_from_result(inner_result)
                    
                    # 生成纯文本版本
                    inner_text_only = multimodal.result_to_text_only(inner_result)
                    
                    if isinstance(result, dict) and "result" in result:
                        sanitized_result = {**result, "result": json.loads(inner_text_only)}
                        text_only = json.dumps(sanitized_result)
                    else:
                        text_only = inner_text_only
                    
                    processed.append({**msg, "content": text_only})
                    
                    if images:
                        tool_name = msg.get("name", "tool")
                        description = f"[Image from {tool_name}]"
                        
                        if provider == "anthropic":
                            img_content = multimodal.to_anthropic_content(images, description)
                        else:
                            img_content = multimodal.to_openai_content(images, description)
                        
                        processed.append({
                            "role": "user",
                            "content": img_content,
                        })
                else:
                    # 旧图片：只保留占位符，不创建 user message
                    inner_text_only = multimodal.result_to_text_only(inner_result)
                    
                    if isinstance(result, dict) and "result" in result:
                        sanitized_result = {**result, "result": json.loads(inner_text_only)}
                        text_only = json.dumps(sanitized_result)
                    else:
                        text_only = inner_text_only
                    
                    processed.append({**msg, "content": text_only})
            else:
                processed.append(msg)
        else:
            processed.append(msg)
    
    return processed
```

**调用时：**

```python
# task_queue/business/llm.py::LLMBusiness.call
processed = process_multimodal_messages(sanitized, provider, max_recent_images=5)
```

**优点：**
- ✅ 图片数据不丢失（仍在数据库）
- ✅ 控制发送给 LLM 的图片数量
- ✅ 防止上下文爆炸
- ✅ 实现相对简单

**缺点：**
- ❌ 数据库仍然保存完整图片（但不影响 LLM）
- ❌ LLM 看不到旧图片

### 方案 C：图片外部存储（推荐长期方案）

详见 `MULTIMODAL_CONTEXT_EXPLOSION_INVESTIGATION.md`

## 🧪 测试验证

### 测试脚本位置

```
/tmp/test_multimodal.py                  - 基础功能测试
/tmp/test_multiple_tool_results.py       - 多个 tool results 测试
/tmp/analyze_real_context.py             - 实际数据分析
/tmp/check_user_message_size.py          - 大小验证
```

### 验证命令

```bash
# 验证多模态处理
python3 /tmp/test_multimodal.py

# 验证实际数据
python3 /tmp/analyze_real_context.py
```

## 📌 总结

### 回答用户的问题

1. **为什么单个工具结果时正常，多个工具结果时失效？**
   - ❌ 这个前提不对
   - ✅ 单个和多个工具结果的处理**都正常**
   - 问题是：多个图片导致**总大小累积**，不是"失效"

2. **是否是循环逻辑的问题？**
   - ✅ 是循环问题，但不是 `process_multimodal_messages` 的循环
   - 是**数据流的循环**：保存完整图片 → 读取 → 处理 → 发送 → 累积

3. **是否是状态管理的问题？**
   - ✅ 是状态管理问题
   - 数据库保存策略导致状态不断累积

4. **精确的 bug 位置？**
   - **不是 Bug**，是设计缺陷
   - 位置：`gateway/api/internal/runtime.py::append_message_to_context`
   - 问题：保存完整图片到数据库

5. **根本原因？**
   - 数据库保存完整图片
   - 每次 LLM 调用都处理所有历史图片
   - 发送给 LLM 的消息包含所有历史图片（data URL 格式）
   - 导致上下文线性增长

6. **修复方案？**
   - **短期**：方案 B（限制历史图片数量）
   - **长期**：方案 C（图片外部存储）
   - **❌ 不推荐方案 A**：会导致功能失效
