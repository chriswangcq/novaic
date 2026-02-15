# NovaIC Tool Result Service

工具结果存储服务。采用**三要素**结构：

```json
{
  "text": "Screenshot captured.\nfile_url: /api/files/...",
  "files_created": [{"url": "...", "filename": "...", "modality": "image"}],
  "display_files": [{"url": "...", "filename": "...", "modality": "image"}]
}
```

## 三要素说明

| 字段 | 说明 | 示例场景 |
|------|------|----------|
| `text` | 文本说明，包含 file_url 供 LLM 后续使用 | 所有工具 |
| `files_created` | 本次创建的文件元数据 | screenshot, file_pull |
| `display_files` | 需要展示给 LLM 的文件（当前 round 有效） | screenshot, display |

### 场景示例

- **screenshot**: `files_created=[{...}], display_files=[{...}]` — 创建文件且展示
- **file_pull**: `files_created=[{...}], display_files=[]` — 仅创建，不展示
- **display**: `files_created=[], display_files=[{...}]` — 展示已有文件
- **file_push**: `files_created=[], display_files=[]` — 无文件操作

## 快速启动

```bash
novaic-backend tool-result-service --port 19994 --data-dir /path/to/data
```

## 依赖

- **File Service (19995)**：存储二进制，返回 URL

## 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/create` | 创建 result（传入三要素） |
| GET | `/{result_id}` | 获取 normalized（三要素结构） |
| GET | `/{result_id}/for-llm` | LLM 格式（URL→base64，支持 include_display） |
| GET | `/{result_id}/preview` | 前端预览 |
| POST | `/api/resolve` | 单 URL→base64 |
| GET | `/api/health` | 健康检查 |

## API 详情

### POST /api/create

一次性创建 result，传入三要素：

```json
// 请求
{
  "agent_id": "agent-1",
  "tool_name": "screenshot",
  "tool_call_id": "call_xxx",
  "text": "Screenshot captured.\nfile_url: /api/files/images/agent-1/xxx.png",
  "files_created": [{"url": "/api/files/images/agent-1/xxx.png", "filename": "xxx.png", "modality": "image"}],
  "display_files": [{"url": "/api/files/images/agent-1/xxx.png", "filename": "xxx.png", "modality": "image"}]
}
// 响应
{ "success": true, "result_id": "trs_a1b2c3d4" }
```

### GET /api/{result_id}

返回 normalized 结构（三要素）：

```json
{
  "success": true,
  "result_id": "trs_a1b2c3d4",
  "normalized": {
    "text": "Screenshot captured.\nfile_url: /api/files/...",
    "files_created": [...],
    "display_files": [...]
  }
}
```

### GET /api/{result_id}/for-llm

返回 LLM 可直接使用的 content，图片 URL 已解析为 base64。

参数：
- `provider`: `openai` | `anthropic`（默认 `openai`）
- `include_display`: `true` | `false`（默认 `true`）
  - `true`: 当前 round，包含 display_files 中的图片
  - `false`: 历史 round，仅返回文本

```json
// include_display=true
{
  "success": true,
  "content": [
    {"type": "text", "text": "Screenshot captured.\nfile_url: ..."},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
  ]
}

// include_display=false
{
  "success": true,
  "content": [
    {"type": "text", "text": "Screenshot captured.\nfile_url: ..."}
  ]
}
```

### GET /api/{result_id}/preview

返回摘要与元数据，用于前端预览：

```json
{
  "success": true,
  "result_id": "trs_a1b2c3d4",
  "agent_id": "agent-1",
  "tool_name": "screenshot",
  "created_at": "2024-01-01T00:00:00Z",
  "summary": "Screenshot captured.\n[1 image(s) to display]",
  "files_created_count": 1,
  "display_files_count": 1
}
```

### POST /api/resolve

单 URL 解析为 base64：

```json
{ "url": "/api/files/images/agent-1/xxx.png" }
→ { "success": true, "data": "base64..." }
```

## SDK 使用

```python
from task_queue.utils.trs_sdk import get_trs_client

client = get_trs_client()

# 创建
result_id = client.create_from_raw(raw_result, "agent-1", "screenshot")

# 获取 LLM 内容
content = client.to_llm_content(result_id, include_display=True)   # 当前 round
content = client.to_llm_content(result_id, include_display=False)  # 历史 round
```

## 消息展开

```python
from task_queue.utils.trs_client import expand_messages_for_llm

# 当前 round 的 tool 消息包含图片，历史 round 仅文本
expanded = expand_messages_for_llm(
    messages,
    provider="openai",
    current_round_id="round_123",
)
```
