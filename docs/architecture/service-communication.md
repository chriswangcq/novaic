# 服务间通信模式

本文档描述 Novaic 平台各服务之间的通信模式、调用关系、消息传递范式，以及端口分配与服务发现机制。

## 通信模式总览

平台内服务间通信采用三种核心模式：

| 模式 | 协议 | 特点 | 典型场景 |
|------|------|------|---------|
| 请求-响应 | HTTP REST | 同步、无状态、最普遍 | 大部分服务间调用 |
| 订阅-通知 | WebSocket | 双向、持久连接、实时推送 | Entangled 同步、设备控制 |
| 命令-派发 | 进程 spawn / WS typed cmd | 单向派发、异步执行 | Worker 调度、VmControl 指令 |

```
通信模式分布：HTTP REST ~60% ｜ WebSocket ~30% ｜ 进程 Spawn / Typed Cmd ~10%
```

## HTTP 调用关系

### 调用图

```
┌─────────┐
│ Gateway │─────────┬──────────────┬──────────────┬──────────────┐
│ :19999  │         │              │              │              │
└─────────┘         ▼              ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
              │ Business │  │  Cortex  │  │   Blob   │  │  Device  │
              │  :19998  │  │  :19996  │  │  :19995  │  │  :19993  │
              └────┬─────┘  └──────────┘  └──────────┘  └──────────┘
                   │
          ┌────────┼──────────────┐
          ▼        ▼              ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  Queue   │ │  Device  │ │Entangled │
    │  Service │ │  :19993  │ │  :19900  │
    │  :19997  │ └──────────┘ └──────────┘
    └────┬─────┘
         │ spawn
    ┌────▼──────┐
    │  Agent    │──────┬──────────────┬──────────────┬──────────────┐
    │  Runtime  │      │              │              │              │
    └───────────┘      ▼              ▼              ▼              ▼
                 ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
                 │  Cortex  │  │  Device  │  │   LLM    │  │ Sandbox  │
                 │  :19996  │  │  :19993  │  │ Factory  │  │ Service  │
                 └──────────┘  └──────────┘  │ :19990   │  └──────────┘
                                             └──────────┘
```

### 各服务出站调用明细

| 调用方 | 目标服务 | 协议 | 用途 |
|--------|---------|------|------|
| Gateway | Business :19998 | HTTP | 业务逻辑代理（消息、Agent 管理） |
| Gateway | Cortex :19996 | HTTP | 上下文查询代理 |
| Gateway | Blob Service :19995 | HTTP | 文件上传/下载代理 |
| Gateway | Device :19993 | HTTP | 设备管理代理（WebRTC 信令等） |
| Business | Queue Service :19997 | HTTP | 任务创建与状态查询 |
| Business | Device :19993 | HTTP | 设备状态查询 |
| Business | Entangled :19900 | HTTP | 实体写入（触发同步） |
| Agent Runtime | Cortex :19996 | HTTP | 上下文读写（ContextEvent） |
| Agent Runtime | Device :19993 | HTTP | 工具执行（shell、截图、输入） |
| Agent Runtime | LLM Factory :19990 | HTTP | LLM 推理调用 |
| Agent Runtime | Sandbox Service | HTTP | 沙箱内代码/命令执行 |

### HTTP 客户端实现

所有 Python 服务通过 `novaic-common` 提供的统一 HTTP 客户端发起调用：

- 基于 `httpx.AsyncClient`，支持异步调用
- 内置连接池、超时配置、重试策略
- 自动携带 HS256 内部 JWT
- 统一的错误处理和日志记录

## WebSocket 通道

### 活跃 WS 连接

| 通道 | 端点 | 方向 | 用途 |
|------|------|------|------|
| AppBridge | Gateway :19999 `/ws/bridge` | App ↔ Gateway | 实时事件推送（Agent 状态、通知） |
| Entangled Sync | Entangled :19900 `/ws/sync` | App ↔ Entangled | 实体数据双向同步 |
| Cloud Bridge | Device :19993 `/ws/device` | Device ↔ VmControl | 设备控制指令双向传输 |

### AppBridge WS

App ↔ Gateway :19999 `/ws/bridge`，握手时携带 Clerk JWT。推送事件类型：`agent_status_changed`、`task_progress`、`auth_rejected`、`notification`。断线时客户端自动重连。

### Device ↔ VmControl (Cloud Bridge)

