# API 变更说明

## 概述

本文档记录了 MCP 多模态标准化改造中涉及的所有 API 变更。

**版本**: 1.0.0  
**变更日期**: 2026-02-07  
**向后兼容**: 是

## 变更原则

1. **默认使用新格式**: 所有 API 默认返回 MCP 标准格式
2. **可选旧格式支持**: 通过参数支持旧格式（过渡期）
3. **自动转换**: 系统自动处理新旧格式转换
4. **版本标识**: 通过 Header 或参数标识 API 版本

## API 变更清单

### 1. VMControl API

#### 1.1 GET/POST `/api/vmcontrol/vms/{vm_id}/screenshot`

**变更类型**: 响应格式变更

**变更前**:

```http
POST /api/vmcontrol/vms/{vm_id}/screenshot
Accept: image/png

Response:
Content-Type: image/png
[Binary PNG data]
```

**变更后（推荐）**:

```http
POST /api/vmcontrol/vms/{vm_id}/screenshot
Accept: application/json

Response:
Content-Type: application/json

{
    "status": "success",
    "content": [
        {
            "type": "image",
            "data": "base64_encoded_png_data",
            "mimeType": "image/png"
        }
    ]
}
```

**向后兼容方式**:

```http
POST /api/vmcontrol/vms/{vm_id}/screenshot?format=binary
Accept: image/png

Response:
Content-Type: image/png
[Binary PNG data]
```

**参数说明**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `format` | string | "json" | 响应格式：<br>- "json": MCP 标准 JSON 格式（推荐）<br>- "binary": PNG 二进制数据（向后兼容） |

**错误响应**:

```json
{
    "status": "error",
    "error": "VM not found",
    "content": [
        {
            "type": "text",
            "text": "VM with ID 'xxx' not found"
        }
    ]
}
```

**迁移指南**:

```python
# 旧代码
response = requests.post(f"/api/vmcontrol/vms/{vm_id}/screenshot")
image_bytes = response.content

# 新代码（推荐）
response = requests.post(f"/api/vmcontrol/vms/{vm_id}/screenshot")
result = response.json()
image_base64 = result["content"][0]["data"]
image_bytes = base64.b64decode(image_base64)

# 或者继续使用旧格式（过渡期）
response = requests.post(f"/api/vmcontrol/vms/{vm_id}/screenshot?format=binary")
image_bytes = response.content
```

---

### 2. Browser Control API

#### 2.1 POST `/api/vms/{vm_id}/browser/screenshot`

**变更类型**: 新增 API

**端点**: `POST /api/vms/{vm_id}/browser/screenshot`

**请求**:

```http
POST /api/vms/{vm_id}/browser/screenshot
Content-Type: application/json

{
    "full_page": false  // 可选
}
```

**响应**:

```json
{
    "status": "success",
    "content": [
        {
            "type": "text",
            "text": "Screenshot captured"
        },
        {
            "type": "image",
            "data": "base64_encoded_png_data",
            "mimeType": "image/png",
            "metadata": {
                "width": 1920,
                "height": 1080,
                "url": "https://example.com",
                "timestamp": "2026-02-07T10:00:00Z"
            }
        }
    ]
}
```

**错误响应**:

```json
{
    "status": "error",
    "error": "Browser not available",
    "content": [
        {
            "type": "text",
            "text": "Browser is not running on this VM"
        }
    ]
}
```

---

### 3. Desktop Screenshot API

#### 3.1 POST `/api/vms/{vm_id}/screenshot`

**变更类型**: 响应格式变更（与 VMControl API 类似）

**变更前**:

```json
{
    "image_data": "base64_encoded_data",
    "format": "png",
    "width": 1920,
    "height": 1080
}
```

**变更后**:

```json
{
    "status": "success",
    "content": [
        {
            "type": "image",
            "data": "base64_encoded_data",
            "mimeType": "image/png",
            "metadata": {
                "width": 1920,
                "height": 1080
            }
        }
    ]
}
```

**向后兼容**: 系统自动识别新旧客户端，旧客户端仍返回旧格式。

---

### 4. Tool Execution API

#### 4.1 POST `/api/tools/execute`

**变更类型**: 响应格式标准化

**端点**: `POST /api/tools/execute`

**请求**:

```json
{
    "tool_name": "browser_screenshot",
    "arguments": {},
    "vm_id": "test-vm-id"
}
```

**变更前**:

```json
{
    "success": true,
    "result": {
        "image_data": "base64_encoded_data",
        "format": "png"
    }
}
```

**变更后**:

