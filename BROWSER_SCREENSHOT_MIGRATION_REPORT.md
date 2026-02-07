# browser_screenshot 工具统一格式迁移报告

**日期**: 2026-02-07  
**试点工具**: `browser_screenshot`  
**状态**: ✅ 完成

---

## 1. 修改内容

### 1.1 修改的文件

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `novaic-backend/gateway/clients/vmuse_adapter.py` | 核心修改 | 更新截图工具返回格式 |

### 1.2 修改的方法

#### 方法 1: `_browser_screenshot` (第421-450行)

**改动前**：
```python
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
    response.raise_for_status()
    result = response.json()
    
    if "content" in result and isinstance(result["content"], list):
        # MCP 标准格式，直接返回
        return {
            "success": result.get("status") == "success",
            "result": {
                "_mcp_content": result["content"]  # ❌ 嵌套 + 内部格式
            }
        }
    else:
        return {
            "success": result.get("status") == "success",
            "result": result  # ❌ 嵌套结构
        }
```

**改动后**：
```python
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """浏览器截图 - 返回 MCP 标准格式"""
    try:
        response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
        response.raise_for_status()
        result = response.json()
        
        # 检查返回格式
        if "content" in result and isinstance(result["content"], list):
            # vmcontrol 已返回 MCP 标准格式，直接使用
            return {
                "success": result.get("status") == "success",
                "content": result["content"]  # ✅ 直接返回 content 数组
            }
        else:
            # 转换传统格式为标准格式
            image_data = result.get("data") or result.get("image_data", "")
            
            if not image_data:
                return {
                    "success": False,
                    "error": "No image data returned from vmcontrol",
                    "content": []
                }
            
            # 可选：压缩图像（如果过大）
            image_data, metadata = await self._compress_image_if_needed(image_data)
            
            # 构建标准格式
            content = [
                {
                    "type": "text",
                    "text": f"Browser screenshot captured successfully. {metadata.get('compression_info', '')}"
                },
                {
                    "type": "image",
                    "data": image_data,  # ✅ 图像永不截断
                    "mimeType": f"image/{result.get('format', 'png')}",
                    "metadata": {
                        "width": result.get("width"),
                        "height": result.get("height"),
                        **metadata
                    }
                }
            ]
            
            return {
                "success": True,
                "content": content  # ✅ 标准格式
            }
    
    except Exception as e:
        logger.error(f"[VmuseAdapter] Browser screenshot failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": []  # ✅ 错误时也包含 content
        }
```

#### 方法 2: `_screenshot` (第543-562行)

同样更新为标准格式，逻辑与 `_browser_screenshot` 相同。

#### 新增方法 3: `_compress_image_if_needed`

**功能**：图像压缩（可选）

```python
async def _compress_image_if_needed(
    self,
    image_data: str,
    max_size_kb: int = 500
) -> tuple[str, dict]:
    """
    压缩图像到指定大小
    
    Args:
        image_data: Base64 编码的图像数据
        max_size_kb: 最大大小（KB），默认 500KB
    
    Returns:
        (compressed_data, metadata) - 压缩后的数据和元数据
    """
    # 1. 检查原始大小
    original_size = len(image_data.encode('utf-8'))
    
    # 2. 小于阈值，直接返回
    if original_size <= max_size_kb * 1024:
        return image_data, {"compressed": False, ...}
    
    # 3. 使用 PIL 压缩
    try:
        from PIL import Image
        from io import BytesIO
        
        # 解码 → 降分辨率 → 压缩质量 → 编码
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        
        # 降分辨率（最大 1920px）
        if max(img.size) > 1920:
            ratio = 1920 / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.LANCZOS)
        
        # 压缩保存
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        compressed_data = base64.b64encode(output.getvalue()).decode('utf-8')
        
        return compressed_data, {
            "compressed": True,
            "original_size": original_size,
            "compressed_size": len(compressed_data),
            ...
        }
    
    except ImportError:
        # PIL 不可用，跳过压缩
        return image_data, {"compressed": False, ...}
```

#### 新增方法 4: `_extract_image_from_content`

**功能**：从标准格式中提取图像数据（用于兼容性）

```python
def _extract_image_from_content(self, result: Dict[str, Any]) -> str:
    """从 content 数组中提取图像 data 字段"""
    content = result.get("content", [])
    for item in content:
        if item.get("type") == "image":
            return item.get("data", "")
    return ""
```

### 1.3 代码差异汇总

