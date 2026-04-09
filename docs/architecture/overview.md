# NovAIC 架构概览（L1）

本文档描述**父仓库视角**的系统拓扑：各模块的职责、典型数据流与**可验证**的本地端口约定。细节以各子模块源码与 `HANDOVER.md` 为准。

## 1. 仓库与边界

- **父仓库**：聚合脚本（`scripts/`）、共享配置（`novaic-common`）、顶层文档（`docs/`）。
- **实现代码**：在 **submodule** 或同级目录内；改行为时请进入对应目录并以其 README 为准。
- **`.gitmodules`**：权威 submodule 清单；初始化：`git submodule update --init --recursive`。

## 2. 逻辑拓扑

```
                    ┌─────────────────┐
                    │  Relay / STUN   │  novaic-quic-service（P2P 兜底 + 静态资源 CDN）
                    └────────┬────────┘
                             │
  ┌──────────────┐    ┌──────▼──────┐    ┌──────────────────┐
  │  novaic-app  │◄──►│   Gateway   │◄──►│ Agent Runtime    │
  │  (Tauri UI)  │    │ (FastAPI)   │    │ (任务/Saga/工具)  │
  └──────┬───────┘    └──────┬──────┘    └────────┬─────────┘
         │                   │                    │
         │   ┌───────────────┤                    ▼
         │   │               │           ┌──────────────────┐
         │   ▼               └──────────►│ Cortex (HTTP)    │  认知/Scope/Sandbox
         │ Entangled                     └──────────────────┘
         │ (实时同步引擎)
         │   • entangled.server  协议层
         │   • entangled.sql     SQL 存储层
         │   • entangled.app     独立服务壳
         ▼
  本地 SQLite（Gateway 内嵌 Entangled 同步；客户端缓存）
```

- **桌面/移动端**：`novaic-app` — React/Vite + Tauri；经 CloudBridge / REST / WebSocket 与 Gateway 通信。
- **云端 API**：`novaic-gateway` — REST + WS 网关；实体层使用 `entangled.sql.SqlEntityStore`，业务扩展在 `gateway/entity/store.py`（serializer/deserializer 钩子）；生产环境前面有 Nginx。
- **Agent 执行**：`novaic-agent-runtime` — 任务队列（Queue Service :19997）、Saga、工具分发；与 Cortex 协作。
- **Cortex**：`novaic-cortex` — 独立 HTTP 服务（:19996），Agent 通过工具调用与之交互，不直连业务 UI。
- **Entangled**：实时实体同步引擎。三层架构：
  - `entangled.server` — 通用同步协议（不依赖存储）
  - `entangled.sql` — SQLite 存储层（FieldDef / EntityDef / EntityStore / Database / Locks）
  - `entangled.app` — 可选独立服务壳（FastAPI + WS + CRUD + Auth），可 `python -m entangled.app.main` 启动
- **P2P**：`novaic-quic-service` — STUN/TURN，配合 Gateway 与客户端 WebRTC。
- **共享库**：`novaic-common`（含统一 `config/services.json`）。

## 3. 典型本地端口（`novaic-common/config/services.json`）

以下为主机 `127.0.0.1` 上的**约定端口**（本地开发常用；若冲突请改环境变量或配置）。

| 服务键 (`services.json`) | 端口    | 说明                                                               |
| --------------------- | ----- | ---------------------------------------------------------------- |
| `gateway`             | 19999 | Gateway HTTP + WS（主入口，novaic-gateway）                           |
| `queue_service`       | 19997 | Queue Service（novaic-agent-runtime `queue-service` 子命令）          |
| `vmcontrol`           | 19996 | 本地 VmControl HTTP（Tauri 嵌入，`novaic-app/src-tauri/vmcontrol/`）  |
| `cortex`              | 19996 | Cortex HTTP (`novaic-cortex`)，开发时需避开与 vmcontrol 的端口冲突           |
| `file_service`        | 19995 | 文件服务（novaic-storage-a）                                          |
| `entangled_service`   | 19900 | Entangled 独立服务（`python -m entangled.app.main`，按需启动）              |

> **注意**：**Cortex** 在 `services.json` 中没有独立字段（依赖环境变量 `CORTEX_PORT`），默认端口 19996 与 `vmcontrol` 冲突。同一台机器上开发时需调整其一。

## 4. 模块速查

实际 submodule 以 `.gitmodules` 为准。

| 目录                     | submodule | 角色                                                             |
| ---------------------- | --------- | -------------------------------------------------------------- |
| `novaic-app`           | ✅         | 客户端 UI（React/Vite + Tauri）、VmControl 嵌入                       |
| `novaic-gateway`       | ✅         | API 网关、实体管理（基于 `entangled.sql`）、WS 同步                          |
| `novaic-agent-runtime` | ✅         | Agent 运行时：Queue Service、Task/Saga Worker、Watchdog、Scheduler    |
| `novaic-cortex`        | ✅         | Cortex HTTP：Workspace / Scope / Sandbox / Recall               |
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
| Cortex（Scope/DFS/Recall 拆页） | [../cortex/README.md](../cortex/README.md) |
| 前端 Path C | [app-ui.md](app-ui.md) |
| 子模块 | [../reference/submodules.md](../reference/submodules.md) |
| 配置与环境 | [../reference/config-and-environment.md](../reference/config-and-environment.md) |
| 文件与语音 | [../reference/file-service.md](../reference/file-service.md) |
| 技术债、Model 方案 | [../roadmap/technical-debt.md](../roadmap/technical-debt.md)、[../roadmap/model-entity-refactor.md](../roadmap/model-entity-refactor.md) |

**Runbooks**：[local-dev.md](../runbooks/local-dev.md) · [local-backends.md](../runbooks/local-backends.md) · [deploy.md](../runbooks/deploy.md) · [build-and-release.md](../runbooks/build-and-release.md) · [cloud-production.md](../runbooks/cloud-production.md) · [troubleshooting.md](../runbooks/troubleshooting.md)

根目录 **HANDOVER.md** 保留变更史；旧路径见 [historical-doc-links.md](../historical-doc-links.md)。**novaic-app/FRONTEND_ARCHITECTURE.md** — 前端分层详解。