Device Service ↔ VmControl (Rust) `/ws/device`，使用 typed command 协议（`type` + `payload`）。支持请求-响应和单向通知两种模式。命令类型包括 StartDevice/StopDevice、ExecuteShell、TakeScreenshot、WebRTC 信令转发、DeviceStatus 心跳。断线时标记设备 offline。

## 消息传递模式

### 模式一：请求-响应（HTTP）

`Client → POST /api/xxx → Server → 200 JSON response`。最常见模式，超时默认 30s，重试由 novaic-common 统一管理。

### 模式二：订阅-通知（Entangled Sync）

`Client → Entangle(entity) → Server`（订阅），`Server → Sync(delta/full) → Client`（通知，可多次），`Client → Disentangle → Server`（取消）。

### 模式三：命令-派发（Worker / Device）

Queue Service spawn worker 进程；Device Service 通过 WS 发送 typed command 到 VmControl。调用方不阻塞，结果通过回调或 Entangled 同步获取。

## 端口与服务发现

### 端口分配表

服务名不随环境改名；`prod` 和 `staging` 都叫 `gateway`、`business`、`queue_service`。环境隔离来自 registry namespace、Compose project、数据目录、Postgres/Redis/OSS 前缀和 host 端口。

| prod 端口 | staging 端口 | 服务 | 说明 |
|-----------|--------------|------|------|
| 19999 | 29999 | Gateway | API 网关，外部流量入口 |
| 19998 | 29998 | Business | 核心业务逻辑 |
| 19997 | 29997 | Queue Service | 任务队列与 Worker 调度 |
| 19991 | 29991 | Service Registry | 中心化服务注册与发现 |
| 19996 | 29996 | Cortex | 上下文管理 |
| 19995 | 29995 | Blob Service | 大对象存储 |
| 19993 | 29993 | Device Service | 设备管理 |
| 19900 | 29900 | Entangled | 实时同步 |
| 19990 | 29990 | LLM Factory | LLM 推理网关 |

### 服务发现：registry-only runtime discovery

```json
{
  "gateway": {
    "url": "http://127.0.0.1:19999",
    "port": 19999,
    "health_path": "/api/health",
    "compose_service": "gateway",
    "dependencies": ["queue_service", "blob_service"]
  },
  "service_registry": {
    "url": "http://127.0.0.1:19991",
    "port": 19991,
    "health_path": "/ready",
    "compose_service": "service-registry",
    "dependencies": []
  },
  "llm_factory": {
    "url": "http://127.0.0.1:19990",
    "port": 19990,
    "health_path": "/health",
    "compose_service": "llm-factory",
    "dependencies": []
  }
}
```

- `services.json` 是服务 manifest/bootstrap 元数据，负责服务身份、预期端口、健康检查、Compose 名称、owner 和依赖关系；它不是运行时 fallback。
- `ServiceCatalog`（novaic-common）加载并验证这份 manifest，供配置校验、文档和 bootstrap 使用。
- `service-registry` 是运行在 API host Docker 中的中心化 HTTP 服务，prod 默认 `127.0.0.1:19991`，staging 默认 `127.0.0.1:29991`，Postgres 表为 `service_registry_instances`。
- Registry 主键是 `(namespace, service_name, instance_id)`；调用方发现依赖时必须带同一个 namespace，例如 staging `business` 只 discover `namespace=staging, service=queue_service`。
- `common.service_runtime` 负责进程启动前从 service-registry 解析同 namespace 依赖 URL，并在服务健康后注册自身、定时 heartbeat、退出时 deregister。
- `ServiceRegistry` / `RegistryOnlyResolver` 是运行时实例层；调用方只接受 fresh healthy registry 实例，registry 不可用或无实例时显式失败，不使用静态 URL 回退。
- 运行时密钥来自 `/opt/novaic/etc/<namespace>/secrets.json` 或本地 `secrets.local.json`，不写入 committed `services.json`。

### Nginx ingress 边界

Nginx 只做外部 ingress，不参与服务发现，也不决定内部依赖路由。

```nginx
server_name api.gradievo.com;
proxy_pass http://127.0.0.1:19999;

server_name staging-api.gradievo.com;
proxy_pass http://127.0.0.1:29999;
```

内部服务发现仍由 namespace registry 决定：prod 服务无法 discover staging 实例，staging 服务也无法 discover prod 实例。

### 连接拓扑总结

全平台共 16 条通信链路：HTTP 调用对 11 条、WebSocket 3 条（AppBridge / Entangled Sync / Cloud Bridge）、进程 Spawn 1 条（Queue → Worker）、WebRTC 1 条（VmControl → App 媒体流）。
