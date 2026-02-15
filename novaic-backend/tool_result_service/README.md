# NovaIC Tool Result Service

工具结果规范与存储。采用 **create + insert** 模式：先创建 result，再逐项追加 content。

## 快速启动

```bash
novaic-backend tool-result-service --port 19994 --data-dir /path/to/data
```

## 依赖

- **File Service (19995)**：存储二进制，返回 URL

## 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/create` | 创建空 result，返回 result_id |
| POST | `/{result_id}/insert/text` | 追加文本项（长文本自动截断） |
| POST | `/{result_id}/insert/image` | 追加图片项（url 或 base64 data） |
| POST | `/{result_id}/insert/resource` | 追加资源项（url 或 base64 data） |
| GET | `/{result_id}` | 获取 normalized |
| GET | `/{result_id}/for-llm` | LLM 格式（URL→base64） |
| GET | `/{result_id}/preview` | 前端预览 |
| GET | `/{result_id}/full` | 完整内容（含长文本） |
| POST | `/api/resolve` | 单 URL→base64 |
| GET | `/api/health` | 健康检查 |

## API 详情

### POST /api/create

```json
// 请求
{ "agent_id": "agent-1", "tool_name": "desktop_screenshot", "tool_call_id": "call_xxx" }
// 响应
{ "success": true, "result_id": "trs_a1b2c3d4" }
```

### POST /api/{result_id}/insert/text

```json
{ "text": "..." }
```

长文本自动截断，完整内容存 full_texts，可用 GET /full 获取。

### POST /api/{result_id}/insert/image

```json
{ "url": "/api/files/images/agent-1/xxx.png" }
// 或 base64
{ "data": "base64...", "mimeType": "image/png" }
```

### POST /api/{result_id}/insert/resource

```json
{ "url": "/api/files/apk/agent-1/app.apk" }
// 或 base64
{ "data": "base64...", "mimeType": "application/vnd.android.package-archive" }
```

### GET /api/{result_id}/for-llm?provider=openai|anthropic

返回 LLM 可直接使用的 content，图片 URL 已解析为 base64。

### GET /api/{result_id}/preview?max_text_len=500

返回摘要与元数据，用于前端预览。

### GET /api/{result_id}/full

返回完整内容，长文本项由存储的 full_texts 还原。

### POST /api/resolve

```json
{ "url": "/api/files/images/agent-1/xxx.png" }
→ { "success": true, "data": "base64..." }
```
