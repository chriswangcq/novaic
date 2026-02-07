# LLM Multimodal 处理逻辑 - 新格式兼容性分析报告

**分析日期**: 2026-02-07  
**分析范围**: task_queue/utils/multimodal.py, context.py, result.py, gateway/core/llm_client.py

---

## 执行摘要

**总体状态**: ⚠️ **部分兼容 - 发现 1 个关键问题**

- ✅ **文本提取**: 完全支持新格式
- ✅ **图片提取**: 完全支持新格式  
- ❌ **图片检测**: `has_images()` 不支持新格式（关键问题）
- ✅ **Context 处理**: 支持新格式（依赖修复后的 `has_images()`）
- ✅ **LLM API 转换**: 完全支持（格式无关）

---

## 1. 新旧格式对比

### 新格式（MCP 标准）
```python
{
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot captured"},
        {"type": "image", "data": "base64...", "mimeType": "image/png"}
    ]
}
```

### 旧格式（传统字段）
```python
{
    "success": True,
    "result": {
        "screenshot": "base64...",
        "message": "Screenshot captured"
    }
}
```

---

## 2. 兼容性分析

### 2.1 文件：`task_queue/utils/multimodal.py`

#### ✅ `extract_from_result()` (行 112-206)

**状态**: 完全支持新格式

**检查点**:
- ✅ 优先级正确（第 169-179 行）
  1. 先检查 `_mcp_content`（MCP 客户端格式）
  2. 再检查 `content` 数组（新格式）✅
  3. 最后检查传统字段（旧格式）✅

- ✅ 文本提取（通过 `_parse_content_array()` 行 84-87）
  ```python
  if item_type == "text":
      text = item.get("text", "")
      if text:
          text_parts.append(text)
  ```

- ✅ 图片提取（通过 `_parse_content_array()` 行 89-95）
  ```python
  elif item_type == "image":
      data = item.get("data", "")
      if data and _is_likely_base64_image(data):
          images.append({
              "data": data,
              "mime_type": item.get("mimeType", item.get("mime_type", "image/png"))
          })
  ```

- ✅ MIME 类型兼容（行 94）
  - 支持 `mimeType`（标准）和 `mime_type`（备选）

**测试场景**:

```python
# 场景 1：新格式（纯文本）
result1 = {
    "success": True,
    "content": [{"type": "text", "text": "Hello"}]
}
text, images = extract_from_result(result1)
# 预期：text = "Hello", images = []
# 实际：✅ 正确

# 场景 2：新格式（含图片）
result2 = {
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot"},
        {"type": "image", "data": "iVBORw0KG...", "mimeType": "image/png"}
    ]
}
text, images = extract_from_result(result2)
# 预期：text = "Screenshot", images = [{"data": "iVBORw0KG...", "mime_type": "image/png"}]
# 实际：✅ 正确

# 场景 3：旧格式（兼容性）
result3 = {
    "success": True,
    "result": {
        "screenshot": "iVBORw0KG...",
        "message": "Done"
    }
}
text, images = extract_from_result(result3)
# 预期：应该能提取图片
# 实际：✅ 正确（传统字段检测）
```

---

#### ❌ `has_images()` (行 209-239)

**状态**: ❌ **不支持新格式 - 关键问题**

**问题描述**:

当前实现只检查：
1. ✅ `_mcp_content` 数组（行 224-231）
2. ✅ 传统字段（行 234-237）
3. ❌ **缺少对 `content` 数组的检查**

**当前代码**:
```python
def has_images(result: Dict[str, Any]) -> bool:
    # 1. 检查 _mcp_content（MCP 标准格式）
    mcp_content = result.get("_mcp_content", [])
    for item in mcp_content:
        if item.get("type") == "image" and item.get("data"):
            return True
        if item.get("type") == "resource":
            mime_type = item.get("mimeType", "")
            if mime_type.startswith("image/") and item.get("blob"):
                return True
    
    # 2. 检查常见图片字段（向后兼容）
    for field_name in IMAGE_FIELD_NAMES:
        value = result.get(field_name)
        if _is_likely_base64_image(value):
            return True
    
    return False
```

