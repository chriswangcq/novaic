# 工具调用返回格式统一协议

> **问题**：工具调用返回格式与 LLM API 调用不匹配，需要统一的协议标准
> 
> **涉及组件**：gateway/api/internal、vmuse_adapter、tools_server

---

## 1. 当前状况分析

### 1.1 现有返回格式

三个组件都使用相似但不完全统一的格式：

```python
# 当前格式（基本一致）
{
    "success": bool,        # 是否成功
    "result": Any,          # 结果数据（可能包含嵌套）
    "error": Optional[str]  # 错误信息
}
```

### 1.2 存在的问题

#### 问题 1：多层嵌套
```python
# 工具返回
{
    "success": True,
    "result": {
        "success": True,  # ❌ 嵌套的 success 字段
        "result": {...}   # ❌ 嵌套的 result 字段
    }
}
```

**影响**：需要额外的解包逻辑（`api.py:322-344`），增加复杂度。

#### 问题 2：多模态内容格式不统一

**三种格式并存**：

```python
# 格式 1：MCP 标准（推荐）
{
    "success": True,
    "result": {
        "content": [
            {"type": "text", "text": "..."},
            {"type": "image", "data": "base64...", "mimeType": "image/png"}
        ]
    }
}

# 格式 2：内部格式
{
    "success": True,
    "result": {
        "_mcp_content": [...],  # MCP 客户端添加
        "observation": "..."
    }
}

# 格式 3：传统格式（向后兼容）
{
    "success": True,
    "result": {
        "image_data": "base64...",  # 或 screenshot/image/png_data 等
        "format": "png"
    }
}
```

**影响**：需要复杂的优先级提取逻辑（`multimodal.py:112-207`）。

#### 问题 3：字段名不统一

**图片字段有 9 种命名**：
```python
IMAGE_FIELD_NAMES = [
    "screenshot", "image_base64", "image_data", "base64_image",
    "image", "png_data", "jpeg_data", "data"
]
```

**影响**：容易遗漏字段，维护成本高。

#### 问题 4：LLM API 转换复杂

```python
# 工具结果需要转换为 LLM 消息格式
工具返回 → extract_from_result() → 文本版本 + 图片列表
                                ↓
                         to_anthropic_content() / to_openai_content()
                                ↓
                         LLM API 消息格式
```

**影响**：多个转换步骤，容易出错。

---

## 2. 长结果截断问题

### 2.1 当前截断机制

系统在多个位置对工具结果进行截断：

| 位置 | 阈值 | 目的 | 标记 |
|------|------|------|------|
| 前端广播 | 100 字符 | 减少传输量 | `"..."` |
| Context 清理 | 5000 字符 | 防止 context 过大 | `"...[truncated]"` |
| 完整轮次 | 2000 字符 | 摘要生成 | `"... [truncated]"` |
| LLM 输入 | 1000 字符 | 节省 token | `"..."` |
| 错误信息 | 200 字符 | 保持简洁 | 无标记 |

**配置位置**：`common/config.py:ServiceConfig`

```python
TEXT_TRUNCATE_THINK = 500
TEXT_TRUNCATE_ARGS = 200
TEXT_TRUNCATE_RESULT = 2000
TEXT_TRUNCATE_LLM_INPUT = 1000
TEXT_TRUNCATE_ERROR = 200
TEXT_TRUNCATE_REASONING = 500
```

### 2.2 现有问题

1. **信息丢失**：硬截断丢失中间内容
2. **不一致**：多处硬编码阈值（如 `context.py:5000`）
3. **LLM 感知不足**：LLM 不知道如何获取完整内容
4. **自动机制缺失**：计划的 4KB 自动截断未实现

### 2.3 完整保存机制

系统已有 `TaskManager.create_completed()` 用于保存完整结果：

```python
# 保存完整结果到文件
task_id = task_manager.create_completed(
    tool_name="browser_screenshot",
    truncated_result=truncated_version,
    full_output=full_output,
    ttl_hours=24,
    agent_id=agent_id
)

# 返回 task_id 供查询
return {
    "success": True,
    "task_id": task_id,
    "message": "Result truncated, use task_query to get full output"
}
```

**问题**：该机制未集成到工具执行流程中。

---

## 3. 统一协议设计

### 2.1 核心原则

1. **单层结构**：避免嵌套 `{success, result}` 格式
2. **MCP 标准优先**：采用 MCP 标准的 `content` 数组格式
3. **向后兼容**：保留对传统字段的支持（逐步废弃）
4. **类型明确**：使用 `mimeType` 指定媒体类型

### 2.2 标准返回格式

#### 成功返回（纯文本）

