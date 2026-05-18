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
                 └──────────┘  └──────────┘  │  :9100   │  └──────────┘
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
| Agent Runtime | LLM Factory :9100 | HTTP | LLM 推理调用 |
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

| 端口 | 服务 | 说明 |
|------|------|------|
| 19999 | Gateway | API 网关，外部流量入口 |
| 19998 | Business | 核心业务逻辑 |
| 19997 | Queue Service | 任务队列与 Worker 调度 |
| 19996 | Cortex | 上下文管理 |
| 19995 | Blob Service | 大对象存储 |
| 19993 | Device Service | 设备管理 |
| 19900 | Entangled | 实时同步 |
| 9100 | LLM Factory | LLM 推理网关 |

### 服务发现：services.json

```json
{
  "gateway":       { "host": "localhost", "port": 19999 },
  "business":      { "host": "localhost", "port": 19998 },
  "queue_service": { "host": "localhost", "port": 19997 },
  "cortex":        { "host": "localhost", "port": 19996 },
  "blob_service":  { "host": "localhost", "port": 19995 },
  "device":        { "host": "localhost", "port": 19993 },
  "entangled":     { "host": "localhost", "port": 19900 },
  "llm_factory":   { "host": "localhost", "port": 9100  }
}
```

- 由 `ServiceConfig`（novaic-common）加载解析，启动时严格校验
- 所有服务引用目标地址均通过 `ServiceConfig` 获取，不硬编码端口
- 云端部署时 host 替换为内部 DNS 名称，端口保持不变

### 连接拓扑总结

全平台共 16 条通信链路：HTTP 调用对 11 条、WebSocket 3 条（AppBridge / Entangled Sync / Cloud Bridge）、进程 Spawn 1 条（Queue → Worker）、WebRTC 1 条（VmControl → App 媒体流）。
