# 多模态字段迁移指南

## 概述

本指南帮助开发者将现有工具和代码迁移到 MCP 标准多模态格式。

## 目标读者

- 工具开发者
- API 开发者
- 系统集成人员

## 前置要求

- 熟悉 Python 或 JavaScript/TypeScript
- 了解 Base64 编码
- 阅读过 `MULTIMODAL_STANDARD.md`

## 迁移路径

### 选项 1: 仅使用 MCP 标准格式（推荐）

**适用于**: 新工具、重构的工具

**优点**:
- 代码简洁
- 完全符合标准
- 易于维护

**缺点**:
- 需要确保所有客户端支持新格式

### 选项 2: 双格式支持（过渡期推荐）

**适用于**: 现有工具、需要向后兼容的场景

**优点**:
- 平滑迁移
- 兼容旧客户端
- 风险低

**缺点**:
- 代码稍冗余
- 维护成本略高

### 选项 3: 保持旧格式（不推荐）

**适用于**: 即将废弃的工具

**说明**: 系统会自动转换，但不推荐新工具使用。

## 迁移步骤

### Step 1: 评估当前实现

检查你的工具当前使用的格式：

```bash
# 搜索返回格式
rg "image_data|screenshot|base64_image" --type py
```

记录所有返回多模态数据的位置。

### Step 2: 更新返回格式

#### 场景 A: 截图工具

**迁移前**:
```python
def screenshot():
    screenshot_bytes = capture_screenshot()
    return {
        "status": "success",
        "image_data": base64.b64encode(screenshot_bytes).decode('utf-8'),
        "format": "png"
    }
```

**迁移后**:
```python
def screenshot():
    screenshot_bytes = capture_screenshot()
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    
    return {
        "status": "success",
        "content": [
            {
                "type": "text",
                "text": "Screenshot captured successfully"
            },
            {
                "type": "image",
                "data": screenshot_base64,
                "mimeType": "image/png"
            }
        ]
    }
```

**双格式版本**（过渡期）:
```python
def screenshot():
    screenshot_bytes = capture_screenshot()
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    
    return {
        "status": "success",
        # MCP 标准格式
        "content": [
            {
                "type": "text",
                "text": "Screenshot captured successfully"
            },
            {
                "type": "image",
                "data": screenshot_base64,
                "mimeType": "image/png"
            }
        ],
        # 向后兼容字段
        "image_data": screenshot_base64,
        "format": "png"
    }
```

#### 场景 B: 多张图片

**迁移前**:
```python
def capture_grid():
    images = [capture_region(i) for i in range(4)]
    return {
        "images": [
            base64.b64encode(img).decode('utf-8') 
            for img in images
        ]
    }
```

**迁移后**:
```python
def capture_grid():
    images = [capture_region(i) for i in range(4)]
    
    content = [
        {
            "type": "text",
            "text": f"Captured {len(images)} grid images"
        }
    ]
    
    for i, img in enumerate(images):
        content.append({
            "type": "image",
            "data": base64.b64encode(img).decode('utf-8'),
            "mimeType": "image/png",
            "metadata": {
                "grid_position": i
            }
        })
    
    return {
        "status": "success",
        "content": content
    }
```

#### 场景 C: 混合内容（文本 + 图片）

**迁移前**:
```python
def analyze_page():
    screenshot = capture()
    analysis = perform_analysis()
    
    return {
        "analysis": analysis,
        "screenshot": base64.b64encode(screenshot).decode('utf-8')
    }
```

**迁移后**:
```python
def analyze_page():
    screenshot = capture()
    analysis = perform_analysis()
    
    return {
        "status": "success",
        "content": [
            {
                "type": "text",
                "text": f"Analysis: {analysis}"
            },
            {
                "type": "image",
                "data": base64.b64encode(screenshot).decode('utf-8'),
                "mimeType": "image/png"
            }
        ]
    }
```

#### 场景 D: 错误处理

**迁移前**:
```python
def screenshot():
    try:
        img = capture()
        return {"image_data": base64.b64encode(img).decode('utf-8')}
    except Exception as e:
        return {"error": str(e)}
```

**迁移后**:
```python
def screenshot():
    try:
        img = capture()
        return {
            "status": "success",
            "content": [
                {
                    "type": "image",
                    "data": base64.b64encode(img).decode('utf-8'),
                    "mimeType": "image/png"
                }
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "content": [
                {
                    "type": "text",
                    "text": f"Screenshot failed: {str(e)}"
                }
            ]
        }
```

