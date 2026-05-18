# 系统总览

## 系统简介

Novaic 是一个 AI Agent 平台，提供 Agent 创建、设备绑定、远程桌面控制、自动化执行等能力。用户通过桌面/移动客户端与 Agent 交互，Agent 通过 LLM 推理和工具调用在绑定的设备上执行任务。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端服务 | Python 3.x + FastAPI + uvicorn |
| 数据存储 | SQLite（各服务本地）、Redis（Cortex scope lock） |
| 客户端 | Tauri 2.x（Rust）+ React 18 + TypeScript |
| 设备控制 | Rust（VmControl）、WebRTC、Scrcpy 3.3.4 |
| VM 内工具 | Python + aiohttp + xdotool + Playwright |
| 通信协议 | HTTP/REST、WebSocket、Entangled Sync Protocol |
| 认证 | JWT（Clerk RS256 外部 + HS256 内部） |
| 构建 | monorepo + git submodules |

## 服务拓扑

```
                        ┌──────────────────────────────────────────────┐
                        │              Cloud / Server Side             │
                        │                                              │
  ┌─────────┐    HTTP   │  ┌─────────┐    HTTP    ┌──────────┐        │
  │         │◄─────────►│  │ Gateway │◄──────────►│ Business │        │
  │  novaic │    WS     │  │ :19999  │            │ :19998   │        │
  │   app   │◄─────────►│  └────┬────┘            └────┬─────┘        │
  │ (Tauri) │           │       │                      │              │
  │         │◄────WS───►│  ┌────┴──────────┐     ┌────┴─────┐        │
  └────┬────┘  Entangled│  │   Entangled   │     │  Queue   │        │
       │       Sync     │  │   :19900      │     │  Service │        │
       │                │  └───────────────┘     │  :19997  │        │
       │                │                        └────┬─────┘        │
       │                │  ┌──────────┐          ┌────┴─────┐        │
       │                │  │  Cortex  │◄────────►│  Agent   │        │
       │                │  │  :19996  │          │ Runtime  │        │
       │                │  └──────────┘          └────┬─────┘        │
       │                │                             │              │
       │                │  ┌──────────┐  ┌─────────┐  │  ┌─────────┐ │
       │                │  │  Device  │  │  Blob   │  │  │   LLM   │ │
       │                │  │  :19993  │  │ Service │  │  │ Factory │ │
       │                │  └────┬─────┘  │ :19995  │  │  │  :9100  │ │
       │                │       │        └─────────┘  │  └─────────┘ │
       │                └───────┼─────────────────────┼──────────────┘
       │                        │                     │
       │                   WS   │                     │ HTTP
       │                        ▼                     ▼
  ┌────┴────┐           ┌────────────┐        ┌────────────┐
  │VmControl│◄─────────►│  VmControl │        │  Sandbox   │
  │(嵌入式) │  oneshot   │  (远程PC)  │        │  Service   │
  └────┬────┘           └────────────┘        │  :19994    │
       │                                      └──────┬─────┘
       │ WebRTC/Scrcpy/VNC                           │
       ▼                                             ▼
  ┌──────────┐                                ┌────────────┐
  │ Linux VM │                                │  MCP-VMUSE │
  │ Android  │                                │  (VM 内部) │
  │ Desktop  │                                │   :8080    │
  └──────────┘                                └────────────┘
```

## 端口清单

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Gateway | 19999 | HTTP + WS | API 网关、WebSocket 信令、Blob 代理 |
| Business | 19998 | HTTP | 实体管理、Action Hooks |
| Queue Service | 19997 | HTTP | 任务队列、Worker 调度 |
| Cortex | 19996 | HTTP | 上下文管理、ContextEvent |
| Blob Service | 19995 | HTTP | 对象存储（blob:// + object tree） |
| Sandbox Service | 19994 | HTTP | 进程隔离执行 |
| Device | 19993 | HTTP + WS | 设备管理、typed command 协议 |
| VMControl | 19992 | HTTP | 独立模式（嵌入式无端口） |
| Entangled | 19900 | HTTP + WS | 实体同步服务 |
| LLM Factory | 9100 | HTTP | LLM Provider 路由 |
| MCP-VMUSE | 8080 | HTTP | VM 内桌面控制（VM 内部端口） |

## 子模块一览

| 子模块 | 类型 | 语言 | 职责 |
|--------|------|------|------|
| novaic-agent-runtime | 服务 | Python | Agent 执行引擎 + Queue Service（Worker 调度、Saga/Task 处理） |
| novaic-cortex | 服务 | Python | 上下文管理（Scope Lock、ContextEvent、Token 压缩） |
| novaic-business | 服务 | Python | 实体管理（Entity Schema、Action Hooks、DispatchSubscriber） |
| novaic-gateway | 服务 | Python | API 网关（双 JWT 认证、WebSocket 信令、Blob 代理） |
| novaic-device | 服务 | Python | 设备管理（typed command WS、3 设备类型、mounted tools） |
| novaic-llm-factory | 服务 | Python | LLM Provider 路由（OpenAI/Anthropic/Google、API Key 加密） |
| novaic-sandbox-service | 服务 | Python | 进程隔离执行（AsyncProcessRunner、mount namespace） |
| novaic-blob-service | 服务 | Python | 对象存储（blob:// 原始 + object tree 结构化、双后端） |
| novaic-app | 客户端 | Rust + TS | 桌面/移动客户端（Tauri 2.x + React 18、Entangled 同步引擎） |
| novaic-common | 库 | Python | 共享库（ServiceConfig、HTTP 客户端、9 contract 模块、5 LLM 工具） |
| novaic-logicalfs | 库 | Python | 文件系统抽象（Snapshot/Authority/Store） |
| novaic-mcp-vmuse | 工具 | Python | VM 内桌面控制（6 类工具、40+ HTTP API 端点） |

## 数据流概览

### Agent 执行链路

```
用户消息 → App → Gateway → Business(action hook) → Queue Service → Agent Runtime(worker)
         → LLM Factory(推理) → Cortex(上下文) → Device/Sandbox(工具执行) → 结果回传
```

### 实体同步

```
App(React) → Tauri IPC → EntangledSyncBridge(Rust) → WS → Entangled 服务
           → sync 帧 → SQLite 缓存 → entities_changed 事件 → React Query invalidation
```

### 设备控制

```
Agent Runtime → Device Service → Cloud Bridge WS → VmControl(宿主机)
             → QEMU/Scrcpy/enigo → 设备(Linux VM/Android/Desktop)
             → WebRTC → App(前端显示)
```
