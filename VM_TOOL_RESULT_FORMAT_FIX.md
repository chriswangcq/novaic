# VM 工具返回格式修复

## 问题

executor.py 把 VMUSE 的返回结果（包含 `screenshot` 字段）整个 JSON.dumps 成 text：

```python
# 错误做法
return {
    "success": True,
    "content": [{"type": "text", "text": json.dumps(vm_result)}]  # ❌ 图片数据被序列化了
}
```

这导致：
1. **图片无法被识别**：`multimodal.py` 无法检测到 screenshot 字段
2. **LLM 看不到图片**：只能看到一个巨大的 JSON 字符串
3. **浪费 tokens**：base64 图片数据占用大量 tokens

## 解决方案

### 修改后的 executor.py

```python
# ✅ 正确做法：直接返回原始结果
if vm_result.get("success") is not False:
    return vm_result  # {"success": true, "screenshot": "base64...", "width": 1280, ...}
```

### 为什么这样可行？

系统的 `task_queue/utils/multimodal.py` 已经有完整的图片检测和转换逻辑：

1. **检测图片字段**:
```python
IMAGE_FIELD_NAMES = [
    "screenshot",      # ✅ VMUSE 截图
    "image_base64",
    "image_data",
    "zoomed_screenshot",  # ✅ VMUSE aim 操作
    ...
]
```

2. **自动转换为 MCP content**:
```python
# multimodal.py 会自动转换为：
{
    "content": [
        {"type": "image", "data": "base64...", "mimeType": "image/png"},
        {"type": "text", "text": "Width: 1280\nHeight: 800\n..."}
    ]
}
```

3. **LLM 客户端处理**:
   - OpenAI: 转换为 `image_url` 格式
   - Anthropic: 转换为 `image` 格式
   - Gemini: 转换为 `inline_data` 格式

## MCP 协议兼容性

### MCP 标准工具结果格式

```typescript
interface CallToolResult {
  content: [
    { type: "text", text: string } |
    { type: "image", data: string, mimeType: string } |
    { type: "resource", resource: {...} }
  ];
  isError?: boolean;
}
```

### 我们的实现

**Level 1**: 工具原始返回（executor.py）
```json
{
  "success": true,
  "screenshot": "iVBORw0...",
  "width": 1280,
  "height": 800,
  "hint": "使用提示..."
}
```

**Level 2**: 多模态转换（multimodal.py）
```json
{
  "content": [
    {"type": "image", "data": "iVBORw0...", "mimeType": "image/png"},
    {"type": "text", "text": "Width: 1280\nHeight: 800\nHint: 使用提示..."}
  ]
}
```

**Level 3**: LLM 格式转换（llm_client.py）
- OpenAI: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`
- Anthropic: `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}`

## 测试验证

```bash
# 1. 调用截图工具
curl -X POST http://localhost:18080/api/desktop/screenshot \
  -H 'Content-Type: application/json' \
  -d '{"area":"full","grid":true}'

# 返回格式（原始）:
{
  "success": true,
  "screenshot": "iVBORw0KGgoAAAA...",  # base64
  "width": 1280,
  "height": 800,
  "grid": true,
  "hint": "FULL SCREEN (1280x800)..."
}

# 2. multimodal.py 会自动检测并转换
# 3. LLM 客户端会看到正确的多模态格式
```

## 支持的工具

所有返回图片的 VM 工具都会受益：

### Desktop Tools
- `screenshot` → `screenshot` 字段
- `mouse` (aim) → `zoomed_screenshot` 字段

### Browser Tools
- `browser_screenshot` → `screenshot` 字段
- `browser_content` → 可能包含 `screenshot`

## 总结

✅ **修改点**: 仅修改 `tools_server/executor.py` 一个文件
✅ **兼容性**: 完全符合 MCP 协议
✅ **向后兼容**: 利用现有 multimodal.py 逻辑
✅ **效果**: LLM 可以正确看到和分析图片

---

Generated: 2026-02-07