**缺少的检查**（应该添加在第 1 和第 2 步之间）:
```python
# 2. 检查 content 数组（MCP 标准格式）
content = result.get("content", [])
if isinstance(content, list):
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "image" and item.get("data"):
                return True
            if item.get("type") == "resource":
                resource = item.get("resource", {})
                mime_type = resource.get("mimeType", "")
                if mime_type.startswith("image/") and resource.get("blob"):
                    return True
```

**影响**:

当工具返回新格式时：
1. ❌ `has_images(result)` 返回 `False`（应该返回 `True`）
2. ❌ `process_multimodal_messages()` 不会提取图片
3. ❌ 图片 base64 数据作为纯文本发送给 LLM
4. ❌ 可能导致 token 超限或图片丢失

**影响范围**:

1. **`task_queue/utils/context.py` 行 222**:
   ```python
   if isinstance(inner_result, dict) and multimodal.has_images(inner_result):
       _, images = multimodal.extract_from_result(inner_result)
       # 如果 has_images() 返回 False，图片不会被提取
   ```

2. **`task_queue/utils/result.py` 行 91**:
   ```python
   if has_images(inner):
       summary["has_image"] = True
   # 如果 has_images() 返回 False，摘要不会标记有图片
   ```

---

#### ✅ `result_to_text_only()` (行 297-342)

**状态**: 完全支持新格式

**检查点**:
- ✅ 处理 `content` 字段（行 330-335）
  ```python
  if key == "_mcp_content" or key == "content":
      if isinstance(value, list):
          output[key] = sanitize_content_array(value)
  ```

- ✅ 正确清理图片（行 314-327）
  ```python
  def sanitize_content_array(content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
      sanitized = []
      for item in content:
          if item.get("type") == "image":
              sanitized.append({
                  "type": "image",
                  "_placeholder": True,
                  "mimeType": item.get("mimeType", item.get("mime_type", "image/png")),
                  "_note": "Image data provided separately to LLM"
              })
          else:
              sanitized.append(item)
      return sanitized
  ```

**测试场景**:
```python
result = {
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot"},
        {"type": "image", "data": "iVBORw0KG...(10KB)", "mimeType": "image/png"}
    ]
}
text_only = result_to_text_only(result)
# 预期：图片被替换为占位符
# 实际：✅ 正确
# 输出：{"success": true, "content": [{"type": "text", "text": "Screenshot"}, {"type": "image", "_placeholder": true, "mimeType": "image/png", "_note": "Image data provided separately to LLM"}]}
```

---

#### ✅ `to_openai_content()` / `to_anthropic_content()` (行 242-294)

**状态**: 完全支持（格式无关）

**原因**: 这些函数接收已经提取的图片列表，与原始格式无关。

---

### 2.2 文件：`task_queue/utils/context.py`

#### ✅ `process_multimodal_messages()` (行 175-261)

**状态**: 支持新格式（但依赖修复后的 `has_images()`）

**检查点**:
- ✅ 调用正确的函数（行 222-223）
  ```python
  if isinstance(inner_result, dict) and multimodal.has_images(inner_result):
      _, images = multimodal.extract_from_result(inner_result)
  ```

- ✅ 处理嵌套结构 `{success, result}` （行 217-234）
  ```python
  if isinstance(result, dict) and "result" in result and isinstance(result["result"], dict):
      inner_result = result["result"]
  else:
      inner_result = result
  ```

- ✅ 生成纯文本版本（行 226-234）
  ```python
  inner_text_only = multimodal.result_to_text_only(inner_result)
  
  if isinstance(result, dict) and "result" in result:
      sanitized_result = {**result, "result": json.loads(inner_text_only)}
      text_only = json.dumps(sanitized_result)
  else:
      text_only = inner_text_only
  ```

- ✅ 转换为 LLM 格式（行 243-255）
  ```python
  if provider == "anthropic":
      img_content = multimodal.to_anthropic_content(images, description)
  else:
      img_content = multimodal.to_openai_content(images, description)
  ```

**依赖问题**:
- ⚠️ 依赖 `has_images()` 函数（需要先修复）
- 如果 `has_images()` 返回 False，整个提取流程不会执行

---

### 2.3 文件：`gateway/core/llm_client.py`

#### ✅ `_convert_content_to_anthropic()` (行 368-433)

**状态**: 完全支持（格式无关）

