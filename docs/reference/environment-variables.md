# 环境变量参考

## 全局环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NOVAIC_ENV` | 运行环境（development/production） | development |
| `NOVAIC_DATA_DIR` | 数据目录 | `/opt/novaic/data` |
| `NOVAIC_LOG_LEVEL` | 日志级别 | INFO |

## Gateway

| 变量 | 说明 |
|------|------|
| `JWT_SECRET` | 内部 HS256 JWT 签名密钥 |
| `CLERK_PUBLISHABLE_KEY` | Clerk 公钥（RS256 外部认证） |
| `CLERK_SECRET_KEY` | Clerk 密钥 |
| `GATEWAY_HOST` | 监听地址（默认 127.0.0.1） |
| `GATEWAY_PORT` | 监听端口（默认 19999） |

## Business

| 变量 | 说明 |
|------|------|
| `BUSINESS_HOST` | 监听地址 |
| `BUSINESS_PORT` | 监听端口（默认 19998） |

## Agent Runtime / Queue Service

| 变量 | 说明 |
|------|------|
| `QUEUE_SERVICE_HOST` | Queue Service 监听地址 |
| `QUEUE_SERVICE_PORT` | Queue Service 端口（默认 19997） |
| `health_check_interval_seconds` | 健康检查间隔（runtime switch） |
| `scheduler_poll_interval_seconds` | 调度器轮询间隔（runtime switch） |

## Cortex

| 变量 | 说明 |
|------|------|
| `CORTEX_HOST` | 监听地址 |
| `CORTEX_PORT` | 监听端口（默认 19996） |
| `REDIS_URL` | Redis 连接 URL（scope lock） |

## Blob Service

| 变量 | 说明 |
|------|------|
| `BLOB_SERVICE_HOST` | 监听地址 |
| `BLOB_SERVICE_PORT` | 监听端口（默认 19995） |
| `BLOB_STORAGE_BACKEND` | 存储后端（disk / oss） |
| `BLOB_DISK_ROOT` | 磁盘后端根目录 |
| `OSS_ACCESS_KEY_ID` | 阿里云 OSS Access Key |
| `OSS_ACCESS_KEY_SECRET` | 阿里云 OSS Secret |
| `OSS_BUCKET` | OSS Bucket 名 |
| `OSS_ENDPOINT` | OSS Endpoint |

## Sandbox Service

| 变量 | 说明 |
|------|------|
| `SANDBOX_HOST` | 监听地址 |
| `SANDBOX_PORT` | 监听端口（默认 19994） |

## Device

| 变量 | 说明 |
|------|------|
| `DEVICE_HOST` | 监听地址 |
| `DEVICE_PORT` | 监听端口（默认 19993） |

## LLM Factory

| 变量 | 说明 |
|------|------|
| `LLM_FACTORY_HOST` | 监听地址 |
| `LLM_FACTORY_PORT` | 监听端口（默认 9100） |
| `RSA_PRIVATE_KEY` | API Key 解密私钥（RSA-2048） |

## VmControl

| 变量 | 说明 |
|------|------|
| `VMCONTROL_PORT` | 独立模式端口（默认 19992） |
| `TURN_SECRET` | TURN 服务器凭证密钥 |

## MCP-VMUSE

| 变量 | 前缀 `NOVAIC_` | 说明 |
|------|----------------|------|
| `NOVAIC_HOST` | 是 | 监听地址（默认 0.0.0.0） |
| `NOVAIC_PORT` | 是 | 监听端口（默认 8080） |
| `NOVAIC_WORK_DIR` | 是 | 工作目录（默认 /tmp/novaic-work） |
| `NOVAIC_BROWSER_HEADLESS` | 是 | 浏览器无头模式（默认 False） |
| `NOVAIC_BROWSER_TIMEOUT` | 是 | 浏览器超时（默认 30000ms） |

## novaic-app (Tauri)

客户端配置通过 Tauri 命令 `set_gateway_url` 设置 Gateway URL，持久化到本地存储。不使用环境变量。

## 注意事项

部分历史变量已在代码中废弃并由 CI guard 检测禁止使用。如需查看废弃变量清单，参见 `scripts/ci/check_start_config_contract.py`。