```json
{
    "success": true,
    "result": {
        "status": "success",
        "content": [
            {
                "type": "text",
                "text": "Screenshot captured"
            },
            {
                "type": "image",
                "data": "base64_encoded_data",
                "mimeType": "image/png"
            }
        ]
    }
}
```

---

## 通用响应格式

### 成功响应

所有成功的多模态响应都应遵循以下格式：

```typescript
interface SuccessResponse {
    status: "success";
    content: Content[];
    metadata?: Record<string, any>;  // 可选
}

type Content = TextContent | ImageContent | ResourceContent;

interface TextContent {
    type: "text";
    text: string;
}

interface ImageContent {
    type: "image";
    data: string;           // Base64 encoded, no data URI prefix
    mimeType: string;       // e.g., "image/png"
    metadata?: {            // 可选
        width?: number;
        height?: number;
        timestamp?: string;
        [key: string]: any;
    };
}

interface ResourceContent {
    type: "resource";
    resource: {
        blob?: string;      // Base64 encoded binary data
        uri?: string;       // Resource URI
        mimeType: string;
        text?: string;      // Optional description
    };
}
```

### 错误响应

```typescript
interface ErrorResponse {
    status: "error";
    error: string;          // Error message
    error_code?: string;    // Optional error code
    content: Content[];     // Human-readable error details
}
```

**示例**:

```json
{
    "status": "error",
    "error": "VM not found",
    "error_code": "VM_NOT_FOUND",
    "content": [
        {
            "type": "text",
            "text": "The VM with ID 'test-vm-id' does not exist or has been deleted"
        }
    ]
}
```

---

## 客户端适配指南

### Python 客户端

#### 旧代码

```python
# 旧格式处理
response = requests.post(f"/api/vms/{vm_id}/screenshot")
result = response.json()

if "image_data" in result:
    image_data = result["image_data"]
elif "data" in result:
    image_data = result["data"]
```

#### 新代码

```python
from typing import List, Dict, Any

def extract_images(result: Dict[str, Any]) -> List[str]:
    """提取图像数据"""
    images = []
    
    # 检查 MCP 格式
    if "content" in result:
        for item in result["content"]:
            if item.get("type") == "image":
                images.append(item["data"])
    
    # 向后兼容
    elif "image_data" in result:
        images.append(result["image_data"])
    elif "data" in result:
        images.append(result["data"])
    
    return images

# 使用
response = requests.post(f"/api/vms/{vm_id}/screenshot")
result = response.json()
images = extract_images(result)
```

#### 使用工具函数

```python
# 推荐：使用系统提供的工具函数
from task_queue.utils.multimodal import extract_from_result

response = requests.post(f"/api/vms/{vm_id}/screenshot")
result = response.json()

text, images = extract_from_result(result)
# images: List[Dict[str, str]] with keys: "data", "mime_type"
```

### JavaScript/TypeScript 客户端

#### 旧代码

```typescript
const response = await fetch(`/api/vms/${vmId}/screenshot`);
const blob = await response.blob();
const imageUrl = URL.createObjectURL(blob);
```

#### 新代码

```typescript
interface MCPContent {
    type: 'text' | 'image' | 'resource';
    text?: string;
    data?: string;
    mimeType?: string;
}

interface MCPResponse {
    status: 'success' | 'error';
    content: MCPContent[];
    error?: string;
}

async function getScreenshot(vmId: string): Promise<string[]> {
    const response = await fetch(`/api/vms/${vmId}/screenshot`);
    const result: MCPResponse = await response.json();
    
    if (result.status === 'error') {
        throw new Error(result.error);
    }
    
    // 提取图像
    const images = result.content
        .filter(item => item.type === 'image')
        .map(item => item.data!);
    
    return images;
}

// 使用
const images = await getScreenshot('test-vm-id');
const imageUrl = `data:image/png;base64,${images[0]}`;
```

#### 向后兼容

```typescript
async function getScreenshot(vmId: string, useLegacy: boolean = false): Promise<Blob> {
    if (useLegacy) {
        // 旧格式：返回二进制数据
        const response = await fetch(`/api/vms/${vmId}/screenshot?format=binary`);
        return await response.blob();
    } else {
        // 新格式：返回 JSON
        const response = await fetch(`/api/vms/${vmId}/screenshot`);
        const result: MCPResponse = await response.json();
        
        const imageData = result.content.find(item => item.type === 'image')?.data;
        if (!imageData) {
            throw new Error('No image in response');
        }
        
        // 转换为 Blob
        const binary = atob(imageData);
        const array = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            array[i] = binary.charCodeAt(i);
        }
        return new Blob([array], { type: 'image/png' });
    }
}
```

---

## API 版本管理