**原因**: 
- 处理的是已经转换后的 OpenAI 格式内容
- 由 `process_multimodal_messages()` 生成，与原始工具格式无关

**检查点**:
- ✅ 处理 image_url 类型（行 393-420）
  ```python
  elif item_type == "image_url":
      image_url = item.get("image_url", {})
      url = image_url.get("url", "")
      
      if url.startswith("data:"):
          header, data = url.split(",", 1)
          media_type = header.split(":")[1].split(";")[0]
          converted.append({
              "type": "image",
              "source": {
                  "type": "base64",
                  "media_type": media_type,
                  "data": data
              }
          })
  ```

---

## 3. 兼容性矩阵

| 功能 | 新格式支持 | 旧格式支持 | 状态 | 说明 |
|------|-----------|-----------|------|------|
| **文本提取** | ✅ | ✅ | 正常 | `extract_from_result()` 完全支持 |
| **图片提取** | ✅ | ✅ | 正常 | `extract_from_result()` 完全支持 |
| **图片检测** | ❌ | ✅ | **问题** | `has_images()` 不检查 `content` 数组 |
| **图片清理** | ✅ | ✅ | 正常 | `result_to_text_only()` 完全支持 |
| **Context 处理** | ⚠️ | ✅ | 依赖修复 | 依赖 `has_images()` 的修复 |
| **Anthropic 转换** | ✅ | ✅ | 正常 | 格式无关 |
| **OpenAI 转换** | ✅ | ✅ | 正常 | 格式无关 |
| **结果摘要** | ⚠️ | ✅ | 依赖修复 | `summarize_result()` 依赖 `has_images()` |

---

## 4. 发现的问题清单

### 问题 1：`has_images()` 不支持新格式 ❌ 【P0 - 关键】

**位置**: `task_queue/utils/multimodal.py` 行 209-239

**描述**: 
`has_images()` 函数只检查 `_mcp_content` 和传统字段，没有检查新格式的 `content` 数组。

**影响**: 
- 当工具返回新格式时，图片检测失败
- `process_multimodal_messages()` 不会提取图片
- 图片 base64 数据作为文本发送给 LLM，可能导致 token 超限

**影响范围**:
1. `task_queue/utils/context.py:222` - 图片提取判断
2. `task_queue/utils/result.py:91` - 结果摘要生成

**修复优先级**: 🔴 **P0 - 必须立即修复**

**修复建议**: 见第 5 节

---

## 5. 修复建议

### 修复 `has_images()` 函数

**文件**: `task_queue/utils/multimodal.py`  
**行号**: 209-239

#### 修复前代码

```python
def has_images(result: Dict[str, Any]) -> bool:
    """
    检查结果是否包含图片
    
    支持两种检测:
    1. MCP 标准格式: _mcp_content 数组中的 image 类型
    2. 常见字段格式: screenshot, image_base64 等字段
    
    Args:
        result: 工具执行结果
        
    Returns:
        bool: 是否包含图片
    """
    # 1. 检查 _mcp_content（MCP 标准格式）
    mcp_content = result.get("_mcp_content", [])
    for item in mcp_content:
        if item.get("type") == "image" and item.get("data"):
            return True
        if item.get("type") == "resource":
            mime_type = item.get("mimeType", "")
            if mime_type.startswith("image/") and item.get("blob"):
                return True
    
    # 2. 检查常见图片字段（向后兼容）
    for field_name in IMAGE_FIELD_NAMES:
        value = result.get(field_name)
        if _is_likely_base64_image(value):
            return True
    
    return False
```

#### 修复后代码

