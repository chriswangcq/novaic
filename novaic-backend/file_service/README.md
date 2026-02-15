# NovaIC File Service

独立文件管理服务，负责文件存储、URL 生成、内部 resolve（URL → base64/path）。

## 快速启动

```bash
# 通过 backend 统一入口（推荐，端口 19995）
novaic-backend file-service --port 19995 --data-dir /path/to/data
# 或 python -m main_novaic file-service --port 19995

# 独立运行
python -m file_service.main --port 19995 --base-dir /path/to/data
```

## HTTP API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/files/upload` | 上传文件 (multipart)，需 agent_id，可选 category、subagent_id |
| POST | `/api/files/from-base64` | 提交 base64，需 agent_id、data，可选 mime_type、category |
| GET | `/api/files/info?url=xxx` | 文件元信息 |
| GET | `/api/files/{path}` | 下载文件 |
| DELETE | `/api/files/{path}` | 删除文件 |

## Python Client（内部使用）

```python
from file_service import create_client

client = create_client(base_dir="/path/to/files")

# 存 base64 得 URL
url = client.save_from_base64(b64_data, "images", "agent-1", mime_type="image/png")

# URL → base64（供 LLM 等调用点）
b64 = client.resolve_to_base64(url)

# URL → 本地路径（供 adb install 等）
path = client.get_local_path_str(url)
```

## 目录结构

```
{base_dir}/files/
  ├── images/{agent_id}/...
  ├── apk/{agent_id}/...
  ├── audio/{agent_id}/...
  ├── video/{agent_id}/...
  ├── documents/{agent_id}/...
  └── binaries/{agent_id}/...
```