### Step 3: 更新测试

#### 单元测试

**迁移前**:
```python
def test_screenshot():
    result = screenshot()
    assert "image_data" in result
    assert len(result["image_data"]) > 0
```

**迁移后**:
```python
def test_screenshot():
    result = screenshot()
    assert result["status"] == "success"
    assert "content" in result
    
    # 查找图像内容
    images = [c for c in result["content"] if c["type"] == "image"]
    assert len(images) == 1
    assert images[0]["mimeType"] == "image/png"
    assert len(images[0]["data"]) > 0
```

#### 集成测试

```python
async def test_screenshot_e2e():
    # 调用工具
    result = await call_tool("screenshot", {})
    
    # 验证返回格式
    assert result["status"] == "success"
    assert "content" in result
    
    # 解析多模态内容
    from task_queue.utils.multimodal import extract_from_result
    text, images = extract_from_result(result)
    
    # 验证解析结果
    assert len(images) > 0
    assert images[0]["mime_type"] == "image/png"
    
    # 验证可以转换为 LLM API 格式
    from task_queue.utils.anthropic import to_anthropic_content
    content = to_anthropic_content(images[0])
    assert content["type"] == "image"
```

### Step 4: 更新文档

更新工具的返回格式说明：

**迁移前**:
```markdown
## Returns

- `image_data` (str): Base64 encoded screenshot
- `format` (str): Image format (png/jpeg)
```

**迁移后**:
```markdown
## Returns

Returns a result with MCP-compliant content array:

```json
{
    "status": "success",
    "content": [
        {
            "type": "text",
            "text": "Screenshot captured successfully"
        },
        {
            "type": "image",
            "data": "base64_encoded_data",
            "mimeType": "image/png"
        }
    ]
}
```

See `MULTIMODAL_STANDARD.md` for details.
```

### Step 5: 部署和验证

1. **本地测试**:
   ```bash
   pytest tests/test_your_tool.py -v
   ```

2. **集成测试**:
   ```bash
   pytest tests/integration/test_multimodal.py -v
   ```

3. **手动验证**:
   ```bash
   # 调用工具
   python -m novaic.tools.screenshot
   
   # 验证输出格式
   python -m novaic.utils.validate_mcp result.json
   ```

4. **部署到开发环境**:
   ```bash
   git checkout -b feature/mcp-screenshot
   git add .
   git commit -m "Migrate screenshot tool to MCP standard"
   git push origin feature/mcp-screenshot
   ```

5. **监控**:
   - 检查日志中的错误
   - 监控性能指标
   - 收集用户反馈

## 特定场景迁移

### Playwright Helper

`novaic-backend/scripts/playwright_helper.py` 是关键工具，需要优先迁移。

**涉及的命令**:
- `screenshot`
- `browser_screenshot`
- `full_page_screenshot`

**迁移示例**:

```python
# 文件: novaic-backend/scripts/playwright_helper.py

elif command == "screenshot":
    try:
        screenshot_bytes = page.screenshot(full_page=False)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        result = {
            "status": "success",
            "content": [
                {
                    "type": "text",
                    "text": "Screenshot captured"
                },
                {
                    "type": "image",
                    "data": screenshot_base64,
                    "mimeType": "image/png",
                    "metadata": {
                        "viewport": {
                            "width": page.viewport_size["width"],
                            "height": page.viewport_size["height"]
                        },
                        "url": page.url
                    }
                }
            ]
        }
    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "content": [
                {
                    "type": "text",
                    "text": f"Screenshot failed: {str(e)}"
                }
            ]
        }
```

### VMUse Adapter

`novaic-backend/gateway/clients/vmuse_adapter.py` 需要实现新的工具和更新现有工具。

**新增 browser_screenshot**:

```python
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """浏览器截图 - MCP 标准格式"""
    response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
    response.raise_for_status()
    result = response.json()
    
    # 确保返回格式正确
    if "content" in result:
        return {
            "success": True,
            "result": result  # 直接传递 MCP 格式
        }
    else:
        # 向后兼容：转换旧格式
        return {
            "success": True,
            "result": {
                "content": [
                    {
                        "type": "image",
                        "data": result.get("data", result.get("image_data", "")),
                        "mimeType": f"image/{result.get('format', 'png')}"
                    }
                ]
            }
        }
```

**更新工具注册**:

```python
async def call_tool(self, tool_name: str, arguments: Dict[str, Any], vm_id: str) -> Dict[str, Any]:
    # ... 现有代码 ...
    
    elif tool_name == "browser_screenshot":
        return await self._browser_screenshot(vm_id, arguments)
    
    # ... 其他工具 ...
```

