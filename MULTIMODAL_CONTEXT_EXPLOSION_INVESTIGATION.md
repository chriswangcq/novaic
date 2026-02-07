# 多模态上下文爆炸问题调查报告

## 问题描述

当有多个工具结果包含图片时，上下文大小会线性增长，导致"上下文爆炸"。

## 调查结果

### 1. 多模态处理流程（当前）

**代码位置：** `novaic-backend/task_queue/utils/context.py::process_multimodal_messages`

**处理流程：**

```
tool result (包含图片 ~600KB)
    ↓
process_multimodal_messages()
    ↓
1. 提取图片数据
2. tool result 中的图片替换为占位符
3. 创建新的 user message，包含图片 data URL
    ↓
结果：总大小几乎不变（-11 bytes）
```

**实际数据验证：**

- Runtime: rt-9b23e58b3bbc
- 原始 context: 696,393 bytes (8 条消息)
- 处理后 context: 696,382 bytes (9 条消息)
- 差异: **-11 bytes (0.0%)**

**新增的 user message 大小：**
- User message: 661,919 bytes
- 其中 base64 图片数据: 661,772 bytes

### 2. 根本原因

`process_multimodal_messages` 的设计目标是：
- 将 tool result 中的图片数据提取出来
- 作为单独的 user message 发送给 LLM（符合 LLM API 规范）

**问题：**
1. 虽然 tool result 中的图片被替换为占位符
2. 但图片数据以 **data URL** 形式添加到 user message 中
3. **总大小没有减少**

### 3. 上下文爆炸场景

**场景 1：单个对话中多个截图**
```
Round 1: screenshot → 600KB
Round 2: screenshot → 600KB
Round 3: screenshot → 600KB
...
Total: 3MB+ (线性增长)
```

**场景 2：一次调用多个 tool calls（都返回图片）**
```
Assistant: tool_calls=[screenshot, screenshot, screenshot]
    ↓
3 个 tool results (每个 600KB)
    ↓
处理后：3 个 user messages (总共 1.8MB)
```

### 4. 代码验证

**测试文件：** `/tmp/analyze_real_context.py`

```python
# 实际数据
原始 context 消息数: 8
处理后 context 消息数: 9
图片 user messages: 1

# 大小对比
原始: 696,393 bytes
处理后: 696,382 bytes
差异: -11 bytes (0.0%)

# 新增的 user message
Role: user
Content: [
  {type: "image_url", url: "data:image/png;base64,<661772 bytes>"},
  {type: "text", text: "[Image from tool]"}
]
```

## 问题分析

### process_multimodal_messages 是否有 Bug？

**答案：否**

`process_multimodal_messages` 的行为是**符合设计预期的**：

1. ✅ 正确检测图片（通过 `has_images`）
2. ✅ 正确提取图片（通过 `extract_from_result`）
3. ✅ 正确清理 tool result（替换为占位符）
4. ✅ 正确创建 user message（符合 LLM API 规范）

### 真正的问题

**问题不在于多模态处理逻辑，而在于架构设计：**

1. **数据库保存策略**
   - 当前：数据库保存原始 tool result（包含完整图片）
   - 位置：`gateway/api/internal/runtime.py::append_message_to_context`
   - 注释：`# 保持原始 tool result（包含完整图片数据）`

2. **LLM 调用时的处理**
   - 当前：从数据库读取 context → `process_multimodal_messages` → 发送给 LLM
   - 每次都重新处理图片（提取 + 创建 user message）
   - 结果：发送给 LLM 的消息包含完整图片数据

3. **上下文累积**
   - Round 1: 1 个图片 (600KB)
   - Round 2: 2 个图片 (1.2MB)
   - Round 3: 3 个图片 (1.8MB)
   - ...历史图片始终在 context 中

## 修复方案

### 方案 1：在保存时清理图片数据（推荐）

**目标：** 数据库只保存占位符，不保存完整图片

**修改位置：**
1. `gateway/api/internal/runtime.py::append_message_to_context`
2. 在保存前调用 `multimodal.result_to_text_only` 清理图片

**代码示例：**

```python
# gateway/api/internal/runtime.py
from task_queue.utils import multimodal

def append_message_to_context(runtime_id, message, data):
    # ... existing code ...
    
    # 清理图片数据（如果是 tool result）
    if message.get("role") in ("tool", "tool_result"):
        content = message.get("content", "")
        try:
            result = json.loads(content) if isinstance(content, str) else content
            
            # 检查并清理嵌套的 result 字段
            if isinstance(result, dict):
                if "result" in result and isinstance(result["result"], dict):
                    inner_result = result["result"]
                    if multimodal.has_images(inner_result):
                        # 清理图片数据
                        clean_inner = json.loads(multimodal.result_to_text_only(inner_result))
                        result["result"] = clean_inner
                        message["content"] = json.dumps(result)
                elif multimodal.has_images(result):
                    # 直接清理
                    message["content"] = multimodal.result_to_text_only(result)
        except:
            pass
    
    message_with_meta = {
        **message,
        "_round_id": round_id,
        "_message_type": message_type,
    }
    # ... rest of the code ...
```

