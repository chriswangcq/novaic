# 多模态字段标准 (MCP Standard)

## 概述

本文档定义了 NovaIC 系统中多模态数据（图像、音频、视频等）的标准格式，遵循 MCP (Model Context Protocol) 规范。

## 版本

- **当前版本**: 1.0.0
- **MCP 规范版本**: 2024-11-05
- **更新日期**: 2026-02-07

## 设计原则

### 1. 标准优先 (Standard First)

优先使用 MCP 标准格式，确保与行业标准兼容：

```python
# ✅ 推荐：MCP 标准格式
{
    "content": [
        {"type": "text", "text": "Screenshot taken"},
        {"type": "image", "data": "base64_encoded_data", "mimeType": "image/png"}
    ]
}
```

### 2. 向后兼容 (Backward Compatible)

保持对现有格式的支持，不破坏现有功能：

```python
# ✅ 仍然支持：传统格式
{
    "image_data": "base64_encoded_data",
    "format": "png"
}
```

### 3. 类型安全 (Type Safe)

明确定义数据类型，避免歧义：

```python
# ✅ 明确的类型标识
{"type": "image", ...}
{"type": "text", ...}
{"type": "resource", ...}
```

### 4. 可扩展性 (Extensible)

设计支持未来扩展，不限制新功能：

```python
# ✅ 可扩展的元数据
{
    "type": "image",
    "data": "...",
    "mimeType": "image/png",
    "metadata": {
        "width": 1920,
        "height": 1080,
        "timestamp": "2026-02-07T10:00:00Z"
    }
}
```

## MCP 标准格式规范

### Content 数组结构

MCP 使用统一的 `content` 数组来表示多模态内容：

```typescript
interface ContentArray {
    content: Content[];
}

type Content = TextContent | ImageContent | ResourceContent;
```

### 文本内容 (Text Content)

```python
{
    "type": "text",
    "text": "Human-readable text content"
}
```

**使用场景**:
- 工具执行结果的文本描述
- 错误消息
- 状态信息

**示例**:
```python
{
    "content": [
        {"type": "text", "text": "Screenshot captured successfully"},
        {"type": "text", "text": "Resolution: 1920x1080"}
    ]
}
```

### 图像内容 (Image Content)

```python
{
    "type": "image",
    "data": "base64_encoded_image_data",
    "mimeType": "image/png" | "image/jpeg" | "image/gif" | "image/webp"
}
```

**必需字段**:
- `type`: 必须为 "image"
- `data`: Base64 编码的图像数据（不包含 data URI 前缀）
- `mimeType`: MIME 类型

**可选字段**:
```python
{
    "type": "image",
    "data": "...",
    "mimeType": "image/png",
    "metadata": {
        "width": 1920,
        "height": 1080,
        "format": "PNG",
        "timestamp": "2026-02-07T10:00:00Z",
        "source": "screenshot"
    }
}
```

**编码规则**:
- 使用标准 Base64 编码
- **不包含** `data:image/png;base64,` 前缀
- 使用 UTF-8 字符集

**示例**:
```python
import base64

# 编码图像
with open("screenshot.png", "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

result = {
    "content": [
        {
            "type": "image",
            "data": image_base64,  # 纯 Base64，无前缀
            "mimeType": "image/png"
        }
    ]
}
```

### 资源内容 (Resource Content)

#### 内嵌资源 (Embedded Resource)

```python
{
    "type": "resource",
    "resource": {
        "blob": "base64_encoded_binary_data",
        "mimeType": "application/pdf" | "audio/mp3" | "video/mp4" | ...
    }
}
```

**使用场景**:
- 非图像的二进制数据
- PDF 文档
- 音频文件
- 视频片段

**示例**:
```python
{
    "content": [
        {
            "type": "text",
            "text": "Audio recording captured"
        },
        {
            "type": "resource",
            "resource": {
                "blob": "base64_audio_data",
                "mimeType": "audio/wav"
            }
        }
    ]
}
```

#### 资源链接 (Resource Link)

```python
{
    "type": "resource",
    "resource": {
        "uri": "file:///path/to/resource",
        "mimeType": "image/png",
        "text": "Optional description"
    }
}
```

**使用场景**:
- 大文件引用
- 共享资源
- 网络资源

## 字段优先级

系统按以下优先级解析多模态内容：

### 1. `_mcp_content` (最高优先级)

MCP 客户端转换后的内部格式：

```python
{
    "_mcp_content": [
        {"type": "text", "text": "..."},
        {"type": "image", "data": "...", "mimeType": "image/png"}
    ]
}
```

**说明**: 内部使用，由 MCP 客户端自动添加。

### 2. `content` 数组 (MCP 标准)

标准 MCP 格式：

```python
{
    "content": [
        {"type": "image", "data": "...", "mimeType": "image/png"}
    ]
}
```

**说明**: 所有新工具应使用此格式。

### 3. 传统字段 (向后兼容)

按以下顺序检查：

