# 多模态字段标准化改造实施计划

## 执行摘要

本文档定义了将 NovaIC 系统迁移到 MCP (Model Context Protocol) 标准多模态格式的详细实施计划。

**目标**: 在保持向后兼容的前提下，将系统多模态数据处理完全迁移到 MCP 标准。

**时间线**: 8-13 天（约 2 周）

**风险等级**: 低（采用渐进式迁移和向后兼容设计）

## 目录

- [改造原则](#改造原则)
- [分阶段实施计划](#分阶段实施计划)
- [详细代码修改计划](#详细代码修改计划)
- [测试计划](#测试计划)
- [回滚方案](#回滚方案)
- [风险评估](#风险评估)
- [时间表](#时间表)
- [成功标准](#成功标准)

## 改造原则

### 1. 标准优先 (Standard First)

优先使用 MCP 标准格式，确保与行业标准兼容。

**具体措施**:
- 所有新工具必须使用 MCP `content` 数组格式
- API 响应优先返回标准格式
- 文档中推荐标准格式

### 2. 向后兼容 (Backward Compatible)

保持对现有格式的支持，不破坏现有功能。

**具体措施**:
- 解析器支持新旧两种格式
- 可选择性保留旧字段
- 现有测试保持通过

### 3. 渐进迁移 (Progressive Migration)

分阶段实施，降低风险。

**具体措施**:
- 先升级基础设施（解析器）
- 再迁移关键工具
- 最后优化和推广

### 4. 测试驱动 (Test-Driven)

每个阶段都有完整的测试。

**具体措施**:
- 每个 Phase 都有明确的验证标准
- 单元测试覆盖率 > 90%
- 集成测试覆盖关键路径
- 回归测试确保无破坏

### 5. 文档完善 (Well-Documented)

提供清晰的迁移指南。

**具体措施**:
- 标准文档（`MULTIMODAL_STANDARD.md`）
- 迁移指南（`MIGRATION_GUIDE.md`）
- API 变更说明（`API_CHANGES.md`）
- 测试指南（`TESTING_GUIDE.md`）

## 分阶段实施计划

### Phase 0: 准备阶段（1-2天）

**目标**: 建立迁移基础，确保有清晰的标准和测试基准。

#### 任务清单

1. **创建标准文档**
   - [ ] 编写 `MULTIMODAL_STANDARD.md`
   - [ ] 定义 MCP content 数组规范
   - [ ] 定义字段优先级
   - [ ] 定义 MIME 类型列表

2. **备份当前代码**
   - [ ] 创建 git 分支: `git checkout -b feature/mcp-standard`
   - [ ] 标记当前版本: `git tag -a v1.0-pre-mcp -m "Before MCP migration"`

3. **建立测试基准**
   - [ ] 运行现有测试套件：`pytest tests/ -v`
   - [ ] 记录测试覆盖率：`pytest --cov=novaic-backend`
   - [ ] 记录性能基准：运行 `scripts/benchmark.py`
   - [ ] 保存结果到 `reports/baseline_before_mcp.json`

4. **确定影响范围**
   - [ ] 扫描所有返回多模态数据的工具
   - [ ] 识别需要迁移的 API 端点
   - [ ] 评估客户端兼容性
   - [ ] 创建影响范围文档

#### 产出

- [x] `MULTIMODAL_STANDARD.md`
- [ ] `reports/baseline_before_mcp.json`
- [ ] `reports/impact_analysis.md`
- [ ] Git 分支和标签

#### 验证标准

- [ ] 所有文档创建完成
- [ ] 测试基准已建立
- [ ] 影响范围已识别
- [ ] 团队已审阅标准文档

---

### Phase 1: 基础设施升级（2-3天）

**目标**: 使系统能够识别和处理 MCP 标准格式，同时保持向后兼容。

#### 1.1 更新 multimodal.py

**文件**: `novaic-backend/task_queue/utils/multimodal.py`

##### 修改清单

1. **添加 MCP 常量**
   ```python
   # MCP 标准 content 类型
   MCP_CONTENT_TYPES = {
       "text": "text",
       "image": "image",
       "audio": "audio",
       "video": "video",
       "resource": "resource",
       "resource_link": "resource_link"
   }
   ```

2. **更新 IMAGE_FIELD_NAMES**
   ```python
   IMAGE_FIELD_NAMES = [
       # 标准字段（优先）
       "image_data",      # ✅ 推荐
       "image_base64",    # ✅ 推荐
       
       # 通用字段
       "image",
       "screenshot",
       
       # 特定格式
       "png_data",
       "jpeg_data",
       
       # 向后兼容
       "data",            # ✅ 添加（支持 playwright_helper）
       "base64_image",
   ]
   ```

3. **添加 `_parse_content_array()` 函数**
   
   实现 MCP content 数组的解析逻辑：
   - 支持 `{"type": "text", "text": "..."}`
   - 支持 `{"type": "image", "data": "...", "mimeType": "..."}`
   - 支持 `{"type": "resource", "resource": {...}}`
   
   参见 `MULTIMODAL_STANDARD.md` 中的完整实现。

4. **更新 `extract_from_result()` 函数**
   
   添加 MCP 格式检测优先级：
   1. `_mcp_content` (最高优先级)
   2. `content` 数组 (MCP 标准)
   3. 传统字段 (向后兼容)

##### 测试计划

- [ ] 创建 `tests/test_multimodal_standard.py`
- [ ] 测试 MCP content 数组解析
- [ ] 测试传统字段向后兼容
- [ ] 测试优先级顺序
- [ ] 测试错误处理
- [ ] 测试边界情况

##### 验证标准

- [ ] 所有新增测试通过
- [ ] 现有测试保持通过
- [ ] 代码覆盖率 > 90%
- [ ] 无性能退化

#### 1.2 验证 context.py 兼容性

**文件**: `novaic-backend/task_queue/utils/context.py`

##### 验证清单

- [ ] `process_multimodal_messages()` 能处理新格式
- [ ] 添加日志记录新格式的处理
- [ ] 更新相关测试

##### 产出

- [ ] 更新后的 `multimodal.py`
- [ ] 更新后的 `context.py`
- [ ] 新增测试文件 `tests/test_multimodal_standard.py`
- [ ] Phase 1 测试报告

---

### Phase 2: 工具适配（3-5天）

**目标**: 将关键工具迁移到标准格式。

#### 2.1 优先级 P0 工具（必须立即修复）

这些工具是核心功能，必须优先迁移。

##### 2.1.1 playwright_helper.py

**文件**: `novaic-backend/scripts/playwright_helper.py`

**涉及命令**:
- `screenshot`
- `browser_screenshot`
- `full_page_screenshot`

**修改示例**:

```python
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
                    "mimeType": "image/png"
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

**测试计划**:
- [ ] 单元测试：验证返回格式
- [ ] 集成测试：验证与 vmuse_adapter 集成
- [ ] 端到端测试：验证 LLM 能接收图像

##### 2.1.2 vmuse_adapter.py

**文件**: `novaic-backend/gateway/clients/vmuse_adapter.py`

**新增功能**:
- [ ] 实现 `_browser_screenshot()` 方法
- [ ] 在 `call_tool()` 中添加路由

**修改示例**:

```python
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """浏览器截图 - MCP 标准格式"""
    response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
    response.raise_for_status()
    result = response.json()
    
    # 确保返回 MCP 格式
    if "content" in result:
        return {
            "success": True,
            "result": result
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

**更新现有工具**:
- [ ] 更新 `_screenshot()` 方法
- [ ] 更新 `_desktop_screenshot()` 方法

**测试计划**:
- [ ] 单元测试：验证每个方法
- [ ] 集成测试：验证工具调用链
- [ ] Mock 测试：验证错误处理

##### 2.1.3 vmcontrol.py (客户端)

**文件**: `novaic-backend/gateway/clients/vmcontrol.py`

**新增功能**:
- [ ] 添加 `screenshot_json()` 方法（返回 JSON）
- [ ] 保留 `screenshot()` 方法（返回 bytes，用于向后兼容）

**实现**:

```python
async def screenshot_json(self, vm_id: str) -> Dict[str, Any]:
    """获取截图 - 返回 MCP 标准 JSON 格式"""
    screenshot_bytes = await self.screenshot(vm_id)
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

**测试计划**:
- [ ] 单元测试：验证两种方法
- [ ] 集成测试：验证 RPC 调用

##### 2.1.4 vmcontrol.py (API)

**文件**: `novaic-backend/gateway/api/vmcontrol.py`

**修改端点**:
- [ ] 修复 `/api/vmcontrol/vms/{vm_id}/screenshot`

**实现选项**:

**选项 1: 仅返回 JSON**（推荐）
```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    result = await vmcontrol_client.screenshot_json(vm_id)
    return result
```

**选项 2: 支持双格式**（更灵活）
```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str, format: str = "json"):
    if format == "binary":
        screenshot_bytes = await vmcontrol_client.screenshot(vm_id)
        return Response(content=screenshot_bytes, media_type="image/png")
    else:
        return await vmcontrol_client.screenshot_json(vm_id)
```

**测试计划**:
- [ ] API 测试：验证响应格式
- [ ] 集成测试：验证前端调用
- [ ] 性能测试：对比 JSON vs Binary

#### 2.2 优先级 P1 工具（重要但不紧急）

这些工具可以在 P0 完成后逐步迁移。

- [ ] 其他 VM 控制工具（mouse, keyboard）
- [ ] 其他返回二进制数据的工具
- [ ] 音频/视频相关工具（如果有）

#### 产出

- [ ] 更新后的工具代码
- [ ] 新增测试套件
- [ ] Phase 2 测试报告
- [ ] 性能对比报告

#### 验证标准

- [ ] 所有 P0 工具迁移完成
- [ ] 所有测试通过（单元、集成、端到端）
- [ ] LLM 能正确接收和处理图片
- [ ] 无性能退化

---

### Phase 3: 文档和推广（2-3天）

**目标**: 完善文档，推广最佳实践。

#### 3.1 文档清单

1. **MULTIMODAL_STANDARD.md** ✅
   - [x] 标准格式说明
   - [x] 使用示例
   - [x] 最佳实践
   - [x] FAQ

2. **MIGRATION_GUIDE.md** ✅
   - [x] 迁移步骤
   - [x] 代码示例
   - [x] 常见问题
   - [x] 兼容性说明

3. **IMPLEMENTATION_PLAN.md** (本文档) ✅
   - [x] 分阶段计划
   - [x] 详细任务清单
   - [x] 验证标准

4. **API_CHANGES.md**
   - [ ] API 端点变更列表
   - [ ] 请求/响应格式变更
   - [ ] 向后兼容说明
   - [ ] 版本信息

5. **TESTING_GUIDE.md**
   - [ ] 测试策略
   - [ ] 测试用例模板
   - [ ] 测试工具使用
   - [ ] CI/CD 集成

6. **工具文档更新**
   - [ ] 更新所有工具的 docstring
   - [ ] 更新 API 文档（Swagger/OpenAPI）
   - [ ] 更新 README
   - [ ] 添加迁移示例

#### 3.2 推广活动

- [ ] 内部技术分享会
- [ ] 发布迁移公告
- [ ] 创建示例项目
- [ ] 更新开发者文档网站

#### 产出

- [ ] 完整文档集
- [ ] 技术分享 PPT
- [ ] 示例代码仓库

---

### Phase 4: 监控和优化（持续）

**目标**: 监控新标准的使用情况，持续优化。

#### 4.1 监控指标

**使用率指标**:
- [ ] 新格式使用率（content 数组）
- [ ] 旧格式使用率（image_data 等）
- [ ] 工具迁移进度

**性能指标**:
- [ ] API 响应时间
- [ ] JSON 序列化时间
- [ ] Base64 编码时间
- [ ] 内存使用

**错误指标**:
- [ ] 解析失败率
- [ ] 格式验证失败率
- [ ] 工具错误率

#### 4.2 优化任务

- [ ] 识别性能瓶颈
- [ ] 优化关键路径
- [ ] 缓存常用数据
- [ ] 异步处理大文件

#### 4.3 持续改进

- [ ] 收集用户反馈
- [ ] 定期审查指标
- [ ] 更新文档
- [ ] 修复发现的问题

---

## 详细代码修改计划

### 文件: task_queue/utils/multimodal.py

#### 修改 1: 添加 MCP 常量

```python
# 在文件开头添加
MCP_CONTENT_TYPES = {
    "text": "text",
    "image": "image",
    "audio": "audio",
    "video": "video",
    "resource": "resource",
    "resource_link": "resource_link"
}
```

#### 修改 2: 更新 IMAGE_FIELD_NAMES

```python
IMAGE_FIELD_NAMES = [
    # 标准字段（优先）
    "image_data",      # ✅ 推荐
    "image_base64",    # ✅ 推荐
    
    # 通用字段
    "image",
    "screenshot",
    
    # 特定格式
    "png_data",
    "jpeg_data",
    
    # 向后兼容
    "data",            # ✅ 新增
    "base64_image",
]
```

#### 修改 3: 添加 _parse_content_array() 函数

```python
def _parse_content_array(content: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, str]]]:
    """
    解析 MCP 标准 content 数组格式
    
    支持的格式:
    - {"type": "text", "text": "..."}
    - {"type": "image", "data": "base64...", "mimeType": "image/png"}
    - {"type": "resource", "resource": {"blob": "base64...", "mimeType": "..."}}
    
    Args:
        content: MCP content 数组
        
    Returns:
        (text_content, images_list)
        
    Example:
        >>> content = [
        ...     {"type": "text", "text": "Screenshot taken"},
        ...     {"type": "image", "data": "iVBORw...", "mimeType": "image/png"}
        ... ]
        >>> text, images = _parse_content_array(content)
        >>> print(text)
        Screenshot taken
        >>> print(len(images))
        1
    """
    text_parts = []
    images = []
    
    for item in content:
        if not isinstance(item, dict):
            continue
            
        item_type = item.get("type", "")
        
        if item_type == "text":
            text = item.get("text", "")
            if text:
                text_parts.append(text)
        
        elif item_type == "image":
            data = item.get("data", "")
            if data and _is_likely_base64_image(data):
                images.append({
                    "data": data,
                    "mime_type": item.get("mimeType", item.get("mime_type", "image/png"))
                })
        
        elif item_type == "resource":
            # Embedded resource with binary data
            resource = item.get("resource", {})
            mime_type = resource.get("mimeType", resource.get("mime_type", ""))
            blob = resource.get("blob", "")
            
            # 只处理图像类型的资源
            if mime_type.startswith("image/") and blob and _is_likely_base64_image(blob):
                images.append({
                    "data": blob,
                    "mime_type": mime_type
                })
    
    return "\n".join(text_parts), images
```

#### 修改 4: 更新 extract_from_result() 函数

```python
def extract_from_result(result: Dict[str, Any], tool_name: str = "") -> Tuple[str, List[Dict[str, str]]]:
    """
    从工具结果中提取多模态内容
    
    优先级:
    1. _mcp_content (MCP 客户端转换后的标准格式)
    2. content 数组 (MCP 标准格式)
    3. 传统字段 (向后兼容)
    
    Args:
        result: 工具返回的结果字典
        tool_name: 工具名称（用于日志）
        
    Returns:
        (text_content, images_list)
    """
    text_parts = []
    images = []
    
    # 1. 优先检查 _mcp_content
    if "_mcp_content" in result:
        mcp_content = result["_mcp_content"]
        if isinstance(mcp_content, list):
            logger.debug(f"[{tool_name}] Using _mcp_content format")
            return _parse_content_array(mcp_content)
    
    # 2. 检查 content 数组（MCP 标准）
    if "content" in result:
        content = result["content"]
        if isinstance(content, list) and content:
            # 检查是否是 MCP 标准格式（包含 type 字段）
            has_type_field = any(
                isinstance(item, dict) and "type" in item 
                for item in content
            )
            if has_type_field:
                logger.debug(f"[{tool_name}] Using MCP content array format")
                return _parse_content_array(content)
    
    # 3. 向后兼容：检查传统字段
    logger.debug(f"[{tool_name}] Using legacy format")
    
    # ... 现有代码保持不变 ...
    # 检查 IMAGE_FIELD_NAMES 中的字段
    # 提取文本内容
    # 返回结果
```

### 文件: scripts/playwright_helper.py

#### 修改所有截图相关命令

```python
import base64
import json

# ... 现有代码 ...

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
                    "mimeType": "image/png"
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

elif command == "full_page_screenshot":
    try:
        screenshot_bytes = page.screenshot(full_page=True)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        result = {
            "status": "success",
            "content": [
                {
                    "type": "text",
                    "text": "Full page screenshot captured"
                },
                {
                    "type": "image",
                    "data": screenshot_base64,
                    "mimeType": "image/png"
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
                    "text": f"Full page screenshot failed: {str(e)}"
                }
            ]
        }

# 返回结果
print(json.dumps(result))
```

### 文件: gateway/clients/vmuse_adapter.py

#### 修改 1: 实现 browser_screenshot

```python
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    浏览器截图 - 返回 MCP 标准格式
    
    Args:
        vm_id: VM ID
        arguments: 工具参数（当前为空）
        
    Returns:
        {
            "success": bool,
            "result": {
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image", "data": "...", "mimeType": "image/png"}
                ]
            }
        }
    """
    try:
        response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
        response.raise_for_status()
        result = response.json()
        
        # 检查是否已经是 MCP 格式
        if "content" in result:
            return {
                "success": result.get("status") == "success",
                "result": result
            }
        else:
            # 向后兼容：转换旧格式
            return {
                "success": result.get("status") == "success",
                "result": {
                    "status": "success",
                    "content": [
                        {
                            "type": "image",
                            "data": result.get("data", result.get("image_data", "")),
                            "mimeType": f"image/{result.get('format', 'png')}"
                        }
                    ]
                }
            }
    except Exception as e:
        logger.error(f"Browser screenshot failed: {e}")
        return {
            "success": False,
            "result": {
                "status": "error",
                "error": str(e),
                "content": [
                    {
                        "type": "text",
                        "text": f"Browser screenshot failed: {str(e)}"
                    }
                ]
            }
        }
```

#### 修改 2: 更新 call_tool() 路由

```python
async def call_tool(self, tool_name: str, arguments: Dict[str, Any], vm_id: str) -> Dict[str, Any]:
    """调用工具"""
    logger.info(f"Calling tool: {tool_name} on VM {vm_id}")
    
    # ... 现有路由 ...
    
    if tool_name == "browser_screenshot":
        return await self._browser_screenshot(vm_id, arguments)
    
    # ... 其他路由 ...
```

### 文件: gateway/clients/vmcontrol.py

#### 修改: 添加 screenshot_json() 方法

```python
async def screenshot_json(self, vm_id: str) -> Dict[str, Any]:
    """
    获取 VM 截图 - 返回 MCP 标准 JSON 格式
    
    Args:
        vm_id: VM ID
        
    Returns:
        {
            "status": "success",
            "content": [
                {
                    "type": "image",
                    "data": "base64_encoded_data",
                    "mimeType": "image/png"
                }
            ]
        }
    """
    # 调用现有的 screenshot() 方法获取二进制数据
    screenshot_bytes = await self.screenshot(vm_id)
    
    # 转换为 MCP 标准格式
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

### 文件: gateway/api/vmcontrol.py

#### 修改: 更新 screenshot 端点

```python
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(
    vm_id: str,
    format: str = Query("json", description="Response format: 'json' or 'binary'"),
    vmcontrol_client: VMControlClient = Depends(get_vmcontrol_client)
):
    """
    获取 VM 截图
    
    Args:
        vm_id: VM ID
        format: 响应格式
            - "json": 返回 MCP 标准 JSON 格式（推荐）
            - "binary": 返回 PNG 二进制数据（向后兼容）
            
    Returns:
        JSON 格式:
        {
            "status": "success",
            "content": [
                {
                    "type": "image",
                    "data": "base64_encoded_data",
                    "mimeType": "image/png"
                }
            ]
        }
        
        Binary 格式:
        PNG 图像二进制数据
    """
    try:
        if format == "binary":
            # 向后兼容：返回二进制数据
            screenshot_bytes = await vmcontrol_client.screenshot(vm_id)
            return Response(content=screenshot_bytes, media_type="image/png")
        else:
            # 推荐：返回 MCP 标准 JSON 格式
            return await vmcontrol_client.screenshot_json(vm_id)
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        if format == "binary":
            raise HTTPException(status_code=500, detail=str(e))
        else:
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

---

## 测试计划

### 单元测试

#### tests/test_multimodal_standard.py

```python
import pytest
from task_queue.utils.multimodal import extract_from_result, _parse_content_array

class TestMCPContentArray:
    """测试 MCP content 数组解析"""
    
    def test_text_content(self):
        """测试文本内容"""
        content = [
            {"type": "text", "text": "Hello World"}
        ]
        text, images = _parse_content_array(content)
        assert text == "Hello World"
        assert len(images) == 0
    
    def test_image_content(self):
        """测试图像内容"""
        content = [
            {
                "type": "image",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "mimeType": "image/png"
            }
        ]
        text, images = _parse_content_array(content)
        assert text == ""
        assert len(images) == 1
        assert images[0]["mime_type"] == "image/png"
    
    def test_mixed_content(self):
        """测试混合内容"""
        content = [
            {"type": "text", "text": "Screenshot taken"},
            {
                "type": "image",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "mimeType": "image/png"
            }
        ]
        text, images = _parse_content_array(content)
        assert text == "Screenshot taken"
        assert len(images) == 1
    
    def test_resource_content(self):
        """测试资源内容"""
        content = [
            {
                "type": "resource",
                "resource": {
                    "blob": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    "mimeType": "image/png"
                }
            }
        ]
        text, images = _parse_content_array(content)
        assert len(images) == 1


class TestExtractFromResult:
    """测试从结果中提取多模态内容"""
    
    def test_mcp_content_priority(self):
        """测试 _mcp_content 优先级最高"""
        result = {
            "_mcp_content": [
                {"type": "image", "data": "A", "mimeType": "image/png"}
            ],
            "content": [
                {"type": "image", "data": "B", "mimeType": "image/png"}
            ],
            "image_data": "C"
        }
        text, images = extract_from_result(result)
        assert images[0]["data"] == "A"
    
    def test_content_array_priority(self):
        """测试 content 数组优先于传统字段"""
        result = {
            "content": [
                {"type": "image", "data": "B", "mimeType": "image/png"}
            ],
            "image_data": "C"
        }
        text, images = extract_from_result(result)
        assert images[0]["data"] == "B"
    
    def test_legacy_image_data(self):
        """测试向后兼容 image_data 字段"""
        result = {
            "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
        text, images = extract_from_result(result)
        assert len(images) == 1
    
    def test_playwright_data_field(self):
        """测试 playwright_helper 的 data 字段"""
        result = {
            "status": "success",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
        text, images = extract_from_result(result)
        assert len(images) == 1
    
    def test_empty_result(self):
        """测试空结果"""
        result = {}
        text, images = extract_from_result(result)
        assert text == ""
        assert len(images) == 0
```

### 集成测试

#### tests/integration/test_browser_screenshot.py

```python
import pytest
from gateway.clients.vmuse_adapter import VMUseAdapter
from task_queue.utils.multimodal import extract_from_result

@pytest.mark.asyncio
async def test_browser_screenshot_mcp_format(vmuse_adapter: VMUseAdapter, test_vm_id: str):
    """测试浏览器截图返回 MCP 格式"""
    result = await vmuse_adapter.call_tool(
        tool_name="browser_screenshot",
        arguments={},
        vm_id=test_vm_id
    )
    
    # 验证返回结构
    assert result["success"] == True
    assert "result" in result
    
    # 验证 MCP 格式
    result_data = result["result"]
    assert "content" in result_data
    assert isinstance(result_data["content"], list)
    
    # 验证图像内容
    images = [c for c in result_data["content"] if c.get("type") == "image"]
    assert len(images) > 0
    assert "data" in images[0]
    assert "mimeType" in images[0]
    
    # 验证可以被 multimodal 解析
    text, extracted_images = extract_from_result(result_data)
    assert len(extracted_images) > 0
```

### 端到端测试

#### tests/e2e/test_multimodal_llm_flow.py

```python
import pytest
from mcp_client.client import MCPClient
from task_queue.utils.anthropic import to_anthropic_content

@pytest.mark.asyncio
async def test_screenshot_to_llm_flow(mcp_client: MCPClient, test_vm_id: str):
    """测试从截图到 LLM 的完整流程"""
    
    # 1. 调用截图工具
    result = await mcp_client.call_tool(
        name="browser_screenshot",
        arguments={},
        vm_id=test_vm_id
    )
    
    # 2. 提取多模态内容
    from task_queue.utils.multimodal import extract_from_result
    text, images = extract_from_result(result)
    
    assert len(images) > 0, "Should extract at least one image"
    
    # 3. 转换为 Anthropic API 格式
    content = []
    if text:
        content.append({"type": "text", "text": text})
    for img in images:
        content.append(to_anthropic_content(img))
    
    # 4. 调用 LLM
    response = await mcp_client.send_message(
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]
    )
    
    # 5. 验证 LLM 能处理图像
    assert response is not None
    assert "content" in response
```

### 回归测试

确保现有功能不被破坏：

```bash
# 运行所有测试
pytest tests/ -v

# 检查覆盖率
pytest --cov=novaic-backend --cov-report=html

# 运行特定测试套件
pytest tests/test_multimodal*.py -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

---

## 回滚方案

### 1. Git 回滚

最简单最安全的回滚方式：

```bash
# 回滚到特定提交
git revert <commit-hash>

# 回滚到标签
git reset --hard v1.0-pre-mcp

# 推送回滚
git push origin main --force
```

### 2. 功能开关

添加配置开关，支持快速切换：

```python
# config.py
USE_MCP_STANDARD = os.getenv("USE_MCP_STANDARD", "true").lower() == "true"

# multimodal.py
def extract_from_result(result: Dict[str, Any], tool_name: str = "") -> Tuple[str, List[Dict[str, str]]]:
    if not USE_MCP_STANDARD:
        # 使用旧逻辑
        return _extract_legacy_format(result)
    
    # 使用新逻辑（MCP 标准）
    # ...
```

**启用/禁用**:
```bash
# 禁用 MCP 标准（回滚）
export USE_MCP_STANDARD=false

# 启用 MCP 标准
export USE_MCP_STANDARD=true
```

### 3. 分支策略

- 在 feature branch 开发：`feature/mcp-standard`
- 充分测试后合并到 `main`
- 保留 feature branch 以便快速回滚
- 使用 git tag 标记关键版本

```bash
# 开发
git checkout -b feature/mcp-standard

# 合并
git checkout main
git merge feature/mcp-standard

# 如果需要回滚
git checkout main
git reset --hard origin/main
```

### 4. 数据库备份

如果涉及数据库变更：

```bash
# 备份
pg_dump novaic_db > backup_before_mcp.sql

# 恢复
psql novaic_db < backup_before_mcp.sql
```

---

## 风险评估

| 风险 | 影响 | 概率 | 缓解措施 | 应急方案 |
|------|------|------|----------|----------|
| 破坏现有工具 | 高 | 低 | 充分测试，向后兼容设计 | Git 回滚，功能开关 |
| 性能下降 | 中 | 低 | 性能测试，优化关键路径 | 性能调优，缓存优化 |
| LLM API 不兼容 | 高 | 低 | 提前验证，转换逻辑 | 回滚到旧格式 |
| 文档不完善 | 中 | 中 | 提前准备文档，及时更新 | 补充文档，技术支持 |
| 迁移成本高 | 低 | 低 | 分阶段迁移，可选采用 | 延长迁移周期 |
| 客户端不兼容 | 中 | 低 | 向后兼容，双格式支持 | 保留旧接口 |
| 测试覆盖不足 | 中 | 中 | 制定测试计划，高覆盖率 | 增加测试用例 |

**风险等级**: **低** ✅

**理由**:
- 采用向后兼容设计，不破坏现有功能
- 分阶段实施，降低风险
- 完善的测试和回滚方案
- 团队有充足的准备时间

---

## 时间表

| 阶段 | 时间 | 工作日 | 负责人 | 主要产出 |
|------|------|--------|--------|----------|
| **Phase 0: 准备** | 2026-02-07 ~ 02-08 | 1-2天 | Tech Lead | 标准文档、测试基准 |
| **Phase 1: 基础设施** | 2026-02-09 ~ 02-11 | 2-3天 | Backend Team | multimodal.py 升级 |
| **Phase 2: 工具适配** | 2026-02-12 ~ 02-16 | 3-5天 | Full Stack Team | 工具迁移、集成测试 |
| **Phase 3: 文档** | 2026-02-17 ~ 02-19 | 2-3天 | Tech Writer + Team | 完整文档 |
| **Phase 4: 监控** | 2026-02-20 ~ | 持续 | DevOps | 指标、优化 |

**总计**: 8-13 工作日（约 2 周）

### 里程碑

- **M1 (02-08)**: 标准文档完成，测试基准建立 ✅
- **M2 (02-11)**: 基础设施升级完成，解析器支持 MCP 格式
- **M3 (02-16)**: 所有 P0 工具迁移完成，集成测试通过
- **M4 (02-19)**: 文档完成，正式发布
- **M5 (持续)**: 监控指标达标，系统稳定运行

---

## 成功标准

### 技术指标

- [ ] **测试覆盖率**: 所有新增代码覆盖率 > 90%
- [ ] **测试通过率**: 100% 单元测试、集成测试、回归测试通过
- [ ] **性能指标**: 响应时间无退化（±5% 以内）
- [ ] **错误率**: 解析失败率 < 0.1%
- [ ] **兼容性**: 支持新旧两种格式，现有工具正常运行

### 功能指标

- [ ] **基础设施**: `multimodal.py` 支持 MCP 标准格式
- [ ] **工具迁移**: 所有 P0 工具迁移完成
  - [ ] playwright_helper.py
  - [ ] vmuse_adapter.py
  - [ ] vmcontrol.py (客户端和 API)
- [ ] **LLM 集成**: LLM 能正确接收和处理图像
- [ ] **API 更新**: 所有相关 API 端点更新完成

### 文档指标

- [ ] **标准文档**: `MULTIMODAL_STANDARD.md` 完成 ✅
- [ ] **迁移指南**: `MIGRATION_GUIDE.md` 完成 ✅
- [ ] **实施计划**: `IMPLEMENTATION_PLAN.md` 完成 ✅
- [ ] **API 文档**: `API_CHANGES.md` 完成
- [ ] **测试指南**: `TESTING_GUIDE.md` 完成
- [ ] **工具文档**: 所有工具文档更新完成

### 质量指标

- [ ] **代码审查**: 所有代码通过 code review
- [ ] **性能测试**: 性能测试通过，无明显退化
- [ ] **安全审查**: 安全审查通过，无安全漏洞
- [ ] **用户反馈**: 内部测试反馈良好

### 合规指标

- [ ] **MCP 规范**: 完全符合 MCP 2024-11-05 规范
- [ ] **向后兼容**: 现有客户端和工具正常工作
- [ ] **版本管理**: 版本信息清晰，变更记录完整

---

## 附录

### A. 参考文档

- [MCP Official Specification](https://modelcontextprotocol.io/specification)
- [MCP Content Types](https://modelcontextprotocol.io/docs/concepts/content)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)

### B. 代码仓库

- **主仓库**: `/Users/wangchaoqun/novaic`
- **Feature 分支**: `feature/mcp-standard`
- **测试数据**: `tests/fixtures/multimodal_examples.json`

### C. 工具和脚本

- **验证工具**: `python -m novaic.utils.validate_mcp`
- **格式转换**: `python -m novaic.utils.convert_legacy_format`
- **性能测试**: `python scripts/benchmark.py`

### D. 联系方式

- **技术负责人**: Tech Lead
- **Backend Team**: backend-team@novaic.com
- **紧急联系**: oncall@novaic.com

---

**文档版本**: 1.0  
**创建日期**: 2026-02-07  
**最后更新**: 2026-02-07  
**状态**: Draft  
**维护者**: NovaIC Backend Team
