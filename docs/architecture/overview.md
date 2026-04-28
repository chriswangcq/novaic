# NovAIC 架构概览（L1）

本文档描述**父仓库视角**的系统拓扑：各模块的职责、典型数据流与**可验证**的本地端口约定。细节以各子模块源码与 `HANDOVER.md` 为准。

## 1. 仓库与边界

- **父仓库**：聚合脚本（`scripts/`）、共享配置（`novaic-common`）、顶层文档（`docs/`）。
- **实现代码**：在 **submodule** 或同级目录内；改行为时请进入对应目录并以其 README 为准。
- **`.gitmodules`**：权威 submodule 清单；初始化：`git submodule update --init --recursive`。

## 2. 逻辑拓扑与数据流

```text
                           ┌─────────────────┐
                           │   LLM Factory   │ (独立 API 代理: 19990)
                           └────────▲────────┘
                                    │ HTTP
┌────────────────┐ WebRTC  ┌────────┴────────┐ HTTP ┌────────────────┐
│ Relay / STUN   │◄───────►│  Agent Runtime  ├─────►│     Cortex     │
│ (quic-service) │ 信令穿透 │ (Watchdog/Worker)│      │  (:19996 HTTP) │
└───────┬────────┘         └────────┬────────┘      │ - Scope / DFS  │
        │                           │ 读写实体/队列  │ - Sandbox      │
        │                           │                └────────────────┘
 ┌──────▼───────┐          ┌────────▼───────────────────────────────────────┐
 │  novaic-app  │  WS/REST │           Nginx (公网入口 :443)                 │
 │  (Tauri 壳)  │◄────────►│  /         → Gateway  (:19999)                │
 │ - VmControl  │          │  /device/  → Device   (:19993)                │
 │ - Entangled  │          │  /business → Business (:19998)                 │
 │   Rust Client│          └────┬───────────┬──────────┬───────────────────┘
 └──────┬───────┘               │           │          │
        ▼               ┌───────▼──┐ ┌──────▼───┐ ┌───▼──────────┐
    本地 SQLite          │ Gateway  │ │ Business │ │   Device     │
 (entangled_cache.db)   │ Auth+WS  │ │ Agent/   │ │ VM/PC-Bridge │
                        │ Turn+File│ │ Skill/   │ │ WS + CRUD    │
                        └────┬─────┘ │ Model    │ └──────┬───────┘
                             │       └────┬─────┘        │
                             │  /internal/entities/*      │
                      ┌──────▼────────────▼──────────────▼──────┐
                      │          Business (:19998)               │
                      │   中枢编排 + Entity CRUD Proxy            │
                      └───────────────────┬─────────────────────┘
                                          │ HTTP (sole consumer)
                      ┌───────────────────▼─────────────────────┐
                      │          Entangled (:19900)              │
                      │    独立进程 HTTP+WS — 实体 CRUD + 同步      │
                      │          (server SQLite)                 │
                      └─────────────────────────────────────────┘
```

- **客户端（本地）**：`novaic-app`（React + Tauri）。内嵌 **VmControl** 作为唯一 runtime owner 处理所有 WebRTC 连接、VM 生命周期、输入控制与截图；内嵌 **Entangled Rust Client** 处理业务实体的实时订阅，数据持久化在**本地 SQLite**（不再依赖 IndexedDB）。
- **云端网关**：`novaic-gateway`（`:19999`）。瘦网关：Auth（JWT 签发/验证）、File Proxy（文件代理）、App WS（实时推送 + WebRTC signaling）。不包含任何业务逻辑或设备调用。
- **业务服务**：`novaic-business`（`:19998`）。**中枢编排层**：所有 Entangled 实体的 action hook 回调（包括 devices）、所有 `/internal/*` API（被 Workers 和 Cortex 直接调用）、Device 生命周期编排（通过 device_client → Device Service）。Cortex 的 BusinessProxy 直接指向此服务。
- **设备服务**：`novaic-device`（`:19993`）。纯硬件基础设施：Device registry、CloudBridge typed WS broker、`/internal/hardware/*` 执行 API、VM/Mobile/HD tool proxy（转发到 VmControl）。不含业务逻辑，不拥有 action hook。所有业务调度由 Business Service 发起。
- **实体同步**：`Entangled`（`:19900`）。独立的实体存储与实时同步引擎。**仅 Business Service 直接访问 Entangled HTTP**；Gateway、Device、Workers 均通过 Business `/internal/entities/*` 代理完成 entity CRUD。前端可选直连 `ws(s)://…/v1/sync`。
- **异步执行管线**：`novaic-agent-runtime`。包含 Watchdog 和 Task/Saga Workers，并内置工具分发逻辑。
- **认知基础设施**：`novaic-cortex`。独立 HTTP 服务。Agent 运行时通过 `CortexBridge` 调用 scope 生命周期、Workspace/DFS 与 LLM context 拼装。当前主路径没有独立 Recall 模块或 wake-summary 通道；跨 wake 连续性来自 agent-root scope 树中的折叠 `summary.md`。Cortex 只保留 `chat`、设备/VM、subagent 的遗留 BusinessProxy 入口；`memory`、`notebook`、`task`、`search` 不再属于 Cortex 代理面。
- **LLM 隔离层**：`novaic-llm-factory`。隐藏所有 api-keys 和底层厂商差异，只暴露标准 OpenAI HTTP 端点。
- **边缘 P2P 与存储**：`novaic-quic-service` 负责 WebRTC 打洞和热更新 CDN；`novaic-storage-a` 负责二进制文件上传。

## 3. 典型本地端口约定

由于采用云端/本地分离的架构，这里分为 **云端后端服务** 与 **本地客户端端侧服务**。注意 `19996` 端口存在历史复用。