```python
{
    "success": true,
    "content": [
        {
            "type": "text",
            "text": "执行结果文本"
        }
    ]
}
```

#### 成功返回（含图片）

```python
{
    "success": true,
    "content": [
        {
            "type": "text",
            "text": "Screenshot captured successfully"
        },
        {
            "type": "image",
            "data": "iVBORw0KGgoAAAANSUhEUgAA...",  # 纯 Base64，无 data URI 前缀
            "mimeType": "image/png",
            "metadata": {  # 可选
                "width": 1920,
                "height": 1080,
                "timestamp": "2026-02-07T10:00:00Z"
            }
        }
    ]
}
```

#### 成功返回（含视频/音频）

```python
{
    "success": true,
    "content": [
        {
            "type": "text",
            "text": "Video recorded"
        },
        {
            "type": "resource",
            "resource": {
                "blob": "base64_encoded_video_data",
                "mimeType": "video/mp4",
                "metadata": {  # 可选
                    "duration": 10.5,
                    "size": 1024000
                }
            }
        }
    ]
}
```

#### 失败返回

```python
{
    "success": false,
    "error": "详细的错误描述",
    "error_code": "TOOL_EXEC_ERROR",  # 可选：错误代码
    "content": [  # 可选：部分结果
        {
            "type": "text",
            "text": "部分执行结果"
        }
    ]
}
```

### 2.3 长结果处理方案

#### 方案 1：智能截断 + task_id（推荐）

**适用场景**：工具结果 > 4KB

```python
{
    "success": true,
    "content": [
        {
            "type": "text",
            "text": "First 1.5KB of output...",
            "_truncated": true,
            "_truncation": {
                "strategy": "head_tail",  # 保留头尾
                "original_size": 102400,   # 原始大小（字节）
                "truncated_size": 3000,    # 截断后大小
                "task_id": "so_abc12345",  # 完整内容的 task_id
                "message": "Output truncated. Use task_query tool to retrieve full content."
            }
        },
        {
            "type": "text",
            "text": "... [middle content removed] ..."
        },
        {
            "type": "text",
            "text": "Last 1.5KB of output..."
        }
    ]
}
```

#### 方案 2：纯引用（极简）

**适用场景**：工具结果 > 10KB

```python
{
    "success": true,
    "content": [
        {
            "type": "text",
            "text": "Output is too large (100KB). Full content saved.",
            "_truncated": true,
            "_truncation": {
                "strategy": "reference_only",
                "original_size": 102400,
                "task_id": "so_abc12345",
                "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
            }
        }
    ]
}
```

#### 方案 3：智能摘要（未来）

**适用场景**：结构化数据截断

```python
{
    "success": true,
    "content": [
        {
            "type": "text",
            "text": "File contains 1000 lines. Showing structure:\n{...summary...}",
            "_truncated": true,
            "_truncation": {
                "strategy": "llm_summary",
                "original_size": 102400,
                "task_id": "so_abc12345",
                "summary": "LLM-generated summary of the content",
                "message": "This is an AI-generated summary. Use task_query for full content."
            }
        }
    ]
}
```

### 2.4 字段定义

#### 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `success` | boolean | ✅ | 执行是否成功 |
| `content` | array | ✅ | 内容数组（MCP 标准） |
| `error` | string | ❌ | 错误信息（仅失败时） |
| `error_code` | string | ❌ | 错误代码（便于分类处理） |
| `task_id` | string | ❌ | 任务 ID（长结果时） |

#### content 数组元素类型

**文本内容**：
```python
{
    "type": "text",
    "text": str,                    # 文本内容
    "_truncated": bool,             # 可选：是否被截断
    "_truncation": dict             # 可选：截断元数据
}
```

**截断元数据** (`_truncation`)：
```python
{
    "strategy": str,        # 截断策略："head_tail", "reference_only", "llm_summary"
    "original_size": int,   # 原始大小（字节）
    "truncated_size": int,  # 截断后大小（可选）
    "task_id": str,         # 完整内容的 task_id
    "message": str,         # 提示信息
    "summary": str          # 可选：智能摘要
}
```

**图片内容**：
```python
{
    "type": "image",
    "data": str,        # Base64 编码，无 data URI 前缀
    "mimeType": str,    # 如 "image/png", "image/jpeg"
    "metadata": dict    # 可选：宽度、高度、时间戳等
}
```

**资源内容**（视频、音频、文档等）：
```python
{
    "type": "resource",
    "resource": {
        "blob": str,       # Base64 编码的二进制数据
        "mimeType": str,   # 如 "video/mp4", "audio/wav", "application/pdf"
        "metadata": dict   # 可选：时长、大小等
    }
}
```

