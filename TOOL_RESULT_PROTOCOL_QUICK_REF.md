# 工具返回格式快速参考

> 工具调用统一协议的快速查阅手册

---

## 标准格式

### 成功返回（纯文本）
```json
{
    "success": true,
    "content": [
        {"type": "text", "text": "执行结果"}
    ]
}
```

### 成功返回（含图片）
```json
{
    "success": true,
    "content": [
        {"type": "text", "text": "Screenshot captured"},
        {
            "type": "image",
            "data": "iVBORw0KGg...",
            "mimeType": "image/png"
        }
    ]
}
```

### 成功返回（含视频）
```json
{
    "success": true,
    "content": [
        {"type": "text", "text": "Video recorded"},
        {
            "type": "resource",
            "resource": {
                "blob": "base64_data...",
                "mimeType": "video/mp4"
            }
        }
    ]
}
```

### 失败返回
```json
{
    "success": false,
    "error": "详细错误描述",
    "error_code": "TOOL_EXEC_ERROR"
}
```

---

## content 数组元素

### 文本
```json
{"type": "text", "text": "内容"}
```

### 图片
```json
{
    "type": "image",
    "data": "base64...",
    "mimeType": "image/png"
}
```

### 资源（视频/音频/文档）
```json
{
    "type": "resource",
    "resource": {
        "blob": "base64...",
        "mimeType": "video/mp4"
    }
}
```

---

## 长结果处理

### 自动截断（仅文本）

| 文本大小 | 处理方式 |
|---------|---------|
| < 4KB | 完整返回 |
| 4KB - 10KB | 保留首尾各 1.5KB |
| > 10KB | 仅返回引用 |

**重要**：✨ **图像、视频、音频永不截断**

### 截断标记
```json
{
    "type": "text",
    "text": "First 1.5KB...",
    "_truncated": true,
    "_truncation": {
        "strategy": "head_tail",
        "original_size": 102400,
        "task_id": "so_abc12345",
        "message": "Use task_query(task_id='so_abc12345') to retrieve full content."
    }
}
```

### 获取完整内容
```python
# LLM 使用 task_query 工具
task_query(task_id="so_abc12345")
```

---

## 图像处理

### 图像压缩（自动）

| 图像大小 | 处理方式 |
|---------|---------|
| < 500KB | 不压缩 |
| > 500KB | 自动压缩 |

**压缩策略**：
- 降分辨率（最大 1920px）
- 降质量（85%）
- 保持宽高比

```json
{
    "type": "image",
    "data": "compressed_base64...",
    "mimeType": "image/png",
    "metadata": {
        "compressed": true,
        "original_size": 2048000,
        "compressed_size": 512000,
        "compression_ratio": "25.0%"
    }
}
```

---

## 内容类型处理

| 类型 | 截断 | 处理方式 |
|------|------|---------|
| 文本 | ✅ | head_tail 策略 |
| 图像 | ❌ | 压缩或完整保留 |
| 视频 | ❌ | 完整保留或降分辨率 |
| 音频 | ❌ | 完整保留或降采样 |

---

## 支持的 MIME 类型

| 类型 | MIME 类型 |
|------|-----------|
| PNG 图片 | `image/png` |
| JPEG 图片 | `image/jpeg` |
| MP4 视频 | `video/mp4` |
| WAV 音频 | `audio/wav` |
| PDF 文档 | `application/pdf` |

---

## 错误代码

| 代码 | 说明 |
|------|------|
| `TOOL_EXEC_ERROR` | 工具执行错误 |
| `TOOL_NOT_FOUND` | 工具不存在 |
| `TOOL_INVALID_ARGS` | 参数无效 |
| `HTTP_ERROR` | HTTP 请求错误 |
| `RUNTIME_NOT_FOUND` | Runtime 不存在 |

---

## 工具开发模板

```python
async def my_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = execute_logic(arguments)
        
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
        return {
            "success": False,
            "error": str(e),
            "error_code": "TOOL_EXEC_ERROR"
        }
```

---

## 配置项

```python
# 文本截断
AUTO_TRUNCATE_THRESHOLD_SMALL = 4096   # 4KB
AUTO_TRUNCATE_THRESHOLD_LARGE = 10240  # 10KB
AUTO_TRUNCATE_HEAD_SIZE = 1536         # 1.5KB
AUTO_TRUNCATE_TAIL_SIZE = 1536         # 1.5KB

# 图像压缩
IMAGE_MAX_SIZE_KB = 500                # 500KB
IMAGE_MAX_DIMENSION = 1920             # 1920px
IMAGE_QUALITY = 85                     # 85%
```

---

## 关键规则

1. ✅ **总是**返回 `{success, content}` 格式
2. ✅ **使用** MCP 标准 `content` 数组
3. ✅ **图片** Base64 编码，无 data URI 前缀
4. ✅ **指定** `mimeType` 字段
5. ✨ **图像、视频、音频永不截断**
6. ✨ **只对文本进行截断**
7. ✨ **大图像自动压缩**
8. ❌ **避免**嵌套 `{success, result}` 结构
9. ❌ **避免**使用传统字段（`image_data` 等）

---

## 需要改动的文件

| 优先级 | 文件 | 说明 |
|--------|------|------|
| P0 | `tools_server/executor.py` | 所有内置工具 + 截断机制 |
| P0 | `vmuse_adapter.py` | VM 工具适配器 + 图像压缩 |
| P1 | `gateway/api/internal/__init__.py` | 移除解包逻辑 |
| P1 | `task_queue/utils/multimodal.py` | 简化提取逻辑 |
| P1 | `common/config.py` | 添加配置项 |

---

## 相关文档

- 详细设计：`TOOL_RESULT_UNIFIED_PROTOCOL.md`
- MCP 标准：`MULTIMODAL_STANDARD.md`
- 工具开发：`dev-guide/tool-development.md`（待创建）

---

*最后更新：2026-02-07（添加图像处理说明）*