### VMControl API

`novaic-backend/gateway/api/vmcontrol.py` 需要更新截图端点。

**迁移前**:
```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    screenshot_bytes = await vmcontrol_client.screenshot(vm_id)
    return Response(content=screenshot_bytes, media_type="image/png")
```

**迁移后**:
```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    screenshot_bytes = await vmcontrol_client.screenshot(vm_id)
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    
    return {
        "status": "success",
        "content": [
            {
                "type": "image",
                "data": screenshot_base64,
                "mimeType": "image/png"
            }
        ]
    }
```

**向后兼容版本**:

```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str, format: str = "json"):
    screenshot_bytes = await vmcontrol_client.screenshot(vm_id)
    
    # 支持两种响应格式
    if format == "binary":
        # 旧格式：返回二进制数据
        return Response(content=screenshot_bytes, media_type="image/png")
    else:
        # 新格式：返回 JSON with MCP content
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        return {
            "status": "success",
            "content": [
                {
                    "type": "image",
                    "data": screenshot_base64,
                    "mimeType": "image/png"
                }
            ]
        }
```

## 常见问题

### Q1: 迁移会破坏现有功能吗？

**A**: 不会。系统已更新 `extract_from_result()` 函数以支持新旧两种格式。只要你的工具返回标准格式，系统会自动处理。

### Q2: 我必须立即迁移吗？

**A**: 不必须，但强烈建议。新工具应使用 MCP 标准格式。现有工具可以逐步迁移。

### Q3: 如何验证迁移是否成功？

**A**: 运行测试套件：

```bash
# 单元测试
pytest tests/test_multimodal_standard.py

# 集成测试
pytest tests/integration/test_your_tool.py

# 端到端测试
pytest tests/e2e/test_multimodal_flow.py
```

### Q4: 迁移后性能会下降吗？

**A**: 不会显著下降。JSON 序列化的开销很小，且 Base64 编码是必需的（无论哪种格式）。

### Q5: 我可以混合使用新旧格式吗？

**A**: 技术上可以，但不推荐。建议统一使用 MCP 标准格式，或在过渡期使用双格式支持。

### Q6: 如果遇到问题怎么办？

**A**: 
1. 检查 `MULTIMODAL_STANDARD.md` 确认格式正确
2. 运行验证工具：`python -m novaic.utils.validate_mcp`
3. 查看日志：`tail -f logs/novaic-backend.log`
4. 联系团队：backend-team@novaic.com

## 迁移检查清单

### 代码修改

- [ ] 更新返回格式使用 `content` 数组
- [ ] 图像使用 `type: "image"` 和 `mimeType`
- [ ] 文本使用 `type: "text"` 和 `text`
- [ ] 添加状态字段 `status: "success"/"error"`
- [ ] 移除旧的字段引用（或保留用于兼容）
- [ ] 更新错误处理

### 测试

- [ ] 更新单元测试
- [ ] 添加集成测试
- [ ] 运行回归测试
- [ ] 验证向后兼容性
- [ ] 端到端测试

### 文档

- [ ] 更新工具文档
- [ ] 更新 API 文档
- [ ] 添加使用示例
- [ ] 更新 README

### 部署

- [ ] 本地测试通过
- [ ] 开发环境测试通过
- [ ] 创建 PR 并 code review
- [ ] 部署到生产环境
- [ ] 监控错误日志

## 支持和资源

### 文档

- `MULTIMODAL_STANDARD.md` - 标准文档
- `IMPLEMENTATION_PLAN.md` - 实施计划
- `API_CHANGES.md` - API 变更
- `TESTING_GUIDE.md` - 测试指南

### 工具

- 验证工具：`python -m novaic.utils.validate_mcp`
- 测试套件：`pytest tests/test_multimodal_standard.py`
- 格式转换：`python -m novaic.utils.convert_legacy_format`

### 联系方式

- **技术支持**: backend-team@novaic.com
- **文档问题**: docs@novaic.com
- **紧急问题**: oncall@novaic.com

## 附录

### A. 完整迁移示例

参见 `examples/migration_example.py`

### B. 测试数据

参见 `tests/fixtures/multimodal_examples.json`

### C. 迁移脚本

参见 `scripts/migrate_to_mcp_format.py`

---

**维护者**: NovaIC Backend Team  
**最后更新**: 2026-02-07  
**状态**: Draft