#### 支持的 MIME 类型

**图像**：
- `image/png` - PNG 图片（推荐）
- `image/jpeg` - JPEG 图片
- `image/gif` - GIF 动画
- `image/webp` - WebP 格式

**视频**：
- `video/mp4` - MP4 视频（推荐）
- `video/webm` - WebM 视频

**音频**：
- `audio/wav` - WAV 音频（推荐）
- `audio/mp3` - MP3 音频
- `audio/ogg` - OGG 音频

**文档**：
- `application/pdf` - PDF 文档
- `application/json` - JSON 数据
- `text/plain` - 纯文本

---

## 4. 自动截断机制设计

### 4.1 触发条件

**文本内容截断阈值**：

| 阈值 | 策略 | 说明 |
|------|------|------|
| < 4KB | 不截断 | 完整返回 |
| 4KB - 10KB | `head_tail` | 保留首尾各 1.5KB |
| > 10KB | `reference_only` | 仅返回引用 |

**重要**：**图像、视频、音频等二进制内容不进行截断**。

#### 内容类型处理策略

| 内容类型 | 截断策略 | 原因 | 建议 |
|----------|----------|------|------|
| **文本** (`type: text`) | ✅ 截断 | 可以部分保留 | 使用 head_tail 策略 |
| **图像** (`type: image`) | ❌ 不截断 | 截断会破坏图像 | 压缩/降分辨率 |
| **视频** (`type: resource`, `video/*`) | ❌ 不截断 | 截断会破坏视频 | 降帧率/降分辨率 |
| **音频** (`type: resource`, `audio/*`) | ❌ 不截断 | 截断会破坏音频 | 降采样率/降比特率 |
| **文档** (`type: resource`, `application/*`) | ⚠️ 视情况 | 部分格式可提取文本 | PDF 提取文本后截断 |

### 4.2 实现位置

**工具执行后处理**（`tools_server/executor.py`）：

```python
async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # 执行工具
        result = await self._execute_internal(tool_name, arguments)
        
        # 自动截断处理
        return await self._handle_long_result(result, tool_name)
    except Exception as e:
        return {"success": False, "error": str(e)}

async def _handle_long_result(
    self,
    result: Dict[str, Any],
    tool_name: str
) -> Dict[str, Any]:
    """处理长结果"""
    # 计算内容大小
    content = result.get("content", [])
    total_size = self._calculate_content_size(content)
    
    # 小于 4KB：不处理
    if total_size < 4096:
        return result
    
    # 保存完整内容
    task_id = await self._save_full_result(result, tool_name, total_size)
    
    # 4KB - 10KB：head_tail 策略
    if total_size <= 10240:
        truncated_content = self._truncate_head_tail(content, max_size=3000)
        return {
            "success": result.get("success", True),
            "content": truncated_content + [
                {
                    "type": "text",
                    "text": f"[Content truncated: {total_size} bytes total]",
                    "_truncated": True,
                    "_truncation": {
                        "strategy": "head_tail",
                        "original_size": total_size,
                        "truncated_size": 3000,
                        "task_id": task_id,
                        "message": f"Use task_query(task_id='{task_id}') to retrieve full content."
                    }
                }
            ]
        }
    
    # > 10KB：reference_only 策略
    else:
        return {
            "success": result.get("success", True),
            "content": [
                {
                    "type": "text",
                    "text": f"Output is very large ({total_size} bytes). Full content saved to task.",
                    "_truncated": True,
                    "_truncation": {
                        "strategy": "reference_only",
                        "original_size": total_size,
                        "task_id": task_id,
                        "message": f"Use task_query(task_id='{task_id}') to retrieve full content."
                    }
                }
            ],
            "task_id": task_id
        }

async def _save_full_result(
    self,
    result: Dict[str, Any],
    tool_name: str,
    size: int
) -> str:
    """保存完整结果到 TaskManager"""
    import httpx
    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
    
    # 序列化完整结果
    full_output = json.dumps(result, ensure_ascii=False)
    
    # 生成截断版本（简单的前 500 字符）
    truncated_result = full_output[:500] + "..." if len(full_output) > 500 else full_output
    
    # 调用 Gateway API 创建 completed task
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{gateway_url}/internal/tasks/create-completed",
            json={
                "tool_name": tool_name,
                "truncated_result": truncated_result,
                "full_output": full_output,
                "ttl_hours": 24,
                "agent_id": self.agent_id
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data["task_id"]

def _calculate_content_size(self, content: List[Dict[str, Any]]) -> int:
    """
    计算 content 数组的总大小（字节）
    
    注意：只计算文本大小，图像/视频等二进制内容不计入（不应被截断）
    """
    total = 0
    for item in content:
        if item.get("type") == "text":
            total += len(item.get("text", "").encode("utf-8"))
        # 图像、视频等不计入大小（不会被截断）
    return total

def _truncate_head_tail(
    self,
    content: List[Dict[str, Any]],
    max_size: int
) -> List[Dict[str, Any]]:
    """
    保留头尾文本内容
    
    重要：只截断文本，图像/视频/音频等二进制内容完整保留
    """
    head_size = max_size // 2
    tail_size = max_size - head_size
    
    result = []
    text_size = 0  # 只统计文本大小
    
    # 收集头部
    for item in content:
        if item.get("type") == "text":
            text = item["text"]
            if text_size + len(text) <= head_size:
                result.append(item)
                text_size += len(text)
            else:
                # 部分截断文本
                remaining = head_size - text_size
                result.append({
                    "type": "text",
                    "text": text[:remaining]
                })
                text_size = head_size
                break
        else:
            # 图像、视频、音频等完整保留
            result.append(item)
    
    # 如果文本被截断，添加省略标记
    if text_size >= head_size:
        result.append({
            "type": "text",
            "text": "\n... [middle text content removed] ...\n"
        })
        
        # 收集尾部文本（从后往前）
        tail_items = []
        text_size = 0
        for item in reversed(content):
            if item.get("type") == "text":
                text = item["text"]
                if text_size + len(text) <= tail_size:
                    tail_items.insert(0, item)
                    text_size += len(text)
                else:
                    # 部分截断文本
                    remaining = tail_size - text_size
                    tail_items.insert(0, {
                        "type": "text",
                        "text": text[-remaining:]
                    })
                    break
            else:
                # 图像、视频、音频等完整保留
                tail_items.insert(0, item)
        
        result.extend(tail_items)
    
    return result
```