**优点：**
- ✅ 数据库大小大幅减少（不保存图片）
- ✅ Context 不会因为图片而爆炸
- ✅ LLM 调用时仍然能通过 `process_multimodal_messages` 处理（占位符）

**缺点：**
- ❌ **图片数据永久丢失** - LLM 看不到图片！
- ❌ 这会导致功能完全失效

### 方案 2：图片外部存储 + 引用（最佳）

**目标：** 图片存储在文件系统/对象存储，context 只保存引用

**架构：**

```
tool result (图片 base64)
    ↓
保存时：
1. 提取图片，保存到文件系统（/tmp/images/<runtime_id>/<msg_id>.png）
2. tool result 中替换为引用：{"type": "image_ref", "ref": "<msg_id>"}
    ↓
LLM 调用时：
1. 从文件系统加载图片
2. 转换为 data URL
3. 创建 user message
```

**实现：**

```python
# 新文件：task_queue/utils/image_storage.py
import os
import base64
from pathlib import Path

IMAGES_DIR = Path("/tmp/novaic/images")

def save_image(runtime_id: str, msg_id: str, image_data: str, mime_type: str = "image/png") -> str:
    """保存图片到文件系统，返回引用 ID"""
    runtime_dir = IMAGES_DIR / runtime_id
    runtime_dir.mkdir(parents=True, exist_ok=True)
    
    ext = mime_type.split("/")[-1]
    image_path = runtime_dir / f"{msg_id}.{ext}"
    
    # 解码 base64 并保存
    image_bytes = base64.b64decode(image_data)
    image_path.write_bytes(image_bytes)
    
    return f"image_ref://{runtime_id}/{msg_id}.{ext}"

def load_image(ref: str) -> tuple[str, str]:
    """从引用加载图片，返回 (base64_data, mime_type)"""
    # ref 格式: image_ref://<runtime_id>/<msg_id>.png
    path_part = ref.replace("image_ref://", "")
    image_path = IMAGES_DIR / path_part
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {ref}")
    
    # 读取并编码为 base64
    image_bytes = image_path.read_bytes()
    base64_data = base64.b64encode(image_bytes).decode()
    
    # 推断 mime_type
    ext = image_path.suffix.lstrip(".")
    mime_type = f"image/{ext}"
    
    return base64_data, mime_type
```

```python
# 修改：gateway/api/internal/runtime.py
from task_queue.utils import image_storage

def append_message_to_context(runtime_id, message, data):
    # ... existing code ...
    
    # 处理图片（如果是 tool result）
    if message.get("role") in ("tool", "tool_result"):
        content = message.get("content", "")
        try:
            result = json.loads(content) if isinstance(content, str) else content
            
            if isinstance(result, dict):
                # 处理嵌套的 result
                if "result" in result and isinstance(result["result"], dict):
                    inner_result = result["result"]
                    target = inner_result
                    is_nested = True
                else:
                    target = result
                    is_nested = False
                
                # 检查是否有图片
                if multimodal.has_images(target):
                    # 提取并保存图片
                    text, images = multimodal.extract_from_result(target)
                    
                    msg_id = message.get("tool_call_id", f"msg_{uuid.uuid4().hex}")
                    
                    # 替换图片为引用
                    if "content" in target and isinstance(target["content"], list):
                        new_content = []
                        for item in target["content"]:
                            if item.get("type") == "image":
                                # 保存图片
                                ref = image_storage.save_image(
                                    runtime_id,
                                    msg_id,
                                    item.get("data", ""),
                                    item.get("mimeType", "image/png")
                                )
                                # 替换为引用
                                new_content.append({
                                    "type": "image_ref",
                                    "ref": ref,
                                    "mimeType": item.get("mimeType", "image/png")
                                })
                            else:
                                new_content.append(item)
                        
                        target["content"] = new_content
                        
                        # 更新消息
                        if is_nested:
                            result["result"] = target
                        message["content"] = json.dumps(result)
        except Exception as e:
            logger.warning(f"Failed to process images: {e}")
    
    # ... rest of the code ...
```

