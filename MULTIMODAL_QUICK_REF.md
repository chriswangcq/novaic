# 多模态截图支持 - 快速参考

## 修改摘要

### ✅ 已完成的修改

**文件**: `novaic-backend/scripts/playwright_helper.py`

1. **第 26 行**: 添加 `import base64`
2. **第 122 行**: `screenshot_bytes.hex()` → `base64.b64encode(screenshot_bytes).decode('utf-8')`

---

## LLM 多模态支持架构

### 核心模块

| 模块 | 功能 | 位置 |
|------|------|------|
| **multimodal.py** | 图片提取和格式转换 | `task_queue/utils/multimodal.py` |
| **context.py** | 消息预处理管道 | `task_queue/utils/context.py` |
| **llm_client.py** | LLM API 调用 | `gateway/core/llm_client.py` |

### 支持的图片字段

```python
IMAGE_FIELD_NAMES = [
    "screenshot",      # ✅ desktop.screenshot
    "image_data",      # ✅ vmuse_adapter
    "image_base64",    # ✅ 通用
    "base64_image",
    "image",
    "png_data",
    "jpeg_data",
]
```

### 数据流

```
playwright_helper.py (base64) 
  → vmuse_adapter.py (image_data)
  → multimodal.extract_from_result()
  → process_multimodal_messages()
  → llm_client._convert_content_to_anthropic()
  → LLM API
```

---

## 使用示例

### 1. 调用截图工具

```python
result = await vmuse_adapter.call_tool(
    tool_name="browser_screenshot",
    arguments={},
    vm_id="1"
)

# 返回格式
{
    "success": True,
    "result": {
        "image_data": "iVBORw0KGgo..."  # base64 PNG
    }
}
```

### 2. 自动多模态处理

```python
from task_queue.utils import process_multimodal_messages

# 原始消息（包含截图）
messages = [
    {"role": "tool", "content": '{"image_data": "iVBORw0..."}'}
]

# 自动处理
processed = process_multimodal_messages(messages, provider="anthropic")

# 结果：图片被提取为独立的 user message
[
    {"role": "tool", "content": '{"image_data": "[IMAGE PROVIDED SEPARATELY]"}'},
    {"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "data": "iVBORw0..."}}
    ]}
]
```

### 3. 支持的 LLM 提供商

- ✅ **OpenAI**: `image_url` 格式
- ✅ **Anthropic**: `image` + `source.base64` 格式
- ✅ **Google Gemini**: `inline_data` 格式
- ✅ **Azure OpenAI**: OpenAI 格式

---

## 关键函数

### multimodal.py

```python
# 提取图片
text, images = multimodal.extract_from_result(result)

# 转换为 OpenAI 格式
content = multimodal.to_openai_content(images, text)

# 转换为 Anthropic 格式
content = multimodal.to_anthropic_content(images, text)

# 检查是否有图片
has_img = multimodal.has_images(result)
```

### context.py

```python
# 处理多模态消息
from task_queue.utils import process_multimodal_messages

processed = process_multimodal_messages(
    messages, 
    provider="openai"  # or "anthropic"
)
```

---

## 测试验证

### 手动测试步骤

1. **启动服务**
```bash
# 启动 vmcontrol
cd novaic-backend
python -m main_vmcontrol

# 启动 gateway
python -m main_gateway
```

2. **调用截图工具**
```python
# 通过 API 调用
POST /api/agents/{agent_id}/tools/call
{
    "tool_name": "browser_screenshot",
    "arguments": {}
}
```

3. **检查返回格式**
```json
{
    "success": true,
    "result": {
        "image_data": "iVBORw0KGgoAAAANS..."  // ✅ base64 格式
    }
}
```

4. **验证 LLM 识别**
- 查看 LLM API 请求日志
- 确认 `messages` 中包含 `image` 或 `image_url` 类型
- 确认 LLM 能够描述图片内容

---

## 故障排查

### 问题 1: 图片未被识别

**症状**: `multimodal.has_images()` 返回 `False`

**检查**:
1. 字段名是否在 `IMAGE_FIELD_NAMES` 中？
2. 数据是否是 base64 格式？（至少 100 字符）
3. 数据是否符合 base64 字符集？

**解决**:
```python
# 添加自定义字段名
IMAGE_FIELD_NAMES.append("my_custom_field")
```

### 问题 2: LLM 报错 "Invalid image format"

**症状**: LLM API 返回 400 错误

**检查**:
1. base64 数据是否完整？
2. MIME 类型是否正确？
3. 是否包含 data URL 前缀？（OpenAI 需要，Anthropic 不需要）

**解决**:
```python
# OpenAI: 需要 data URL 前缀
"url": "data:image/png;base64,iVBORw0..."

# Anthropic: 只需要 base64 数据
"data": "iVBORw0..."
```

### 问题 3: 图片过大

**症状**: 超时或 413 错误

**解决**:
```python
# 在 playwright_helper.py 中调整截图质量
screenshot_bytes = page.screenshot(
    full_page=False,
    quality=50,  # JPEG 质量 (0-100)
    type='jpeg'  # 使用 JPEG 代替 PNG
)
```

---

## 性能优化建议

1. **压缩截图**
   - 使用 JPEG 代替 PNG（更小）
   - 降低质量参数（quality=50-70）
   - 限制截图尺寸

2. **缓存 base64 数据**
   - 避免重复编码
   - 使用 Redis 缓存大图片

3. **异步处理**
   - 使用 `asyncio` 并发处理多张图片
   - 避免阻塞主线程

---

## 相关文档

- [完整报告](./MULTIMODAL_SCREENSHOT_SUPPORT_REPORT.md)
- [LLM Client 文档](./novaic-backend/gateway/core/llm_client.py)
- [Multimodal Utils](./novaic-backend/task_queue/utils/multimodal.py)

---

**最后更新**: 2026-02-07
