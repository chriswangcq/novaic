# VM 截图 Gateway API 返回格式修复

## 问题诊断

**原始问题**:
- vmcontrol 返回 JSON: `{"data": "base64...", "format": "png", ...}`
- Gateway API 错误地转换为二进制 PNG 字节流
- vmuse_adapter 期望 JSON，实际收到字节流 → 解析失败

**根本原因**:
1. `vmcontrol.py` 客户端的 `screenshot()` 返回 `response.content`（字节流）
2. Gateway API 端点直接返回字节流作为 PNG 响应
3. vmuse_adapter 直接连接 vmcontrol（不通过 Gateway），期望 `image_data` 字段但实际返回 `data` 字段

## 修复方案

### 1. 修复 vmcontrol 客户端

**文件**: `novaic-backend/gateway/clients/vmcontrol.py` (第 79-91 行)

**修改前**:
```python
async def screenshot(self, vm_id: str) -> bytes:
    """获取 VM 截图"""
    response = await self.client.post(f"/api/vms/{vm_id}/screenshot")
    response.raise_for_status()
    return response.content  # 返回字节流
```

**修改后**:
```python
async def screenshot(self, vm_id: str) -> Dict[str, Any]:
    """获取 VM 截图（JSON 格式）"""
    response = await self.client.post(f"/api/vms/{vm_id}/screenshot")
    response.raise_for_status()
    return response.json()  # 返回 JSON
```

### 2. 修复 Gateway API 端点

**文件**: `novaic-backend/gateway/api/vmcontrol.py` (第 142-155 行)

**修改前**:
```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    """获取 VM 截图"""
    try:
        client = get_vmcontrol_client()
        image_data = await client.screenshot(vm_id)
        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        logger.error(f"[VmControl Proxy] Screenshot for VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**修改后**:
```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    """获取 VM 截图（MCP 标准格式）"""
    try:
        client = get_vmcontrol_client()
        result = await client.screenshot(vm_id)  # 现在返回 JSON dict
        
        # 转换为 MCP 标准格式
        return {
            "content": [
                {
                    "type": "image",
                    "data": result.get("data", ""),
                    "mimeType": f"image/{result.get('format', 'png')}"
                }
            ]
        }
    except Exception as e:
        logger.error(f"[VmControl Proxy] Screenshot for VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 修复 vmuse_adapter

**文件**: `novaic-backend/gateway/clients/vmuse_adapter.py` (第 539-553 行)

**修改前**:
```python
async def _screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """获取 VM 截图"""
    response = await self.client.post(f"/api/vms/{vm_id}/screenshot")
    response.raise_for_status()
    result = response.json()
    
    return {
        "success": True,
        "result": {
            "image_data": result.get("image_data", ""),  # 期望 image_data 字段
            "format": result.get("format", "png"),
            "width": result.get("width", 0),
            "height": result.get("height", 0)
        }
    }
```

**修改后**:
```python
async def _screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """获取 VM 截图"""
    response = await self.client.post(f"/api/vms/{vm_id}/screenshot")
    response.raise_for_status()
    result = response.json()
    
    # vmcontrol 返回 JSON: {"data": "base64...", "format": "png", "width": 1280, "height": 800}
    # 兼容两种格式：新格式使用 "data"，旧格式使用 "image_data"
    image_data = result.get("data") or result.get("image_data", "")
    
    return {
        "success": True,
        "result": {
            "image_data": image_data,
            "format": result.get("format", "png"),
            "width": result.get("width", 0),
            "height": result.get("height", 0)
        }
    }
```

## 修改总结

| 组件 | 文件 | 修改内容 | 状态 |
|------|------|----------|------|
| vmcontrol 客户端 | `gateway/clients/vmcontrol.py` | `screenshot()` 返回 JSON 而不是 bytes | ✅ 完成 |
| Gateway API | `gateway/api/vmcontrol.py` | 返回 MCP 标准格式 | ✅ 完成 |
| vmuse_adapter | `gateway/clients/vmuse_adapter.py` | 兼容 `data` 和 `image_data` 字段 | ✅ 完成 |

## 数据流

```
vmcontrol (Rust)
  ↓ 返回: {"data": "base64...", "format": "png", "width": 1280, "height": 800}
  ↓
vmuse_adapter (直接连接 vmcontrol:8080)
  ↓ 提取: image_data = result.get("data") or result.get("image_data")
  ↓ 返回: {"success": True, "result": {"image_data": "...", "format": "png", ...}}
  ↓
MCP Client
  ↓ 使用截图数据
```

**Gateway API 路径** (当前未被 vmuse_adapter 使用):
```
vmcontrol (Rust)
  ↓ 返回: {"data": "base64...", "format": "png", ...}
  ↓
Gateway API (/api/vmcontrol/vms/{vm_id}/screenshot)
  ↓ 转换为 MCP 标准格式
  ↓ 返回: {"content": [{"type": "image", "data": "...", "mimeType": "image/png"}]}
  ↓
前端/其他客户端
```

## 验证

### 语法检查
```bash
cd novaic-backend
python3 -m py_compile gateway/clients/vmcontrol.py
python3 -m py_compile gateway/api/vmcontrol.py
python3 -m py_compile gateway/clients/vmuse_adapter.py
```

✅ 所有文件语法检查通过

### 运行时测试

**注意**: 当前 vmcontrol 服务遇到 QMP 连接问题 ("Broken pipe")，需要修复后才能完整测试。

测试脚本: `test_screenshot_fix.sh`

## 待办事项

### 立即
- [x] 修复 vmcontrol 客户端返回格式
- [x] 修复 Gateway API 返回格式
- [x] 修复 vmuse_adapter 字段兼容性
- [x] 语法检查

### 需要 vmcontrol 服务正常运行后
- [ ] 测试 vmuse_adapter 截图功能
- [ ] 测试 Gateway API 返回 MCP 格式
- [ ] 端到端测试

### 可选优化
- [ ] 考虑统一 vmuse_adapter 使用 Gateway API 而不是直接连接 vmcontrol
- [ ] 添加截图缓存机制
- [ ] 添加截图格式转换选项

## 注意事项

1. **vmuse_adapter 直接连接 vmcontrol**: 
   - vmuse_adapter 不通过 Gateway API，而是直接连接 vmcontrol:8080
   - 因此需要修复 vmuse_adapter 以兼容 vmcontrol 的返回格式

2. **Gateway API MCP 格式**:
   - Gateway API 已修改为返回 MCP 标准格式
   - 适用于前端和其他需要 MCP 格式的客户端

3. **向后兼容**:
   - vmuse_adapter 的修改兼容新旧两种字段名（`data` 和 `image_data`）
   - 确保平滑迁移

## 相关文件

- `novaic-backend/gateway/clients/vmcontrol.py`
- `novaic-backend/gateway/api/vmcontrol.py`
- `novaic-backend/gateway/clients/vmuse_adapter.py`
- `test_screenshot_fix.sh` (测试脚本)
- `test_screenshot_fix.py` (Python 测试脚本，需要虚拟环境)
