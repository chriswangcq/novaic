# 部署与进程启动

> 源码：`novaic_cortex/main_cortex.py`；应用对象来自 `api.app`（`set_registry` / `set_internal_key`）。

## 1. 如何启动

```bash
python -m novaic_cortex.main_cortex \
  --blob-service-url http://127.0.0.1:19995 \
  --sandboxd-url http://127.0.0.1:19994 \
  --cortex-api-url http://127.0.0.1:19996 \
  --operational-sqlite-path /path/to/cortex/operational.sqlite3 \
  --redis-url redis://127.0.0.1:6379/0
```

生产由根目录 `scripts/start.sh` 启动。Cortex 需要：

- `--blob-service-url`：Blob Service base URL。
- `--sandboxd-url`：Sandbox Service base URL，shell 执行必须经过 sandboxd。
- `--cortex-api-url`：注入到 shell capability 的 Cortex base URL；必须显式传入，不能从默认 localhost 或临时文件兜底。
- `--operational-sqlite-path`：Cortex operational state / projection SQLite 路径，由启动配置显式传入。
- `--redis-url`：scope lock 后端。
- `--internal-key`：内部 API 鉴权 key。
- `--jwt-secret`：Capability token secret。

## 2. 启动装配做什么

1. 安装 Redis scope lock backend；失败则拒绝启动。
2. 创建 `WorkspaceRegistry(blob_service_url, operational_store=...)`。
3. 调用 `set_registry(...)` 和 `set_internal_key(...)`。

Cortex 不读取 OSS/S3 凭证，不创建 OSS/S3 client，不知道 bucket/endpoint。物理存储后端属于 Blob Service。

## 3. Blob Service 物理后端

Blob Service 由 `scripts/start.sh` 设置：

```bash
NOVAIC_BLOB_BACKEND=oss
NOVAIC_OSS_ACCESS_KEY=...
NOVAIC_OSS_SECRET_KEY=...
NOVAIC_OSS_ENDPOINT=...
NOVAIC_OSS_BUCKET=...
```

Blob Service 也可在本地测试中使用 Disk backend，但生产的 object/byte 后端统一在 Blob Service 层配置。

## 4. 与专题文档的衔接

- 对象键前缀：[object-keys.md](object-keys.md)
- HTTP 路由：[http-api.md](http-api.md)
