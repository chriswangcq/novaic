# 端口清单与配置参考

## 端口清单

| 服务 | 默认端口 | 协议 | 进程 | 说明 |
|------|----------|------|------|------|
| Gateway | 19999 | HTTP + WS | Python/FastAPI | API 网关、WebSocket 信令、Blob 代理 |
| Business | 19998 | HTTP | Python/FastAPI | 实体管理（API 进程 + Subscriber 进程） |
| Queue Service | 19997 | HTTP | Python/FastAPI | 任务队列、Worker 调度、SQLite 持久化 |
| Cortex | 19996 | HTTP | Python/FastAPI | 上下文管理、Redis scope lock |
| Blob Service | 19995 | HTTP | Python/FastAPI | 对象存储（Disk + OSS 后端） |
| Sandbox Service | 19994 | HTTP | Python/FastAPI | 进程隔离执行、mount namespace |
| Device | 19993 | HTTP + WS | Python/FastAPI | 设备管理、typed command WS 协议 |
| VMControl | 19992 | HTTP | Rust/axum | 独立模式；嵌入式模式无端口 |
| Entangled | 19900 | HTTP + WS | — | 实体同步服务 |
| LLM Factory | 9100 | HTTP | Python/FastAPI | LLM Provider 路由（独立部署） |
| MCP-VMUSE | 8080 | HTTP | Python/aiohttp | VM 内桌面控制（VM 内部端口） |
| 前端 Dev Server | 5173 | HTTP | Vite | 本地开发前端热加载 |
| Tauri Dev | 1420 | HTTP | Tauri | Tauri 开发模式 |

## services.json 配置

所有后端服务的 URL 发现由 `novaic-common/config/services.json` 统一管理。

### 配置文件位置

- 开发环境：`novaic-common/config/services.json`
- 生产环境：`/opt/novaic/services/novaic-common/config/services.json`

### 配置结构

```json
{
  "gateway": {
    "url": "http://127.0.0.1:19999"
  },
  "business": {
    "url": "http://127.0.0.1:19998"
  },
  "queue_service": {
    "url": "http://127.0.0.1:19997"
  },
  "cortex": {
    "url": "http://127.0.0.1:19996"
  },
  "blob_service": {
    "url": "http://127.0.0.1:19995"
  },
  "sandbox_service": {
    "url": "http://127.0.0.1:19994"
  },
  "device": {
    "url": "http://127.0.0.1:19993"
  },
  "entangled": {
    "url": "http://127.0.0.1:19900"
  },
  "llm_factory": {
    "url": "http://127.0.0.1:9100"
  }
}
```

### ServiceConfig 加载机制

`novaic-common` 中的 `ServiceConfig` 类严格验证 `services.json`：

- 启动时加载并验证所有必需字段
- 缺少必需服务 URL 时启动失败
- 提供类型安全的 URL 访问方法
- 各服务通过 `ServiceConfig` 获取其他服务的地址

## 生产部署路径

| 路径 | 说明 |
|------|------|
| `/opt/novaic/services/` | 服务代码目录 |
| `/opt/novaic/data/` | 数据目录（数据库、日志） |
| `/opt/novaic/data/logs/` | 日志目录 |
| `/opt/novaic/start.sh` | 统一启动脚本 |

## 相关文档

- [系统总览](../overview.md)
- [环境变量](environment-variables.md)
- [云端部署](../runbooks/deploy.md)
