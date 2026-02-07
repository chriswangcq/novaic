# Multimodal 处理快速参考

**更新日期**: 2026-02-07  
**状态**: ✅ 新格式完全支持

---

## 格式支持矩阵

| 格式 | has_images() | extract_from_result() | result_to_text_only() | Status |
|------|--------------|----------------------|----------------------|--------|
| **新格式** (`content` 数组) | ✅ | ✅ | ✅ | 完全支持 |
| **MCP 客户端** (`_mcp_content`) | ✅ | ✅ | ✅ | 完全支持 |
| **传统字段** (`screenshot` 等) | ✅ | ✅ | ✅ | 完全支持 |

---

## 工具返回格式规范

### 推荐：新格式（MCP 标准）

```python
{
    "success": True,
    "content": [
        {"type": "text", "text": "操作完成"},
        {"type": "image", "data": "base64...", "mimeType": "image/png"}
    ]
}
```

**优点**:
- ✅ 标准化格式
- ✅ 支持多个图片
- ✅ 明确的 MIME 类型
- ✅ 可扩展（支持其他类型）

### 兼容：传统格式

```python
{
    "success": True,
    "screenshot": "base64...",
    "message": "操作完成"
}
```

**说明**:
- ⚠️ 仅向后兼容
- ⚠️ 新工具推荐使用新格式

---

## API 使用示例

### 检查是否有图片

```python
from task_queue.utils import multimodal

result = {"content": [{"type": "image", "data": "..."}]}

if multimodal.has_images(result):
    print("包含图片")
```

### 提取文本和图片

```python
text, images = multimodal.extract_from_result(result)

print(f"文本: {text}")
print(f"图片数: {len(images)}")

for img in images:
    print(f"  - {img['mime_type']}, {len(img['data'])} bytes")
```

### 清理图片数据（用于 context）

```python
text_only = multimodal.result_to_text_only(result)
# 图片被替换为占位符，可以安全存储到 context
```

### 转换为 LLM 格式

```python
# OpenAI 格式
openai_content = multimodal.to_openai_content(images, "Screenshot:")
# [{"type": "image_url", "image_url": {"url": "data:..."}}, {"type": "text", "text": "Screenshot:"}]

# Anthropic 格式
anthropic_content = multimodal.to_anthropic_content(images, "Screenshot:")
# [{"type": "image", "source": {...}}, {"type": "text", "text": "Screenshot:"}]
```

### Context 处理（自动提取图片）

```python
from task_queue.utils.context import process_multimodal_messages

messages = [
    {"role": "tool", "tool_call_id": "call_1", 
     "content": json.dumps(tool_result)}
]

processed = process_multimodal_messages(messages, provider="openai")
# 自动提取图片为单独的 user message
```

---

## 优先级说明

### `has_images()` 检查顺序

1. **`_mcp_content`** - MCP 客户端转换格式
2. **`content`** - MCP 标准格式（新格式）✨
3. **传统字段** - screenshot, image_base64 等

### `extract_from_result()` 提取顺序

1. **`_mcp_content`** - 如果存在，直接返回
2. **`content`** - MCP 标准格式（新格式）✨
3. **传统字段** - 兜底处理

---

## Content 数组支持的类型

### text

```python
{"type": "text", "text": "文本内容"}
```

### image

```python
{"type": "image", "data": "base64...", "mimeType": "image/png"}
```

**MIME 类型**:
- `image/png`
- `image/jpeg`
- `image/gif`
- `image/webp`

### resource（嵌入式）

```python
{
    "type": "resource",
    "resource": {
        "blob": "base64...",
        "mimeType": "image/png"
    }
}
```

---

## 常见字段名（传统格式）

```python
IMAGE_FIELD_NAMES = [
    "screenshot",      # ✅ 最常用
    "image_base64",
    "image_data",
    "base64_image",
    "image",
    "png_data",
    "jpeg_data",
]
```

---

## 数据验证

### Base64 验证

图片数据会通过 `_is_likely_base64_image()` 验证：

```python
# 检查项：
- 类型：必须是字符串
- 长度：至少 100 字符
- 字符集：只包含 A-Z, a-z, 0-9, +, /, =
```

**示例**:
```python
# ✅ 有效
"iVBORw0KGgoAAAANSUhEUgAAA..."  # PNG
"/9j/4AAQSkZJRgABAQAA..."      # JPEG

# ❌ 无效
"abc"           # 太短
"image_123"     # 包含非法字符（下划线）
""              # 空字符串
123             # 非字符串
```

---

## 测试

### 运行测试

```bash
cd /path/to/novaic
python test_multimodal_new_format.py
```

### 测试覆盖

- ✅ 新格式（文本、单图、多图）
- ✅ 旧格式（兼容性）
- ✅ 提取逻辑
- ✅ 清理逻辑
- ✅ 端到端流程
- ✅ 边界情况
- ✅ MIME 类型变体

---

## 故障排查

### 问题：图片没有被提取

**检查**:
1. `has_images(result)` 是否返回 `True`？
2. 数据是否是有效的 base64？
3. 数据长度是否 ≥ 100？
4. 格式是否正确？

**调试**:
```python
# 检查检测
print(f"has_images: {multimodal.has_images(result)}")

# 检查提取
text, images = multimodal.extract_from_result(result)
print(f"Text: {text}")
print(f"Images: {len(images)}")

# 检查数据
if result.get("content"):
    for item in result["content"]:
        if item.get("type") == "image":
            data = item.get("data", "")
            print(f"Image data length: {len(data)}")
            print(f"Is base64: {multimodal._is_likely_base64_image(data)}")
```

### 问题：LLM 收到的消息格式错误

**检查**:
```python
# 查看处理后的消息
processed = process_multimodal_messages(messages, provider="openai")
print(json.dumps(processed, indent=2))

# 检查 provider 是否正确
# OpenAI: image_url
# Anthropic: image with source
```

### 问题：图片数据太长导致 token 超限

**确认**:
- `result_to_text_only()` 是否被调用？
- 图片是否被替换为占位符？
- Context 中是否还包含完整的 base64 数据？

**修复**:
```python
# 清理 tool result
text_only = multimodal.result_to_text_only(result)

# 检查
cleaned = json.loads(text_only)
assert cleaned["content"][1]["_placeholder"] == True
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `task_queue/utils/multimodal.py` | 核心逻辑 |
| `task_queue/utils/context.py` | Context 处理 |
| `task_queue/utils/result.py` | 结果摘要 |
| `gateway/core/llm_client.py` | LLM 格式转换 |
| `test_multimodal_new_format.py` | 测试套件 |
| `MULTIMODAL_COMPATIBILITY_REPORT.md` | 详细分析 |
| `MULTIMODAL_FIX_SUMMARY.md` | 修复总结 |

---

## 版本历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-02-07 | 1.1 | 修复 `has_images()` 支持新格式 |
| 2026-02-07 | 1.0 | 初始版本（支持 `_mcp_content` 和传统字段） |

---

**快速参考文档结束**