### 版本标识

#### 方式 1: 通过 Header

```http
POST /api/vms/{vm_id}/screenshot
X-API-Version: 2.0
```

#### 方式 2: 通过 URL

```http
POST /api/v2/vms/{vm_id}/screenshot
```

#### 方式 3: 通过参数

```http
POST /api/vms/{vm_id}/screenshot?api_version=2.0
```

### 版本对照表

| 版本 | 响应格式 | 支持状态 |
|------|----------|----------|
| 1.0 | 旧格式（`image_data`） | ✅ 支持（向后兼容） |
| 2.0 | MCP 标准格式（`content` 数组） | ✅ 默认 |

---

## 废弃计划

### 当前计划

**无废弃计划** - 系统将长期支持向后兼容格式。

### 未来可能的废弃（仅供参考）

如果将来决定废弃旧格式：

| 时间 | 阶段 | 说明 |
|------|------|------|
| 2026 Q3 | 公告 | 宣布旧格式进入废弃流程 |
| 2026 Q4 | 警告 | 使用旧格式时返回 deprecation warning |
| 2027 Q1 | 移除 | 完全移除旧格式支持 |

**注意**: 这只是假设性的时间线，实际废弃计划需要根据实际使用情况决定。

---

## 测试 API 变更

### 使用 curl 测试

#### 测试新格式

```bash
# 截图 API
curl -X POST http://localhost:8000/api/vmcontrol/vms/test-vm/screenshot \
  -H "Content-Type: application/json" | jq

# 浏览器截图 API
curl -X POST http://localhost:8000/api/vms/test-vm/browser/screenshot \
  -H "Content-Type: application/json" | jq
```

#### 测试旧格式（向后兼容）

```bash
curl -X POST "http://localhost:8000/api/vmcontrol/vms/test-vm/screenshot?format=binary" \
  --output screenshot.png
```

### 使用 Python 测试

```python
import requests
import base64

# 测试新格式
response = requests.post("http://localhost:8000/api/vmcontrol/vms/test-vm/screenshot")
result = response.json()

print(f"Status: {result['status']}")
print(f"Content items: {len(result['content'])}")

for item in result["content"]:
    if item["type"] == "image":
        print(f"Image MIME type: {item['mimeType']}")
        print(f"Image data length: {len(item['data'])}")
        
        # 保存图像
        image_data = base64.b64decode(item["data"])
        with open("screenshot.png", "wb") as f:
            f.write(image_data)

# 测试旧格式
response = requests.post("http://localhost:8000/api/vmcontrol/vms/test-vm/screenshot?format=binary")
with open("screenshot_binary.png", "wb") as f:
    f.write(response.content)
```

### 使用 Postman/Insomnia

**新格式**:

```
POST {{base_url}}/api/vmcontrol/vms/{{vm_id}}/screenshot
Content-Type: application/json

Response Schema:
{
    "status": "success",
    "content": [
        {
            "type": "image",
            "data": "string",
            "mimeType": "string"
        }
    ]
}
```

**旧格式**:

```
POST {{base_url}}/api/vmcontrol/vms/{{vm_id}}/screenshot?format=binary
Accept: image/png

Response: Binary PNG data
```

---

## 常见问题 (FAQ)

### Q1: 我需要立即更新客户端吗？

**A**: 不需要。系统支持向后兼容，旧客户端可以继续使用。但建议逐步迁移到新格式以享受标准化带来的好处。

### Q2: 新格式会影响性能吗？

**A**: 影响很小。JSON 序列化的开销可以忽略不计，且 Base64 编码是必需的（无论哪种格式）。

### Q3: 如何判断 API 返回的是新格式还是旧格式？

**A**: 检查响应中是否包含 `content` 数组：

```python
if "content" in result and isinstance(result["content"], list):
    # 新格式（MCP 标准）
else:
    # 旧格式
```

### Q4: 我可以同时支持新旧两种格式吗？

**A**: 可以。参考"客户端适配指南"中的示例代码。

### Q5: API 版本如何标识？

**A**: 目前通过响应格式自动识别。未来可能引入显式的版本标识（Header 或 URL）。

---

## 联系和支持

### 技术支持

- **Email**: backend-team@novaic.com
- **Slack**: #novaic-api-support
- **文档**: https://docs.novaic.com/api

### 报告问题

- **Bug Report**: https://github.com/novaic/novaic/issues
- **Feature Request**: https://github.com/novaic/novaic/discussions

---

**文档版本**: 1.0.0  
**创建日期**: 2026-02-07  
**最后更新**: 2026-02-07  
**状态**: Draft  
**维护者**: NovaIC Backend Team