| 改动项 | 改动前 | 改动后 |
|--------|--------|--------|
| 返回结构 | `{success, result: {...}}` | `{success, content: [...]}` |
| 图像字段 | `result.image_data` 或 `result._mcp_content` | `content[1].data` |
| MIME 类型 | 无或 `result.format` | `content[1].mimeType` |
| 元数据 | 分散在 `result` 中 | 集中在 `content[1].metadata` |
| 图像压缩 | ❌ 无 | ✅ 可选压缩（>500KB） |
| 错误处理 | `{success: False, error: "..."}` | `{success: False, error: "...", content: []}` |

---

## 2. 格式验证

### 2.1 符合标准的要求

✅ **必需字段**：
- `success`: boolean
- `content`: array

✅ **content 数组元素**：
- 文本元素：`{"type": "text", "text": "..."}`
- 图像元素：`{"type": "image", "data": "...", "mimeType": "..."}`

✅ **图像完整性**：
- 图像数据永不被截断
- Base64 编码，无 data URI 前缀

✅ **可选字段**：
- `error`: string（失败时）
- `metadata`: object（图像元数据）

### 2.2 格式示例

**成功返回**：
```json
{
  "success": true,
  "content": [
    {
      "type": "text",
      "text": "Browser screenshot captured successfully. (compressed from 800KB to 450KB)"
    },
    {
      "type": "image",
      "data": "iVBORw0KGgoAAAANSUhEUg...",
      "mimeType": "image/png",
      "metadata": {
        "width": 1920,
        "height": 1080,
        "compressed": true,
        "original_size": 819200,
        "compressed_size": 460800,
        "compression_ratio": "56.3%"
      }
    }
  ]
}
```

**失败返回**：
```json
{
  "success": false,
  "error": "No image data returned from vmcontrol",
  "content": []
}
```

---

## 3. 测试结果

### 3.1 测试方法

创建了测试脚本 `test_browser_screenshot_format.py`，验证：

1. ✅ 返回格式符合 MCP 标准
2. ✅ `content` 数组包含文本和图像
3. ✅ 图像数据完整（不被截断）
4. ✅ 错误处理正确

### 3.2 测试输出

```
============================================================
测试 browser_screenshot 新统一返回格式
============================================================

【测试 1】成功响应格式
=== 格式验证 ===
✅ 包含 'success' 字段
✅ 包含 'content' 字段
✅ 'content' 是数组，包含 2 个元素
  - 元素 0: type=text
    ✅ 文本内容: Browser screenshot captured successfully...
  - 元素 1: type=image
    ✅ 图像数据长度: 125 字符
    ✅ MIME 类型: image/png
    ✅ 元数据: {...}

✅ 格式验证通过

【测试 2】错误响应格式
=== 错误格式验证 ===
✅ success = false
✅ error: No image data returned from vmcontrol
✅ content: []

✅ 错误格式验证通过

【测试 3】图像完整性
✅ 图像数据完整（未被截断）

============================================================
✅ 所有测试通过
============================================================
```

### 3.3 测试结论

✅ **所有测试通过**

- 格式完全符合 MCP 标准
- 图像数据完整保留
- 错误处理符合规范

---

## 4. 后续建议

### 4.1 其他需要修改的工具

根据协议文档和代码分析，以下工具也需要类似的迁移：

#### 优先级 P0（立即执行）

| 工具 | 文件 | 原因 |
|------|------|------|
| `screenshot` | `vmuse_adapter.py` | ✅ 已完成（与 browser_screenshot 一起更新） |
| 所有文件操作工具 | `vmuse_adapter.py` | 返回 `{success, result}` 嵌套结构 |
| 所有浏览器操作工具 | `vmuse_adapter.py` | 返回 `{success, result}` 嵌套结构 |

#### 优先级 P1（短期内执行）

| 工具 | 文件 | 原因 |
|------|------|------|
| MCP 客户端工具 | `mcp_client/mcp_client.py` | 使用 `_mcp_content` 内部格式 |
| 内部 API | `gateway/api/internal/` | 返回嵌套结构 |
| Tools Server | `tools_server/executor.py` | 需要添加自动截断机制 |

### 4.2 可能的问题和风险

#### 风险 1：向后兼容性

**问题**：现有调用方可能依赖 `result.image_data` 或 `result._mcp_content` 格式

**缓解措施**：
1. ✅ 保留 `_extract_image_from_content` 方法处理兼容性
2. 建议：添加过渡期警告日志
3. 监控：统计使用旧格式的调用

**代码示例**：
```python
# 在 multimodal.py 中添加兼容层
def extract_from_result(result: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    # 优先使用新格式
    if "content" in result and isinstance(result["content"], list):
        return extract_from_content_array(result["content"])
    
    # 兼容旧格式（添加警告）
    logger.warning("⚠️ Tool returned legacy format, please migrate to unified protocol")
    
    if "_mcp_content" in result.get("result", {}):
        return extract_from_content_array(result["result"]["_mcp_content"])
    
    # 传统格式
    return extract_legacy_format(result)
```