```python
# 优先级顺序
IMAGE_FIELD_NAMES = [
    "image_data",      # ✅ 推荐
    "image_base64",    # ✅ 推荐
    "image",
    "screenshot",
    "png_data",
    "jpeg_data",
    "data",            # 支持 playwright_helper
    "base64_image",
]
```

## 支持的 MIME 类型

### 图像格式

| MIME Type | 扩展名 | 说明 |
|-----------|--------|------|
| `image/png` | .png | 推荐用于截图 |
| `image/jpeg` | .jpg, .jpeg | 推荐用于照片 |
| `image/gif` | .gif | 支持动画 |
| `image/webp` | .webp | 现代格式 |
| `image/bmp` | .bmp | 位图格式 |

### 音频格式

| MIME Type | 扩展名 | 说明 |
|-----------|--------|------|
| `audio/wav` | .wav | 无损格式 |
| `audio/mp3` | .mp3 | 压缩格式 |
| `audio/ogg` | .ogg | 开源格式 |
| `audio/webm` | .webm | 网络格式 |

### 视频格式

| MIME Type | 扩展名 | 说明 |
|-----------|--------|------|
| `video/mp4` | .mp4 | 通用格式 |
| `video/webm` | .webm | 网络格式 |
| `video/ogg` | .ogv | 开源格式 |

### 文档格式

| MIME Type | 扩展名 | 说明 |
|-----------|--------|------|
| `application/pdf` | .pdf | PDF 文档 |
| `application/json` | .json | JSON 数据 |
| `text/plain` | .txt | 纯文本 |

## 工具返回格式规范

### 标准返回格式

所有工具应遵循以下格式：

```python
# 成功返回
{
    "status": "success",
    "content": [
        {"type": "text", "text": "Operation successful"},
        {"type": "image", "data": "...", "mimeType": "image/png"}
    ]
}

# 错误返回
{
    "status": "error",
    "error": "Error message",
    "content": [
        {"type": "text", "text": "Detailed error description"}
    ]
}
```

### 向后兼容返回格式

如需支持旧客户端，可同时返回两种格式：

```python
{
    "status": "success",
    # MCP 标准格式
    "content": [
        {"type": "image", "data": "...", "mimeType": "image/png"}
    ],
    # 向后兼容字段
    "image_data": "...",
    "format": "png"
}
```

## 实现示例

### Python 工具实现

```python
import base64
from typing import Dict, Any, List

def screenshot_tool() -> Dict[str, Any]:
    """
    截图工具 - MCP 标准实现
    """
    try:
        # 获取截图
        screenshot_bytes = capture_screenshot()
        
        # 编码为 Base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # 返回 MCP 标准格式
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
                    "mimeType": "image/png",
                    "metadata": {
                        "width": 1920,
                        "height": 1080,
                        "timestamp": "2026-02-07T10:00:00Z"
                    }
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

### JavaScript/TypeScript 工具实现

```typescript
interface MCPContent {
    type: 'text' | 'image' | 'resource';
    text?: string;
    data?: string;
    mimeType?: string;
    resource?: {
        blob?: string;
        uri?: string;
        mimeType: string;
    };
}

interface MCPResult {
    status: 'success' | 'error';
    content: MCPContent[];
    error?: string;
}

async function screenshotTool(): Promise<MCPResult> {
    try {
        // 获取截图
        const screenshotBuffer = await captureScreenshot();
        
        // 编码为 Base64
        const screenshotBase64 = screenshotBuffer.toString('base64');
        
        // 返回 MCP 标准格式
        return {
            status: 'success',
            content: [
                {
                    type: 'text',
                    text: 'Screenshot captured successfully'
                },
                {
                    type: 'image',
                    data: screenshotBase64,
                    mimeType: 'image/png'
                }
            ]
        };
    } catch (error) {
        return {
            status: 'error',
            error: error.message,
            content: [
                {
                    type: 'text',
                    text: `Screenshot failed: ${error.message}`
                }
            ]
        };
    }
}
```

### 解析多模态内容

```python
from typing import Tuple, List, Dict, Any

