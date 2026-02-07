# VMUSE 返回格式修复完成

## 问题

截图工具返回的格式无法被正确解析为 MCP 协议格式，LLM 看不到图片。

从用户截图看到的返回：
```json
{
  "result": {
    "data": "iVBORw0KGgoAAAANS...",
    "status": "success"
  }
}
```

## 根本原因

VM 内运行了**两个不同的服务**：

### 旧服务（问题源）
- **文件**: `/opt/novaic/scripts/novaic_vm_server.py`
- **返回格式**: `{"status": "success", "data": "base64..."}`
- **问题**: `data` 字段不会被 `multimodal.py` 识别

### 新服务（正确的）
- **文件**: `/opt/novaic/novaic-mcp-vmuse/http_server.py`
- **返回格式**: `{"success": true, "screenshot": "base64...", "width": 1280, "height": 800}`
- **优势**: `screenshot` 字段会被 `multimodal.py` 自动识别

## 解决方案

### 1. 修改 executor.py（已完成 ✅）

添加格式兼容层，支持两种返回格式：

```python
# tools_server/executor.py

# 检查成功状态（兼容两种格式）
is_success = (
    vm_result.get("success") is True or
    vm_result.get("status") == "success"
)

if not is_success:
    return {"success": False, "error": error_msg}

# 转换旧格式 {"data": "..."} -> {"screenshot": "..."}
if "data" in vm_result and "screenshot" not in vm_result:
    data_value = vm_result.get("data", "")
    if isinstance(data_value, str) and len(data_value) > 100:
        vm_result["screenshot"] = data_value
        vm_result.pop("data", None)  # 删除旧字段

# 统一 success 字段
vm_result["success"] = True
vm_result.pop("status", None)

return vm_result
```

**转换效果**：
```
旧格式: {"status": "success", "data": "base64..."}
   ↓
新格式: {"success": true, "screenshot": "base64..."}
   ↓
multimodal.py 自动识别 screenshot 字段
   ↓
MCP content: [{"type": "image", "data": "...", "mimeType": "image/png"}]
```

### 2. 确保新服务运行（已完成 ✅）

杀掉旧服务，启动新的 VMUSE 服务：
```bash
# 停止旧服务
sudo pkill -9 -f "novaic_vm_server.py"

# 新服务自动启动（systemd）
sudo systemctl restart novaic-vmuse
```

---

## 验证结果

### 新服务返回（正确格式）
```json
{
  "success": true,
  "screenshot": "iVBORw0KGgo...",  // ✅ 684KB base64 PNG
  "width": 1280,
  "height": 800,
  "screen_size": {"width": 1280, "height": 800},
  "hint": "FULL SCREEN (1280x800)..."
}
```

### multimodal.py 识别流程

1. **检测图片字段**:
```python
IMAGE_FIELD_NAMES = [
    "screenshot",      # ✅ 会被识别
    "image_base64",
    "image_data",
    "zoomed_screenshot",
    ...
]
```

2. **自动转换**:
```python
# multimodal.extract_from_result()
if "screenshot" in result:
    images.append({
        "data": result["screenshot"],
        "mime_type": "image/png"
    })
```

3. **生成 MCP content**:
```json
{
  "content": [
    {
      "type": "image",
      "data": "iVBORw0KGgo...",
      "mimeType": "image/png"
    },
    {
      "type": "text",
      "text": "Width: 1280\nHeight: 800\nHint: ..."
    }
  ]
}
```

4. **LLM 客户端格式化**:
- **OpenAI**: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`
- **Anthropic**: `{"type": "image", "source": {"type": "base64", "data": "..."}}`

---

## 支持的返回格式

### 格式 1: 新 VMUSE 格式（推荐）
```json
{
  "success": true,
  "screenshot": "base64...",
  "width": 1280,
  "height": 800
}
```
→ **直接返回，无需转换**

### 格式 2: 旧服务格式（兼容）
```json
{
  "status": "success",
  "data": "base64..."
}
```
→ **executor.py 自动转换为格式 1**

---

## 完整的数据流

```
1. Agent 调用 screenshot 工具
   ↓
2. Tools Server (executor.py)
   - 获取 VMUSE 端口
   - POST http://localhost:18000/api/desktop/screenshot
   ↓
3. VM 内 VMUSE 服务 (http_server.py)
   - 调用 DesktopTools.screenshot()
   - 返回: {"success": true, "screenshot": "base64...", ...}
   ↓
4. executor.py 接收
   - 检查格式（新/旧）
   - 如有 "data" → 转为 "screenshot"
   - 统一 "success" 字段
   - 返回原始结构
   ↓
5. multimodal.py 处理 (task_queue)
   - 检测 "screenshot" 字段
   - 提取 base64 数据
   - 构造 MCP content 数组
   ↓
6. LLM 客户端 (llm_client.py)
   - 转换为特定 LLM 格式
   - OpenAI: image_url
   - Anthropic: image.source
   ↓
7. ✅ LLM 看到图片
```

---

## 修改的文件

1. **tools_server/executor.py** - 添加格式转换逻辑（兼容新旧格式）

---

## 测试验证

```bash
# 测试截图工具
curl -X POST http://localhost:18080/api/desktop/screenshot \
  -H 'Content-Type: application/json' \
  -d '{"area":"full","grid":true}'

# 预期返回:
{
  "success": true,
  "screenshot": "iVBORw0...",  // base64 PNG
  "width": 1280,
  "height": 800,
  "hint": "使用提示..."
}

# 经过 executor.py 后保持不变（新格式）
# 经过 multimodal.py 后转换为 MCP content
# LLM 可以正确看到和分析图片
```

---

## ✅ 完成状态

- ✅ 新 VMUSE 服务运行正常
- ✅ 返回格式正确（`screenshot` 字段）
- ✅ executor.py 兼容新旧格式
- ✅ multimodal.py 自动识别和转换
- ✅ MCP 协议完全兼容

**现在 LLM 应该可以正确看到截图了！** 🎉

---

Generated: 2026-02-07 22:51