### 4.3 图像处理特殊策略

#### 图像太大的处理方案

**问题**：Base64 编码的高分辨率图像可能有几 MB。

**解决方案**：

**方案 1：工具层压缩（推荐）**
```python
# 在工具执行时压缩图像
async def _compress_image_if_needed(
    self,
    image_data: str,
    max_size_kb: int = 500
) -> tuple[str, dict]:
    """
    压缩图像到指定大小
    
    Returns:
        (compressed_data, metadata)
    """
    import base64
    from PIL import Image
    from io import BytesIO
    
    # 解码
    img_bytes = base64.b64decode(image_data)
    original_size = len(img_bytes)
    
    # 如果小于阈值，直接返回
    if original_size <= max_size_kb * 1024:
        return image_data, {"compressed": False, "original_size": original_size}
    
    # 压缩
    img = Image.open(BytesIO(img_bytes))
    
    # 降分辨率（保持宽高比）
    max_dimension = 1920
    if max(img.size) > max_dimension:
        ratio = max_dimension / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.LANCZOS)
    
    # 降质量
    output = BytesIO()
    img.save(output, format='PNG', optimize=True, quality=85)
    compressed_bytes = output.getvalue()
    compressed_data = base64.b64encode(compressed_bytes).decode('utf-8')
    
    metadata = {
        "compressed": True,
        "original_size": original_size,
        "compressed_size": len(compressed_bytes),
        "compression_ratio": f"{len(compressed_bytes)/original_size:.1%}"
    }
    
    return compressed_data, metadata

# 使用示例
image_data, metadata = await self._compress_image_if_needed(screenshot_data)
return {
    "success": True,
    "content": [
        {
            "type": "text",
            "text": f"Screenshot captured. {metadata.get('compression_ratio', 'No compression')}"
        },
        {
            "type": "image",
            "data": image_data,
            "mimeType": "image/png",
            "metadata": metadata
        }
    ]
}
```

**方案 2：文件引用（极大图像）**
```python
# 对于超大图像（>2MB），保存到文件
if len(image_data) > 2 * 1024 * 1024:
    # 保存到文件
    image_path = await self._save_image_to_file(image_data)
    
    return {
        "success": True,
        "content": [
            {
                "type": "text",
                "text": f"Screenshot is very large. Saved to file."
            },
            {
                "type": "image",
                "data": image_data[:1000] + "...",  # 缩略图或占位符
                "mimeType": "image/png",
                "_file_reference": {
                    "path": image_path,
                    "size": len(image_data),
                    "message": "Full image saved to file system"
                }
            }
        ]
    }
```

### 4.4 配置化

**新增配置项**（`common/config.py`）：