def parse_multimodal_result(result: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """
    解析多模态工具结果
    
    Returns:
        (text_content, images_list)
    """
    text_parts = []
    images = []
    
    # 检查 content 数组
    if "content" in result and isinstance(result["content"], list):
        for item in result["content"]:
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif item.get("type") == "image":
                images.append({
                    "data": item.get("data", ""),
                    "mime_type": item.get("mimeType", "image/png")
                })
            elif item.get("type") == "resource":
                resource = item.get("resource", {})
                if resource.get("mimeType", "").startswith("image/"):
                    images.append({
                        "data": resource.get("blob", ""),
                        "mime_type": resource.get("mimeType", "image/png")
                    })
    
    # 向后兼容：检查传统字段
    elif "image_data" in result:
        images.append({
            "data": result["image_data"],
            "mime_type": f"image/{result.get('format', 'png')}"
        })
    
    return "\n".join(text_parts), images
```

## 验证规则

### 图像数据验证

```python
import re

def is_valid_base64_image(data: str) -> bool:
    """验证 Base64 图像数据"""
    # 检查长度
    if len(data) < 100:
        return False
    
    # 检查 Base64 字符集
    if not re.match(r'^[A-Za-z0-9+/=]+$', data):
        return False
    
    # 检查图像头部
    try:
        decoded = base64.b64decode(data[:20])
        # PNG 头部
        if decoded.startswith(b'\x89PNG'):
            return True
        # JPEG 头部
        if decoded.startswith(b'\xff\xd8\xff'):
            return True
        # GIF 头部
        if decoded.startswith(b'GIF89a') or decoded.startswith(b'GIF87a'):
            return True
    except:
        return False
    
    return False
```

### Content 数组验证

```python
def validate_content_array(content: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """验证 MCP content 数组"""
    if not isinstance(content, list):
        return False, "content must be an array"
    
    for i, item in enumerate(content):
        if not isinstance(item, dict):
            return False, f"content[{i}] must be an object"
        
        item_type = item.get("type")
        if item_type not in ["text", "image", "resource", "resource_link"]:
            return False, f"content[{i}].type is invalid: {item_type}"
        
        if item_type == "text":
            if "text" not in item:
                return False, f"content[{i}] missing 'text' field"
        
        elif item_type == "image":
            if "data" not in item:
                return False, f"content[{i}] missing 'data' field"
            if "mimeType" not in item:
                return False, f"content[{i}] missing 'mimeType' field"
            if not item["mimeType"].startswith("image/"):
                return False, f"content[{i}].mimeType is not an image type"
        
        elif item_type == "resource":
            if "resource" not in item:
                return False, f"content[{i}] missing 'resource' field"
            resource = item["resource"]
            if "mimeType" not in resource:
                return False, f"content[{i}].resource missing 'mimeType' field"
            if "blob" not in resource and "uri" not in resource:
                return False, f"content[{i}].resource must have 'blob' or 'uri'"
    
    return True, "valid"
```

## 迁移检查清单

### 工具开发者

- [ ] 返回格式使用 `content` 数组
- [ ] 图像使用 `type: "image"` 和 `mimeType`
- [ ] Base64 数据不包含 data URI 前缀
- [ ] 包含适当的文本描述
- [ ] 添加元数据（可选但推荐）
- [ ] 处理错误情况
- [ ] 编写单元测试
- [ ] 更新工具文档

### 系统集成

- [ ] 解析器支持 `content` 数组
- [ ] 保持向后兼容性
- [ ] 添加验证逻辑
- [ ] 更新 API 文档
- [ ] 添加集成测试
- [ ] 监控性能指标

## 常见问题 (FAQ)

### Q1: 为什么要使用 content 数组？

**A**: content 数组提供了统一的多模态内容表示方式，支持在单个响应中混合文本、图像、音频等多种类型的内容。这是 MCP 标准的核心设计。

### Q2: 旧格式何时会被废弃？

**A**: 目前没有废弃计划。系统将长期支持向后兼容格式，但强烈建议新工具使用 MCP 标准格式。

### Q3: 如何处理大文件？

**A**: 对于大文件（>10MB），建议使用 resource link 而非内嵌 blob：

```python
{
    "type": "resource",
    "resource": {
        "uri": "file:///path/to/large/file.mp4",
        "mimeType": "video/mp4",
        "text": "Large video file"
    }
}
```

### Q4: Base64 编码是否包含前缀？

**A**: 否，MCP 标准的 Base64 数据**不包含** `data:image/png;base64,` 前缀。MIME 类型通过 `mimeType` 字段单独指定。

```python
# ❌ 错误
{"data": "data:image/png;base64,iVBORw0KG..."}

# ✅ 正确
{"data": "iVBORw0KG...", "mimeType": "image/png"}
```

### Q5: 如何测试 MCP 兼容性？

**A**: 使用官方验证工具和测试套件：

```bash
# 运行标准测试
pytest tests/test_multimodal_standard.py

# 验证格式
python -m novaic.utils.validate_mcp --input result.json
```

## 参考资料

### MCP 规范

- [MCP Official Specification](https://modelcontextprotocol.io/specification)
- [MCP Content Types](https://modelcontextprotocol.io/docs/concepts/content)
- [MCP Resources](https://modelcontextprotocol.io/docs/concepts/resources)

### 相关文档

- 迁移指南（历史文档，已归档）
- `IMPLEMENTATION_PLAN.md` - 实施计划
- `API_CHANGES.md` - API 变更说明
- `TESTING_GUIDE.md` - 测试指南

## 版本历史

### 1.0.0 (2026-02-07)

- 初始版本
- 定义 MCP 标准格式
- 定义向后兼容策略
- 定义验证规则
- 添加实现示例

---

**维护者**: NovaIC Backend Team  
**最后更新**: 2026-02-07  
**状态**: Draft