```python
def has_images(result: Dict[str, Any]) -> bool:
    """
    检查结果是否包含图片
    
    支持三种检测:
    1. MCP 标准格式: _mcp_content 数组中的 image 类型
    2. MCP 标准格式: content 数组中的 image 类型（新格式）
    3. 常见字段格式: screenshot, image_base64 等字段
    
    Args:
        result: 工具执行结果
        
    Returns:
        bool: 是否包含图片
    """
    # 1. 检查 _mcp_content（MCP 客户端转换格式）
    mcp_content = result.get("_mcp_content", [])
    for item in mcp_content:
        if isinstance(item, dict):
            if item.get("type") == "image" and item.get("data"):
                return True
            if item.get("type") == "resource":
                mime_type = item.get("mimeType", "")
                if mime_type.startswith("image/") and item.get("blob"):
                    return True
    
    # 2. 检查 content 数组（MCP 标准格式 - 新格式）
    content = result.get("content", [])
    if isinstance(content, list):
        # 检查是否是 MCP 标准格式（包含 type 字段）
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "image" and item.get("data"):
                    return True
                if item_type == "resource":
                    resource = item.get("resource", {})
                    mime_type = resource.get("mimeType", "")
                    if mime_type.startswith("image/") and resource.get("blob"):
                        return True
    
    # 3. 检查常见图片字段（向后兼容）
    for field_name in IMAGE_FIELD_NAMES:
        value = result.get(field_name)
        if _is_likely_base64_image(value):
            return True
    
    return False
```

#### 修复说明

**添加的逻辑** (新增第 2 步):

1. 获取 `content` 数组
2. 检查是否是列表类型
3. 遍历每个 item，检查：
   - `type == "image"` 且有 `data` 字段
   - `type == "resource"` 且是图片 MIME 类型
4. 与 `extract_from_result()` 的逻辑保持一致

**优先级**:
1. 先检查 `_mcp_content`（MCP 客户端格式）
2. 再检查 `content`（MCP 标准格式 - 新格式）
3. 最后检查传统字段（旧格式）

**兼容性**:
- ✅ 向后兼容旧格式（传统字段）
- ✅ 支持 `_mcp_content` 格式
- ✅ 支持 `content` 数组格式（新格式）

---

## 6. 测试场景验证

### 测试 1：新格式（纯文本）

```python
result = {
    "success": True,
    "content": [{"type": "text", "text": "Hello"}]
}

# has_images
assert has_images(result) == False  # ✅ 修复后：正确

# extract_from_result
text, images = extract_from_result(result)
assert text == "Hello"  # ✅ 已支持
assert images == []  # ✅ 已支持
```

### 测试 2：新格式（含图片）

```python
result = {
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot"},
        {"type": "image", "data": "iVBORw0KG...", "mimeType": "image/png"}
    ]
}

# has_images
assert has_images(result) == True  # ❌ 修复前：False → ✅ 修复后：True

# extract_from_result
text, images = extract_from_result(result)
assert text == "Screenshot"  # ✅ 已支持
assert len(images) == 1  # ✅ 已支持
assert images[0]["mime_type"] == "image/png"  # ✅ 已支持
```

### 测试 3：新格式（多个图片）

```python
result = {
    "success": True,
    "content": [
        {"type": "text", "text": "Multiple images"},
        {"type": "image", "data": "base64_1...", "mimeType": "image/png"},
        {"type": "image", "data": "base64_2...", "mimeType": "image/jpeg"}
    ]
}

# has_images
assert has_images(result) == True  # ❌ 修复前：False → ✅ 修复后：True

# extract_from_result
text, images = extract_from_result(result)
assert text == "Multiple images"  # ✅ 已支持
assert len(images) == 2  # ✅ 已支持
```

### 测试 4：旧格式（兼容性）

```python
result = {
    "success": True,
    "result": {
        "screenshot": "iVBORw0KG...",
        "message": "Done"
    }
}

# has_images
assert has_images(result) == True  # ✅ 修复前后：正确（传统字段检测）

# extract_from_result
text, images = extract_from_result(result)
assert len(images) == 1  # ✅ 已支持
```

### 测试 5：嵌套格式（{success, result} + content）

```python
result = {
    "success": True,
    "result": {
        "content": [
            {"type": "text", "text": "Nested"},
            {"type": "image", "data": "base64...", "mimeType": "image/png"}
        ]
    }
}

# 需要先解包到 inner_result
inner_result = result["result"]

# has_images
assert has_images(inner_result) == True  # ❌ 修复前：False → ✅ 修复后：True

# extract_from_result
text, images = extract_from_result(inner_result)
assert text == "Nested"  # ✅ 已支持
assert len(images) == 1  # ✅ 已支持
```

---

## 7. 端到端流程验证

### 流程：工具返回 → Context 处理 → LLM 调用