```python
# ===== 长结果截断配置 =====
AUTO_TRUNCATE_ENABLED = bool(os.getenv("AUTO_TRUNCATE_ENABLED", "true").lower() == "true")
AUTO_TRUNCATE_THRESHOLD_SMALL = int(os.getenv("AUTO_TRUNCATE_THRESHOLD_SMALL", "4096"))  # 4KB（仅文本）
AUTO_TRUNCATE_THRESHOLD_LARGE = int(os.getenv("AUTO_TRUNCATE_THRESHOLD_LARGE", "10240"))  # 10KB（仅文本）
AUTO_TRUNCATE_HEAD_SIZE = int(os.getenv("AUTO_TRUNCATE_HEAD_SIZE", "1536"))  # 1.5KB
AUTO_TRUNCATE_TAIL_SIZE = int(os.getenv("AUTO_TRUNCATE_TAIL_SIZE", "1536"))  # 1.5KB
AUTO_TRUNCATE_TTL_HOURS = int(os.getenv("AUTO_TRUNCATE_TTL_HOURS", "24"))

# ===== 图像处理配置 =====
IMAGE_COMPRESS_ENABLED = bool(os.getenv("IMAGE_COMPRESS_ENABLED", "true").lower() == "true")
IMAGE_MAX_SIZE_KB = int(os.getenv("IMAGE_MAX_SIZE_KB", "500"))  # 500KB
IMAGE_MAX_DIMENSION = int(os.getenv("IMAGE_MAX_DIMENSION", "1920"))  # 1920px
IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", "85"))  # 85%
```

### 4.5 task_query 工具增强

确保 LLM 可以通过 `task_query` 工具获取完整内容：

```python
# 工具定义
{
    "name": "task_query",
    "description": "Query the full output of a completed task by task_id. Use this when tool results are truncated.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "The task ID returned in _truncation.task_id"
            }
        },
        "required": ["task_id"]
    }
}
```

---

## 5. 实施方案

### 5.1 迁移策略

#### 阶段 1：向后兼容（当前）✅

**已实现**：
- 支持 MCP 标准格式（`content` 数组）
- 支持内部格式（`_mcp_content`）
- 支持传统格式（`image_data` 等）
- 优先级提取逻辑

**位置**：
- `task_queue/utils/multimodal.py:extract_from_result()`
- `mcp_client/mcp_client.py:_convert_tool_result()`

#### 阶段 2：规范化 + 自动截断（建议立即执行）

**目标**：所有工具统一返回 MCP 标准格式 + 自动截断机制

**改动组件**：

1. **tools_server/executor.py**（核心）
   - 所有内置工具返回 `{success, content}` 格式
   - 移除嵌套 `{success, result}` 结构
   - 实现 `_handle_long_result()` 自动截断
   - 实现 `_save_full_result()` 保存完整内容

2. **vmuse_adapter.py**
   - 转换 vmcontrol API 返回值为标准格式
   - 统一使用 `content` 数组
   - 集成截断处理（对于大型截图等）

