# 端口清单与配置参考

## 端口清单

prod 使用 `199xx`，staging 使用 `299xx`。服务名保持不变，环境隔离由 `NOVAIC_NAMESPACE`、Compose project、数据目录、Postgres/Redis/OSS 前缀和 Service Registry namespace 完成。

| 服务 | prod 端口 | staging 端口 | 协议 | 进程 | 说明 |
|------|----------|--------------|------|------|------|
| Gateway | 19999 | 29999 | HTTP + WS | Python/FastAPI | API 网关、WebSocket 信令、Blob 代理 |
| Business | 19998 | 29998 | HTTP | Python/FastAPI | 实体管理（API 进程 + Subscriber 进程） |
| Queue Service | 19997 | 29997 | HTTP | Python/FastAPI | 任务队列、Worker 调度、Postgres 持久化 |
| Service Registry | 19991 | 29991 | HTTP | Python/FastAPI/Docker | 中心化服务注册与发现 |
| Cortex | 19996 | 29996 | HTTP | Python/FastAPI | 上下文管理、Redis scope lock |
| Blob Service | 19995 | 29995 | HTTP | Python/FastAPI | 对象存储（Disk + OSS 后端） |
| Sandbox Service | 19994 | 29994 | HTTP | Python/FastAPI | 进程隔离执行、mount namespace |
| Device | 19993 | 29993 | HTTP + WS | Python/FastAPI | 设备管理、typed command WS 协议 |
| VMControl | 19992 | — | HTTP | Rust/axum | 独立模式；嵌入式模式无端口 |
| Entangled | 19900 | 29900 | HTTP + WS | — | 实体同步服务 |
| LLM Factory | 19990 | 29990 | HTTP | Python/FastAPI/Docker | LLM Provider 路由（API host Docker） |
| MCP-VMUSE | 8080 | — | HTTP | Python/aiohttp | VM 内桌面控制（VM 内部端口） |
| 前端 Dev Server | 5173 | — | HTTP | Vite | 本地开发前端热加载 |
| Tauri Dev | 1420 | — | HTTP | Tauri | Tauri 开发模式 |

## services.json 配置

所有后端服务的 manifest/bootstrap 元数据由 `novaic-common/config/services.json` 统一管理。它声明服务身份、预期本机端口、健康检查路径、Compose 名称、owner 和依赖关系；它不是运行时服务发现 fallback。

### 配置文件位置

- 开发环境：`novaic-common/config/services.json`
- 生产环境：API backend 镜像内的 `novaic-common/config/services.json`，运行时密钥由 `/opt/novaic/etc/<namespace>/secrets.json`、`/opt/novaic/docker/api-backend.<namespace>.env` 与 `/opt/novaic/postgres/secrets/<namespace>/` 注入
- 本地密钥 overlay：`novaic-common/config/secrets.local.json`（已 gitignore）或测试用 `NOVAIC_SECRETS_PATH`

### 配置结构

```json
{
  "gateway": {
    "url": "http://127.0.0.1:19999",
    "protocol": "http",
    "port": 19999,
    "health_path": "/api/health",
    "compose_service": "gateway",
    "owner": "novaic-gateway",
    "dependencies": ["queue_service", "blob_service"]
  },
  "service_registry": {
    "url": "http://127.0.0.1:19991",
    "protocol": "http",
    "port": 19991,
    "health_path": "/ready",
    "compose_service": "service-registry",
    "owner": "novaic-common",
    "dependencies": []
  },
  "llm_factory": {
    "url": "http://127.0.0.1:19990",
    "protocol": "http",
    "port": 19990,
    "health_path": "/health",
    "compose_service": "llm-factory",
    "owner": "novaic-llm-factory",
    "dependencies": []
  }
}
```

### ServiceConfig 加载机制

`novaic-common` 中的 `strict_config` 和 `ServiceCatalog` 会严格验证 `services.json`：

- 启动时加载并验证所有必需字段
- 缺少必需服务 URL 时启动失败
- 提供类型化的 URL、host、port、health path、Compose 服务名、owner、dependencies 访问方法
- `ServiceConfig` 保留 bootstrap/manifest 常量；服务间运行时调用必须通过 `service-registry` 和 `RegistryOnlyResolver`/`common.service_runtime` 获得 fresh healthy 实例地址