```python
# 修改：task_queue/utils/context.py::process_multimodal_messages
def process_multimodal_messages(messages, provider="openai"):
    # ... existing code ...
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role in ("tool_result", "tool"):
            try:
                result = json.loads(content) if isinstance(content, str) else content
            except:
                result = {"content": content}
            
            # 解包嵌套
            if isinstance(result, dict) and "result" in result:
                inner_result = result["result"]
            else:
                inner_result = result
            
            # 检查是否有图片引用
            if isinstance(inner_result, dict) and "content" in inner_result:
                content_array = inner_result["content"]
                if isinstance(content_array, list):
                    images_to_load = []
                    
                    for item in content_array:
                        if isinstance(item, dict) and item.get("type") == "image_ref":
                            # 加载图片
                            ref = item.get("ref")
                            try:
                                image_data, mime_type = image_storage.load_image(ref)
                                images_to_load.append({
                                    "data": image_data,
                                    "mime_type": mime_type
                                })
                            except Exception as e:
                                logger.warning(f"Failed to load image {ref}: {e}")
                    
                    if images_to_load:
                        # 添加 tool result（不含图片）
                        processed.append(msg)
                        
                        # 添加图片作为 user message
                        tool_name = msg.get("name", "tool")
                        description = f"[Image from {tool_name}]"
                        
                        if provider == "anthropic":
                            img_content = multimodal.to_anthropic_content(images_to_load, description)
                        else:
                            img_content = multimodal.to_openai_content(images_to_load, description)
                        
                        processed.append({
                            "role": "user",
                            "content": img_content,
                        })
                        continue
            
            # 原有逻辑（处理直接包含图片的情况）
            # ... existing code ...
```

**优点：**
- ✅ 数据库大小大幅减少（只保存引用）
- ✅ 图片数据不丢失（存储在文件系统）
- ✅ LLM 调用时按需加载图片
- ✅ 可以实现图片缓存、清理策略

**缺点：**
- ❌ 需要管理外部存储（文件清理、备份等）
- ❌ 实现复杂度较高

### 方案 3：限制历史图片数量

**目标：** 只保留最近 N 轮的图片，旧图片清理

**实现：**

```python
# task_queue/utils/context.py
def process_multimodal_messages(messages, provider="openai", max_image_rounds=3):
    """
    处理多模态消息，限制图片数量
    
    Args:
        messages: 消息列表
        provider: LLM 提供商
        max_image_rounds: 保留最近 N 轮的图片
    """
    # 1. 识别包含图片的 tool results
    # 2. 只处理最近 N 轮的图片
    # 3. 旧图片替换为文本描述
```

## 推荐方案

**短期（Quick Fix）：方案 3**
- 限制历史图片数量
- 实现简单，立即生效

**长期（最佳实践）：方案 2**
- 图片外部存储
- 彻底解决问题
- 支持大规模使用

## 测试验证

### 创建测试用例

```python
# test_multimodal_context_explosion.py
import json
from task_queue.utils.context import process_multimodal_messages

def test_multiple_screenshots():
    """测试多个截图的处理"""
    messages = []
    
    # 添加 5 个截图
    for i in range(5):
        messages.extend([
            {"role": "user", "content": f"Screenshot {i+1}"},
            {
                "role": "assistant",
                "tool_calls": [{
                    "id": f"call_{i}",
                    "function": {"name": "screenshot"}
                }]
            },
            {
                "role": "tool",
                "tool_call_id": f"call_{i}",
                "name": "screenshot",
                "content": json.dumps({
                    "success": True,
                    "content": [
                        {"type": "text", "text": f"Screenshot {i+1}"},
                        {"type": "image", "data": "iVBOR..." * 10000}  # ~600KB
                    ]
                })
            }
        ])
    
    # 处理前后大小对比
    original_size = len(json.dumps(messages))
    processed = process_multimodal_messages(messages)
    processed_size = len(json.dumps(processed))
    
    print(f"Original: {original_size:,} bytes")
    print(f"Processed: {processed_size:,} bytes")
    print(f"Difference: {processed_size - original_size:,} bytes")
    
    # 验证
    assert processed_size < original_size * 1.1, "Size should not increase significantly"
```

## 相关文件

- `novaic-backend/task_queue/utils/context.py::process_multimodal_messages` - 多模态处理
- `novaic-backend/task_queue/utils/multimodal.py` - 图片检测和提取
- `novaic-backend/task_queue/business/llm.py::LLMBusiness.call` - LLM 调用
- `novaic-backend/gateway/api/internal/runtime.py::append_message_to_context` - 消息保存

## 结论

1. **`process_multimodal_messages` 没有 Bug**
   - 功能正常，按设计工作
   
2. **问题是架构设计**
   - 数据库保存完整图片
   - 每次 LLM 调用都携带历史图片
   - 导致上下文线性增长

3. **修复方向**
   - 短期：限制历史图片数量
   - 长期：图片外部存储 + 引用

4. **不是"多个工具结果时失效"**
   - 多模态处理对单个和多个工具结果都正常工作
   - 问题是图片数据的累积，不是处理失效