3. **gateway/api/internal/**
   - 内部 API 返回标准格式
   - 移除解包逻辑（`api.py:322-344`）
   - 确保 `/tasks/create-completed` API 正常工作

4. **common/config.py**
   - 添加自动截断配置项
   - 统一所有截断阈值配置

#### 阶段 3：优化和废弃（未来）

**目标**：完全移除传统字段支持

**步骤**：
1. 在日志中标记传统格式使用（添加 warning）
2. 监控 3 个月，确认无使用
3. 移除 `IMAGE_FIELD_NAMES` 相关逻辑

### 5.2 改动清单

#### 优先级 P0：核心转换层 + 自动截断

| 文件 | 改动内容 | 影响范围 | 工作量 |
|------|----------|----------|--------|
| `tools_server/executor.py` | 1. 统一返回格式 `{success, content}`<br>2. 实现自动截断机制（仅文本）<br>3. 实现图像压缩机制 | 所有工具调用 | 🔴 大 |
| `vmuse_adapter.py` | 转换为标准格式 + 图像压缩 | VM 工具 | 🟡 中 |
| `mcp_client/mcp_client.py` | 保持 `_mcp_content` 转换 | MCP 工具 | 🟢 小 |
| `common/config.py` | 添加截断和图像处理配置项 | 全局配置 | 🟢 小 |

#### 优先级 P1：辅助组件

| 文件 | 改动内容 | 影响范围 | 工作量 |
|------|----------|----------|--------|
| `gateway/api/internal/__init__.py` | 移除解包逻辑 | 内部 API | 🟢 小 |
| `gateway/api/internal/task.py` | 确保 create-completed API 正常 | 任务管理 | 🟢 小 |
| `task_queue/utils/multimodal.py` | 简化提取逻辑 | 多模态处理 | 🟡 中 |
| `task_queue/utils/context.py` | 移除硬编码阈值 | Context 处理 | 🟢 小 |

#### 优先级 P2：工具和文档

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 确保 `task_query` 工具可用 | LLM 查询完整内容 | 🟢 小 |
| 更新 System Prompt | 告知 LLM 截断机制 | 🟢 小 |
| 更新 API 文档 | 记录标准格式和截断 | 🟡 中 |
| 添加单元测试 | 验证格式转换和截断 | 🟡 中 |
| 更新开发指南 | 工具开发规范 | 🟢 小 |

### 5.3 示例改动

#### 改动前（executor.py）

```python
# 文件读取工具
async def _execute_file_read(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    response = await client.get(f"/internal/rt/{self.runtime_id}/file/read", params={"path": path})
    result = self._handle_response(response)
    
    # ❌ 返回嵌套结构
    return {
        "success": True,
        "result": {
            "content": result.get("content", ""),
            "size": result.get("size", 0),
            "path": path
        }
    }
```

#### 改动后（executor.py）

```python
# 文件读取工具
async def _execute_file_read(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    response = await client.get(f"/internal/rt/{self.runtime_id}/file/read", params={"path": path})
    result = self._handle_response(response)
    
    # ✅ 返回标准格式
    return {
        "success": True,
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "content": result.get("content", ""),
                    "size": result.get("size", 0),
                    "path": path
                }, ensure_ascii=False)
            }
        ]
    }
```

#### 改动前（vmuse_adapter.py）

```python
# 浏览器截图
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
    result = response.json()
    
    # ❌ 多种格式混用
    if "content" in result:
        return {
            "success": result.get("status") == "success",
            "result": {
                "_mcp_content": result["content"]
            }
        }
    else:
        image_data = result.get("data") or result.get("image_data", "")
        return {
            "success": True,
            "result": {
                "image_data": image_data,
                "format": result.get("format", "png")
            }
        }
```

#### 改动后（vmuse_adapter.py）

```python
# 浏览器截图
async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
    result = response.json()
    
    # ✅ 统一转换为标准格式
    if "content" in result and isinstance(result["content"], list):
        # 已是 MCP 标准格式
        return {
            "success": result.get("status") == "success",
            "content": result["content"]
        }
    else:
        # 转换为标准格式
        image_data = result.get("data") or result.get("image_data", "")
        return {
            "success": True,
            "content": [
                {
                    "type": "text",
                    "text": "Screenshot captured successfully"
                },
                {
                    "type": "image",
                    "data": image_data,
                    "mimeType": f"image/{result.get('format', 'png')}"
                }
            ]
        }
```

#### 简化提取逻辑（multimodal.py）

```python
# 改动前：复杂的优先级检查
def extract_from_result(result: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    # 1. 检查 _mcp_content
    # 2. 检查 content 数组
    # 3. 检查传统字段（9 种命名）
    # ... 100+ 行代码

# 改动后：简化为单一来源
def extract_from_result(result: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """从标准格式提取文本和图片"""
    text_parts = []
    images = []
    
    content = result.get("content", [])
    if not isinstance(content, list):
        logger.warning(f"Invalid content format: {type(content)}")
        return "", []
    
    for item in content:
        item_type = item.get("type", "")
        
        if item_type == "text":
            text_parts.append(item.get("text", ""))
            
        elif item_type == "image":
            images.append({
                "data": item.get("data", ""),
                "mime_type": item.get("mimeType", "image/png")
            })
            
        elif item_type == "resource":
            resource = item.get("resource", {})
            mime_type = resource.get("mimeType", "")
            if mime_type.startswith("image/"):
                images.append({
                    "data": resource.get("blob", ""),
                    "mime_type": mime_type
                })
    
    return "\n".join(text_parts), images
```

---

## 6. 验证和测试

### 6.1 测试用例

#### 测试 1：纯文本工具
```python
# 输入
result = {"success": True, "content": [{"type": "text", "text": "Hello"}]}

# 预期输出
text, images = extract_from_result(result)
assert text == "Hello"
assert images == []
```

#### 测试 2：图片工具
```python
# 输入
result = {
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot taken"},
        {"type": "image", "data": "base64...", "mimeType": "image/png"}
    ]
}

# 预期输出
text, images = extract_from_result(result)
assert text == "Screenshot taken"
assert len(images) == 1
assert images[0]["mime_type"] == "image/png"
```

#### 测试 3：长结果截断（仅文本）
```python
# 输入（10KB 文本）
result = {
    "success": True,
    "content": [{"type": "text", "text": "A" * 10000}]
}

# 预期输出（head_tail 策略）
processed = await executor.execute("some_tool", {})
assert processed["success"] == True
assert len(processed["content"]) >= 3  # head + marker + tail
assert "... [middle text content removed] ..." in str(processed["content"])
assert any(item.get("_truncated") for item in processed["content"])
assert "task_id" in next(item.get("_truncation", {}) for item in processed["content"] if item.get("_truncated"))
```

#### 测试 3.5：图像不被截断
```python
# 输入（大文本 + 图像）
result = {
    "success": True,
    "content": [
        {"type": "text", "text": "A" * 10000},
        {"type": "image", "data": "base64_image_data...", "mimeType": "image/png"}
    ]
}

# 预期输出（文本被截断，图像完整保留）
processed = await executor.execute("screenshot_tool", {})
assert processed["success"] == True

# 检查图像完整
image_item = next(item for item in processed["content"] if item.get("type") == "image")
assert image_item["data"] == "base64_image_data..."  # 图像数据未被截断
assert "_truncated" not in image_item  # 图像不标记为截断

# 检查文本被截断
text_items = [item for item in processed["content"] if item.get("type") == "text"]
assert any("... [middle text content removed] ..." in item.get("text", "") for item in text_items)
```

#### 测试 4：task_query 获取完整内容
```python
# 执行长结果工具
result = await executor.execute("file_read", {"path": "/large/file.txt"})
task_id = result["content"][0]["_truncation"]["task_id"]

# 查询完整内容
full_result = await executor.execute("task_query", {"task_id": task_id})
assert full_result["success"] == True
assert len(full_result["content"][0]["text"]) > 10000
```

#### 测试 5：失败处理
```python
# 输入
result = {"success": False, "error": "Tool failed", "content": []}

# 预期输出
assert result["success"] == False
assert "error" in result
```

### 6.2 回归测试

**确保不破坏现有功能**：

1. ✅ 现有工具调用正常
2. ✅ 图片显示正常（**图像不被截断**）
3. ✅ LLM API 调用正常
4. ✅ 向后兼容（传统格式仍可处理）
5. ✅ 大文本被截断但图像完整保留
6. ✅ 图像压缩不影响显示质量

---

## 7. 错误处理规范

### 7.1 错误代码定义

建议定义标准错误代码，便于分类处理：

```python
# 工具执行错误
TOOL_EXEC_ERROR = "TOOL_EXEC_ERROR"           # 通用执行错误
TOOL_NOT_FOUND = "TOOL_NOT_FOUND"             # 工具不存在
TOOL_INVALID_ARGS = "TOOL_INVALID_ARGS"       # 参数无效
TOOL_PERMISSION_DENIED = "TOOL_PERMISSION_DENIED"  # 权限不足

# 网络错误
HTTP_ERROR = "HTTP_ERROR"                     # HTTP 请求错误
NETWORK_TIMEOUT = "NETWORK_TIMEOUT"           # 网络超时

# 资源错误
RUNTIME_NOT_FOUND = "RUNTIME_NOT_FOUND"       # Runtime 不存在
VM_NOT_AVAILABLE = "VM_NOT_AVAILABLE"         # VM 不可用
```

### 7.2 错误返回示例

```python
{
    "success": false,
    "error": "Tool 'browser_click' execution failed: element not found",
    "error_code": "TOOL_EXEC_ERROR",
    "content": [
        {
            "type": "text",
            "text": "Attempted to click element with selector '#submit-btn', but element was not found on page."
        }
    ]
}
```

---

## 8. 文档和规范

### 8.1 工具开发规范

**新工具必须**：
1. 返回 `{success, content}` 格式
2. 使用 MCP 标准 `content` 数组
3. 图片使用 Base64 编码，指定 `mimeType`
4. 提供清晰的错误信息

**示例模板**：
```python
async def my_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    工具描述
    
    Args:
        arguments: 工具参数
        
    Returns:
        标准格式：
        {
            "success": bool,
            "content": [...],
            "error": str (optional)
        }
    """
    try:
        # 执行工具逻辑
        result = execute_logic(arguments)
        
        # 返回标准格式
        return {
            "success": True,
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False)
                }
            ]
        }
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "TOOL_EXEC_ERROR"
        }
```

### 8.2 System Prompt 更新

**添加截断机制说明**：

```
When tools return large outputs (>4KB), the system automatically truncates them:
- 4-10KB: Head (1.5KB) + tail (1.5KB) with middle content removed
- >10KB: Only a reference is returned

Look for "_truncated": true in tool results. When present, use the task_query tool with the provided task_id to retrieve the full content:

Example:
{
  "type": "text",
  "text": "Output truncated...",
  "_truncated": true,
  "_truncation": {
    "task_id": "so_abc12345",
    "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
  }
}

Use: task_query(task_id="so_abc12345")
```

### 8.3 更新的文档列表

| 文档 | 更新内容 |
|------|----------|
| `dev-guide/tool-development.md` | 新增：工具开发规范 |
| `MULTIMODAL_STANDARD.md` | 更新：标准格式定义 |
| `API_CHANGES.md` | 记录：格式变更 |

---

## 9. 时间线

### 短期（1-2 周）- 阶段 2

- [ ] 实现自动截断机制（`tools_server/executor.py`）
  - [ ] `_handle_long_result()` 函数
  - [ ] `_save_full_result()` 集成
  - [ ] `_truncate_head_tail()` 实现
- [ ] 添加截断配置项（`common/config.py`）
- [ ] 更新 `vmuse_adapter.py`（VM 工具）
- [ ] 确保 `task_query` 工具可用
- [ ] 更新 System Prompt
- [ ] 添加单元测试

### 中期（2-4 周）

- [ ] 简化 `multimodal.py` 提取逻辑
- [ ] 更新所有内部 API
- [ ] 移除解包逻辑
- [ ] 添加错误代码系统
- [ ] 实现智能摘要策略（可选）
- [ ] 更新文档

### 长期（3-6 个月）- 阶段 3

- [ ] 监控传统格式使用
- [ ] 监控截断策略效果
- [ ] 优化截断阈值
- [ ] 逐步废弃传统字段
- [ ] 完全移除兼容代码

---

## 10. 总结

### 8.1 协议优势

1. **统一性**：所有工具使用相同格式
2. **可扩展性**：支持文本、图片、视频、音频等
3. **标准化**：遵循 MCP 标准
4. **向后兼容**：不破坏现有功能
5. **易于维护**：减少转换逻辑

### 8.2 关键改进

- ✅ 移除多层嵌套
- ✅ 统一多模态格式
- ✅ 简化字段命名
- ✅ 标准化错误处理

### 8.3 下一步

1. **讨论并确认**协议设计
2. **选择试点组件**开始迁移
3. **逐步推广**到所有组件
4. **监控和优化**实施效果

---

## 附录：参考文件

| 文件 | 行号 | 说明 |
|------|------|------|
| `tools_server/api.py` | 34-38 | `CallToolResponse` 定义 |
| `tools_server/api.py` | 322-344 | 解包逻辑（待移除） |
| `vmuse_adapter.py` | 120-145 | 工具调用入口 |
| `vmuse_adapter.py` | 421-450 | 浏览器截图处理 |
| `multimodal.py` | 112-207 | 多模态内容提取 |
| `multimodal.py` | 297-334 | `result_to_text_only` |
| `mcp_client.py` | 665-706 | MCP 结果转换 |
| `context.py` | 209-255 | 工具结果 context 处理 |

---

## 附录 B：截断机制相关文件

| 文件 | 当前截断位置 | 阈值 | 说明 |
|------|-------------|------|------|
| `task_queue/utils/result.py` | `summarize_result()` | 100 | 前端广播 |
| `task_queue/utils/simple_summary.py` | `format_round_full()` | 2000 | 完整轮次 |
| `task_queue/utils/simple_summary.py` | `format_rounds_for_llm()` | 1000 | LLM 输入 |
| `task_queue/handlers/llm_handlers.py` | 错误/推理截断 | 200/500 | 错误和推理 |
| `task_queue/utils/context.py` | `clean_context_for_summary()` | 5000 | Context 清理 |
| `gateway/core/task_manager.py` | `create_completed()` | N/A | 完整保存（未集成） |

**建议**：逐步迁移这些截断逻辑到统一的自动截断机制。

---

## 附录 C：截断流程对比

### 当前流程
```
工具执行 → 返回结果
              ↓
       多处独立截断
       ├─ 前端广播截断（100）
       ├─ Context 截断（5000）
       ├─ 摘要截断（2000）
       └─ LLM 输入截断（1000）
              ↓
       发送给 LLM（信息已丢失）
```

### 新流程
```
工具执行 → 返回结果
              ↓
       检查大小（executor.py）
              ↓
       < 4KB：完整返回
       > 4KB：自动截断
       ├─ 保存完整内容到文件（task_id）
       ├─ 返回 head_tail 或引用
       └─ 添加 _truncation 元数据
              ↓
       LLM 收到截断标记
              ↓
       LLM 使用 task_query(task_id) 获取完整内容
```

---

*创建时间：2026-02-07*
*最后更新：2026-02-07（添加长结果截断机制）*