### 密钥拆分

`services.json` 只声明密钥字段名，active committed defaults 必须保持空值。运行时密钥从明确的 overlay 文件加载：

```json
{
  "secrets": {
    "jwt_secret": "...",
    "cortex_internal_key": "...",
    "alibaba_cloud_access_key_id": "...",
    "alibaba_cloud_access_key_secret": "..."
  }
}
```

生产 namespace 路径为 `/opt/novaic/etc/<namespace>/secrets.json`。本地开发可复制 `novaic-common/config/secrets.example.json` 到 `novaic-common/config/secrets.local.json`，后者不会提交。

### 中心化 Service Registry

`service-registry` 是真正运行的中心化注册发现服务，prod 默认监听 `127.0.0.1:19991`，staging 默认监听 `127.0.0.1:29991`。它由 API backend Docker Compose 启动，使用 `/opt/novaic/postgres/secrets/<namespace>/novaic_registry_dsn` 连接 Postgres，并维护 `service_registry_instances` 表。

职责边界：

- `services.json`：服务身份、预期端口和依赖关系的 manifest/bootstrap 元数据。
- Service Registry HTTP 服务：registry-only runtime discovery，负责运行时实例注册、heartbeat、deregister、查询、TTL 过期和 stale 清理。
- `RegistryOnlyResolver` / `common.service_runtime`：客户端侧解析策略；所有注册/发现请求必须带 namespace，registry 不可用或无 fresh healthy 实例时显式失败，不做 runtime fallback。

### Namespace data plane

| 维度 | prod | staging |
|------|------|---------|
| Compose project | `novaic-prod` | `novaic-staging` |
| API env | `/opt/novaic/docker/api-backend.prod.env` | `/opt/novaic/docker/api-backend.staging.env` |
| API data dir | `/opt/novaic/data/prod` | `/opt/novaic/data/staging` |
| API secrets | `/opt/novaic/etc/prod/secrets.json` | `/opt/novaic/etc/staging/secrets.json` |
| Postgres DSN files | `/opt/novaic/postgres/secrets/prod/` | `/opt/novaic/postgres/secrets/staging/` |
| Redis URL | `redis://127.0.0.1:6379/0` | `redis://127.0.0.1:6379/1` |
| Factory env | `/opt/novaic/llm-factory/prod/compose.env` | `/opt/novaic/llm-factory/staging/compose.env` |

OSS 隔离必须由 bucket 或 prefix 完成，不能靠 `metadata.environment`。Registry 隔离只看 namespace 条件。

### Nginx ingress

Nginx 只做 ingress，不参与服务发现：

```nginx
server_name api.gradievo.com;
proxy_pass http://127.0.0.1:19999;

server_name staging-api.gradievo.com;
proxy_pass http://127.0.0.1:29999;
```

### Image promotion and rollback

Release Controller 在 main 分支更新时构建不可变镜像并部署 staging。prod 只通过 `/v1/promotions/prod` promotion 同一组 digest；rollback 只通过 `/v1/rollbacks/<namespace>` 切回 previous pointer。`deploy services-image` 和 `deploy factory-image` 是控制器内部执行器，人工直接调用会失败。回滚就是切回上一组已记录 digest，不在生产机重新 build。

## 生产部署路径

| 路径 | 说明 |
|------|------|
| `/opt/novaic/services/` | 服务代码目录 |
| `/opt/novaic/data/<namespace>/` | 数据目录（数据库、日志） |
| `/opt/novaic/data/logs/` | 日志目录 |
| `/opt/novaic/docker/api-backend/` | API backend Compose 主路径 |
| `/opt/novaic/llm-factory/` | LLM Factory Docker Compose 路径 |
| `/opt/novaic/postgres/secrets/<namespace>/novaic_registry_dsn` | Service Registry Postgres DSN |
| `/opt/novaic/start.sh` | emergency-only legacy rollback placeholder；Owner/removal gate 由 cleanup ledger 维护 |

## 相关文档

- [系统总览](../overview.md)
- [环境变量](environment-variables.md)
- [云端部署](../runbooks/deploy.md)