**Backend（云端后端逻辑）**：
| 服务名                 | 端口    | 说明                                                               |
| --------------------- | ----- | ---------------------------------------------------------------- |
| `entangled`           | 19900 | Entangled 实体同步引擎（HTTP + WS）                                     |
| `gateway`             | 19999 | Gateway 网关（Auth/Turn/File Proxy/App WS）                          |
| `business`            | 19998 | Business Service — 中枢编排层（Agent/Skill/Device/Model 业务逻辑 + 所有 action hooks） |
| `device`              | 19993 | Device Service（设备 registry / CloudBridge typed WS broker / VmControl 命令路由）|
| `queue_service`       | 19997 | Queue Service（novaic-agent-runtime `queue-service`）                 |
| `cortex`              | 19996 | Cortex 认知引擎 HTTP (`novaic-cortex`)，提供 Workspace / Scope / DFS context / Sandbox |
| `file_service`        | 19995 | 文件服务（novaic-storage-a）                                          |

**App / Client（客户端端侧逻辑）**：
| 服务名                 | 端口    | 说明                                                               |
| --------------------- | ----- | ---------------------------------------------------------------- |
| `vmcontrol`           | 19996 | **这是给 App 用的**：嵌入在 Tauri 内的本地 VmControl HTTP 及 WebRTC 引擎，仅在用户个人 Mac 上运行。 |

> **端口冲突避雷**：`19996` 这个数字，在用户 macOS 上是被 `vmcontrol` 占据的；而在后端的云服务器上，是被 `cortex` 占据的。它们处于完全不交叉的两端网络，设计上合理。只有当你**完全在本地同一台机器**上同时把全栈服务（既跑 Tauri UI 又强行跑所有的云端 Backend）都起起来时，才会发生 :19996 冲突。此时建议用环境变量 `CORTEX_PORT=19990` 把你的本地 Cortex 移开。

## 4. 模块速查

实际 submodule 以 `.gitmodules` 为准。

| 目录                     | submodule | 角色                                                             |
| ---------------------- | --------- | -------------------------------------------------------------- |
| `novaic-app`           | ✅         | 客户端 UI（React/Vite + Tauri）、VmControl 嵌入                       |
| `novaic-gateway`       | ✅         | API 网关（Auth/Turn/File Proxy/App WS），瘦身后不含业务逻辑               |
| `novaic-business`      | ✅         | Business Service：中枢编排层 — Agent/Skill/Device/Model/消息等（:19998）   |
| `novaic-device`        | ✅         | Device Service：设备 registry / CloudBridge typed WS broker（:19993）   |
| `novaic-agent-runtime` | ✅         | Agent 运行时：Queue Service、Task/Saga Worker、Watchdog、Scheduler    |
| `novaic-cortex`        | ✅         | Cortex HTTP：Workspace / Scope / DFS context / Sandbox          |
| `novaic-storage-a`     | ✅         | 文件存储服务                                                         |
| `novaic-quic-service`  | ✅         | STUN / Relay / 静态资源 CDN                                        |
| `novaic-common`        | ✅         | 共享配置与工具（含 `config/services.json`）                              |
| `novaic-mcp-vmuse`     | ✅         | MCP VMuse（VM 浏览器自动化）                                           |
| `Entangled`            | ✅         | 实时同步引擎（协议 + SQL 存储 + 独立服务壳）                                   |
| `byclaw-website`       | ✅         | 官网                                                             |
| `thirdparty/openclaw`  | ✅         | 上游参考（非线上服务）                                                    |
| `novaic-llm-factory`   | ❌ 独立 repo | 集中化 LLM 代理（运维与 URL 见 `HANDOVER.md`）                           |

## 5. 文档地图

| 主题 | 文档 |
|------|------|
| OTA、拓扑、TURN | [thin-client-and-topology.md](thin-client-and-topology.md) |
| JWT | [authentication.md](authentication.md) |
| WebRTC | [webrtc.md](webrtc.md) |
| Push、App WS（摘要） | [realtime-sync.md](realtime-sync.md) |
| Entangled Store、schema push | [entangled-store-and-app-ws.md](entangled-store-and-app-ws.md) |
| 数据归属 v63 | [data-ownership.md](data-ownership.md) |
| 后端管线、源码表 | [agent-pipeline.md](agent-pipeline.md) |
| Cortex（纲要） | [cortex.md](cortex.md) |
| Cortex（详细，源码级） | [../cortex-architecture.md](../cortex-architecture.md) |
| Cortex（Scope/DFS 拆页） | [../cortex/README.md](../cortex/README.md) |
| 前端 Path C | [app-ui.md](app-ui.md) |
| 子模块 | [../reference/submodules.md](../reference/submodules.md) |
| 配置与环境 | [../reference/config-and-environment.md](../reference/config-and-environment.md) |
| 文件与语音 | [../reference/file-service.md](../reference/file-service.md) |
| 技术债、Model 方案 | [../roadmap/technical-debt.md](../roadmap/technical-debt.md)、[../roadmap/model-entity-refactor.md](../roadmap/model-entity-refactor.md) |

**Runbooks**：[local-dev.md](../runbooks/local-dev.md) · [local-backends.md](../runbooks/local-backends.md) · [deploy.md](../runbooks/deploy.md) · [build-and-release.md](../runbooks/build-and-release.md) · [cloud-production.md](../runbooks/cloud-production.md) · [troubleshooting.md](../runbooks/troubleshooting.md)

根目录 **HANDOVER.md** 保留变更史；旧路径见 [historical-doc-links.md](../historical-doc-links.md)。**novaic-app/FRONTEND_ARCHITECTURE.md** — 前端分层详解。