#### 风险 2：图像压缩可能影响质量

**问题**：压缩可能导致图像细节丢失

**缓解措施**：
1. ✅ 阈值设置为 500KB（较宽松）
2. ✅ 保留原始尺寸信息在 metadata 中
3. ✅ PIL 不可用时自动跳过压缩
4. 建议：添加配置项控制压缩行为

**配置建议**（`common/config.py`）：
```python
# ===== 图像处理配置 =====
IMAGE_COMPRESS_ENABLED = bool(os.getenv("IMAGE_COMPRESS_ENABLED", "true").lower() == "true")
IMAGE_MAX_SIZE_KB = int(os.getenv("IMAGE_MAX_SIZE_KB", "500"))  # 500KB
IMAGE_MAX_DIMENSION = int(os.getenv("IMAGE_MAX_DIMENSION", "1920"))  # 1920px
IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", "85"))  # 85%
```

#### 风险 3：下游组件需要同步更新

**问题**：`multimodal.py` 和其他消费者需要更新

**缓解措施**：
1. 保留兼容性提取逻辑（见风险 1）
2. 逐步迁移：先工具层，再消费层
3. 充分测试端到端流程

**测试清单**：
- [ ] Gateway → Tools Server → LLM 完整流程
- [ ] 前端显示图像
- [ ] LLM 能正确处理图像
- [ ] 错误情况正确传播

### 4.3 部署建议

#### 步骤 1：灰度发布

1. **第一阶段**（当前）：
   - ✅ 修改 `browser_screenshot` 和 `screenshot`
   - ✅ 保留向后兼容性
   - 监控日志，确认无问题

2. **第二阶段**：
   - 更新其他 VM 工具（文件、浏览器等）
   - 更新 `multimodal.py` 优先使用新格式
   - 继续监控

3. **第三阶段**：
   - 更新 MCP 客户端和内部 API
   - 添加自动截断机制
   - 端到端测试

4. **第四阶段**（3-6个月后）：
   - 移除旧格式支持
   - 清理兼容代码

#### 步骤 2：监控指标

| 指标 | 目标 | 监控方式 |
|------|------|---------|
| 格式错误率 | < 0.1% | 错误日志统计 |
| 图像压缩率 | 40-60% | metadata 统计 |
| 旧格式使用率 | 逐步降为 0 | 警告日志统计 |
| 性能影响 | < 10% | 响应时间监控 |

#### 步骤 3：回滚计划

如果出现问题：
1. 保留原始代码版本（git revert）
2. 使用特性开关控制新格式
3. 监控和调试

```python
# 特性开关示例
USE_UNIFIED_FORMAT = os.getenv("USE_UNIFIED_FORMAT", "true").lower() == "true"

if USE_UNIFIED_FORMAT:
    return new_format_response()
else:
    return legacy_format_response()
```

---

## 5. 总结

### 5.1 完成的工作

✅ **核心实现**：
- 修改 `browser_screenshot` 返回 MCP 标准格式
- 修改 `screenshot` 返回 MCP 标准格式
- 实现图像压缩功能（可选）
- 添加格式提取辅助方法

✅ **测试验证**：
- 创建格式验证测试脚本
- 所有测试通过
- 格式完全符合协议要求

✅ **文档**：
- 详细的迁移报告
- 代码示例和说明
- 风险分析和缓解措施

### 5.2 协议优势验证

通过 `browser_screenshot` 试点，验证了统一协议的优势：

1. ✅ **单层结构**：移除嵌套 `{success, result}` 格式
2. ✅ **标准化**：遵循 MCP 标准 `content` 数组
3. ✅ **类型明确**：使用 `mimeType` 指定媒体类型
4. ✅ **图像完整**：图像永不被截断
5. ✅ **可扩展**：支持元数据和压缩信息

### 5.3 下一步行动

**立即执行**：
1. 将修改合并到主分支
2. 部署到测试环境
3. 监控日志和性能

**短期（1-2周）**：
1. 更新其他 VM 工具
2. 更新 `multimodal.py` 提取逻辑
3. 添加配置项

**中期（2-4周）**：
1. 更新 MCP 客户端
2. 实现自动截断机制
3. 端到端测试

**长期（3-6个月）**：
1. 监控使用情况
2. 逐步废弃旧格式
3. 清理兼容代码

---

**报告创建时间**: 2026-02-07  
**作者**: AI Assistant  
**状态**: ✅ 试点完成，建议推广