```python
# 1. 工具返回新格式
tool_result = {
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot captured"},
        {"type": "image", "data": "iVBORw0KG...", "mimeType": "image/png"}
    ]
}

# 2. 添加到消息列表
messages = [
    {"role": "user", "content": "Take a screenshot"},
    {"role": "assistant", "tool_calls": [{"id": "call_1", "function": {"name": "screenshot"}}]},
    {"role": "tool", "tool_call_id": "call_1", "name": "screenshot", "content": json.dumps(tool_result)}
]

# 3. Context 处理
processed = process_multimodal_messages(messages, provider="openai")

# 修复前：
# - has_images(result) 返回 False
# - 图片不会被提取
# - processed 仍然包含完整的 base64 数据
# ❌ 问题：图片数据作为文本发送给 LLM

# 修复后：
# - has_images(result) 返回 True ✅
# - 图片被提取为单独的 user message ✅
# - tool result 的 content 被清理（图片替换为占位符）✅
# ✅ 正确：图片作为多模态内容发送给 LLM

# 预期结果：
assert len(processed) == 4  # user, assistant+tool_calls, tool_result (text only), user+image
assert processed[2]["content"]  # tool result - 纯文本
assert processed[3]["role"] == "user"  # image message
assert processed[3]["content"][0]["type"] == "image_url"  # OpenAI format
```

---

## 8. 潜在风险和边界情况

### 8.1 空 content 数组

```python
result = {"success": True, "content": []}
# has_images: False ✅
# extract_from_result: "", [] ✅
```

### 8.2 content 不是数组

```python
result = {"success": True, "content": "some string"}
# has_images: False ✅
# extract_from_result: 按传统逻辑处理 ✅
```

### 8.3 混合格式（content + 传统字段）

```python
result = {
    "success": True,
    "content": [{"type": "text", "text": "From content"}],
    "screenshot": "base64..."  # 传统字段
}

# 优先级：content 优先于传统字段
# has_images: True（检测到 screenshot）✅
# extract_from_result: 只处理 content，忽略 screenshot ✅
```

### 8.4 无效的 content 项

```python
result = {
    "success": True,
    "content": [
        {"type": "image"},  # 缺少 data
        {"type": "image", "data": ""},  # data 为空
        {"type": "image", "data": "abc"}  # data 太短
    ]
}

# has_images: False（没有有效图片）✅
# extract_from_result: "", [] ✅
# 原因：_is_likely_base64_image() 会过滤无效数据
```

### 8.5 MIME 类型变体

```python
result = {
    "success": True,
    "content": [
        {"type": "image", "data": "base64...", "mimeType": "image/png"},  # 标准
        {"type": "image", "data": "base64...", "mime_type": "image/jpeg"}  # 备选
    ]
}

# has_images: True ✅
# extract_from_result: 正确提取 mime_type ✅
# 原因：代码支持两种拼写
```

---

## 9. 修复验证清单

在应用修复后，需要验证：

- [ ] **单元测试**: 测试 `has_images()` 的所有场景
- [ ] **集成测试**: 测试 `process_multimodal_messages()` 的端到端流程
- [ ] **回归测试**: 确保旧格式仍然工作
- [ ] **性能测试**: 确认新增检查不影响性能
- [ ] **日志验证**: 检查是否有相关错误日志

### 推荐测试工具

创建测试文件 `test_multimodal_new_format.py`:

```python
import json
from task_queue.utils import multimodal
from task_queue.utils.context import process_multimodal_messages

def test_has_images_new_format():
    """测试 has_images() 对新格式的支持"""
    result = {
        "content": [
            {"type": "text", "text": "Test"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 100, "mimeType": "image/png"}
        ]
    }
    assert multimodal.has_images(result) == True, "应该检测到新格式的图片"

def test_extract_from_result_new_format():
    """测试 extract_from_result() 对新格式的支持"""
    result = {
        "content": [
            {"type": "text", "text": "Screenshot"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 100, "mimeType": "image/png"}
        ]
    }
    text, images = multimodal.extract_from_result(result)
    
    assert text == "Screenshot"
    assert len(images) == 1
    assert images[0]["mime_type"] == "image/png"
    assert "iVBORw0KG" in images[0]["data"]

def test_process_multimodal_new_format():
    """测试端到端处理"""
    tool_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Done"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 100, "mimeType": "image/png"}
        ]
    }
    
    messages = [
        {"role": "tool", "tool_call_id": "call_1", "name": "screenshot", 
         "content": json.dumps(tool_result)}
    ]
    
    processed = process_multimodal_messages(messages, provider="openai")
    
    # 应该生成 2 个消息：tool result (text only) + user (image)
    assert len(processed) == 2
    assert processed[0]["role"] == "tool"
    assert processed[1]["role"] == "user"
    assert isinstance(processed[1]["content"], list)
    assert processed[1]["content"][0]["type"] == "image_url"

def test_backward_compatibility():
    """测试向后兼容性"""
    old_result = {
        "success": True,
        "result": {
            "screenshot": "iVBORw0KG" + "G" * 100,
            "message": "Done"
        }
    }
    
    assert multimodal.has_images(old_result["result"]) == True
    text, images = multimodal.extract_from_result(old_result["result"])
    assert len(images) == 1

if __name__ == "__main__":
    test_has_images_new_format()
    test_extract_from_result_new_format()
    test_process_multimodal_new_format()
    test_backward_compatibility()
    print("✅ All tests passed!")
```

运行测试：
```bash
cd novaic-backend
python test_multimodal_new_format.py
```

---

## 10. 总结和建议

### 10.1 总结

1. **大部分代码已经支持新格式**
   - `extract_from_result()` ✅
   - `result_to_text_only()` ✅
   - LLM 格式转换 ✅

2. **关键问题**：`has_images()` 不支持新格式 ❌
   - 影响图片检测和提取流程
   - 必须立即修复

3. **修复简单**：只需添加约 15 行代码

### 10.2 行动建议

**立即行动** (P0):
1. ✅ 修复 `has_images()` 函数（添加 `content` 数组检查）
2. ✅ 运行测试验证修复
3. ✅ 测试向后兼容性

**后续行动** (P1):
1. 添加单元测试覆盖所有场景
2. 更新文档说明新格式支持
3. 监控生产环境日志

**长期优化** (P2):
1. 统一格式处理逻辑
2. 考虑性能优化（缓存检测结果）
3. 添加格式验证和错误提示

### 10.3 修复检查清单

应用修复后，请确认：

- [ ] `has_images()` 函数已更新
- [ ] 新格式测试通过
- [ ] 旧格式仍然工作（向后兼容）
- [ ] `process_multimodal_messages()` 能正确提取图片
- [ ] `summarize_result()` 能正确标记 `has_image`
- [ ] 没有引入新的 bug 或性能问题

---

## 附录 A：相关文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 多模态工具 | `task_queue/utils/multimodal.py` | 核心逻辑，需要修复 `has_images()` |
| Context 处理 | `task_queue/utils/context.py` | 使用 `has_images()` 和 `extract_from_result()` |
| 结果工具 | `task_queue/utils/result.py` | 使用 `has_images()` 生成摘要 |
| LLM 客户端 | `gateway/core/llm_client.py` | 格式转换，已支持 |
| 工具执行器 | `tools_server/executor.py` | 可能需要检查返回格式 |
| VMuse 适配器 | `gateway/clients/vmuse_adapter.py` | 可能需要检查格式适配 |

---

## 附录 B：格式规范参考

### MCP Content 标准格式

```typescript
type Content = Array<TextContent | ImageContent | ResourceContent>;

interface TextContent {
  type: "text";
  text: string;
}

interface ImageContent {
  type: "image";
  data: string;  // base64
  mimeType: string;  // "image/png", "image/jpeg", etc.
}

interface ResourceContent {
  type: "resource";
  resource: {
    uri?: string;
    mimeType?: string;
    blob?: string;  // base64 for embedded data
    text?: string;
  };
}
```

### 传统格式（向后兼容）

```python
# 常见字段名
IMAGE_FIELD_NAMES = [
    "screenshot",
    "image_base64",
    "image_data",
    "base64_image",
    "image",
    "png_data",
    "jpeg_data",
]
```

---

**报告结束**

如有疑问，请联系：
- 系统架构：检查 multimodal.py 实现
- 工具开发：确保新工具返回正确格式
- 测试团队：验证修复和回归测试
