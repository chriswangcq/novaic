# NovAIC 架构概览（L1）

本文档描述**父仓库视角**的系统拓扑：各 **git submodule** 的职责、典型数据流与**可验证**的本地端口约定。细节以各子模块源码与 `HANDOVER.md` 为准。

## 1. 仓库与边界

- **父仓库**：聚合脚本（`deploy`）、共享配置（`novaic-common`）、顶层文档（本目录）。
- **实现代码**：几乎都在 **submodule** 内；改行为时请进入对应目录并以其 CI/README 为准。
- **`.gitmodules`**：权威 submodule 清单；初始化：`git submodule update --init --recursive`。

## 2. 逻辑拓扑（简化）

```
                    ┌─────────────────┐
                    │  Relay / STUN   │  novaic-quic-service（P2P 兜底 + 静态资源 CDN）
                    └────────┬────────┘
                             │
  ┌──────────────┐    ┌──────▼──────┐    ┌──────────────────┐
  │  novaic-app  │◄──►│   Gateway   │◄──►│ Agent Runtime    │
  │  (Tauri UI)  │    │ (FastAPI)   │    │ (任务/Saga/工具)  │
  └──────┬───────┘    └──────┬──────┘    └────────┬─────────┘
         │                 │                     │
         │                 │                     ▼
         │                 │            ┌──────────────────┐
         │                 └───────────►│ Cortex (HTTP)    │  认知/Scope/Sandbox
         │                              └──────────────────┘
         ▼
  Entangled / 本地 SQLite（实体与同步；详见各子模块）
```

- **桌面/移动端**：`novaic-app` — React/Vite + Tauri；经 CloudBridge / REST 与 Gateway 通信；本地 Entangled 客户端与缓存。
- **云端 API**：`novaic-gateway` — REST、内部 WS、与编排相关的服务端能力；生产环境前面通常有 Nginx（见 `HANDOVER.md` §2.1）。
- **Agent 执行**：`novaic-agent-runtime` — 任务队列、Saga、工具分发；与 Cortex 协作。
- **Cortex**：`novaic-cortex` — 独立 HTTP 服务（默认端口见下），Agent 通过工具调用与之交互，不直连业务 UI。
- **P2P**：`novaic-quic-service` — STUN/TURN 侧配合 Gateway 与客户端 WebRTC（细节见 `HANDOVER.md`）。
- **协议与类型**：`novaic-contracts`；**共享库**：`novaic-common`（含统一 `config/services.json`）。

## 3. 典型本地端口（`novaic-common/config/services.json`）

以下为主机 `127.0.0.1` 上的**约定端口**（本地开发常用；若冲突请改环境变量或配置）。


| 服务键 (`services.json`) | 端口    | 说明                                                     |
| --------------------- | ----- | ------------------------------------------------------ |
| `gateway`             | 19999 | Gateway HTTP                                           |
| `queue_service`       | 19997 | 队列相关服务端点                                               |
| `tools_server`        | 19998 | 历史/兼容命名；当前工具链以 Agent-Runtime + Cortex 为主（见 `HANDOVER`） |
| `vmcontrol`           | 19996 | 本地 VmControl HTTP（Tauri 侧嵌入控制面）                        |
| `file_service`        | 19995 | 文件服务                                                   |
| `tool_result_service` | 19994 | 工具结果服务                                                 |
| `entangled_service`   | 19900 | Entangled 相关本地服务端口约定                                   |


**Cortex**（`novaic-cortex`）默认 **19996**（环境变量 `CORTEX_PORT`），与 `services.json` 中 `vmcontrol` 端口数字相同；**同一台机器同时起 VmControl 与 Cortex 时需避免端口冲突**（调整其一）。

## 4. Submodule 速查


| 目录                     | 角色                                                   |
| ---------------------- | ---------------------------------------------------- |
| `novaic-app`           | 客户端 UI、Tauri、VmControl 嵌入、与 Gateway/Entangled 交互     |
| `novaic-gateway`       | API 网关、运维向 SQLite（`gateway.db` 等；业务实体以 Entangled 为准） |
| `novaic-agent-runtime` | Agent 运行时、工具执行管线                                     |
| `novaic-cortex`        | Cortex HTTP、Workspace/Scope/Sandbox                  |
| `novaic-llm-factory`   | 集中化 LLM 代理（运维与 URL 见 `HANDOVER.md`）                  |
| `novaic-quic-service`  | STUN/Relay/静态资源                                      |
| `novaic-common`        | 共享配置与工具（含 `config/services.json`）                    |
| `novaic-contracts`     | 协议与类型                                                |
| `novaic-storage-a`     | 文件存储服务                                               |
| `novaic-mcp-vmuse`     | MCP VMuse                                            |
| `novaic-control-plane` | 控制面板                                                 |
| `thirdparty/openclaw`  | 上游参考（非线上服务）                                          |


## 5. 文档地图（由 HANDOVER 拆分）

| 主题 | 文档 |
|------|------|
| OTA 薄壳、生产拓扑、TURN/macOS 键盘 | [thin-client-and-topology.md](thin-client-and-topology.md) |
| JWT、Nginx、`X-User-ID` | [authentication.md](authentication.md) |
| 远程桌面 WebRTC、VmControl | [webrtc.md](webrtc.md) |
| App WS、Entangled、Sync Contract 索引 | [realtime-sync.md](realtime-sync.md) |
| Entangled vs gateway.db、消息持久化 | [data-ownership.md](data-ownership.md) |
| Saga、ReactThink、工具、LLM Factory | [agent-pipeline.md](agent-pipeline.md) |
| Cortex、DFS Step Tree | [cortex.md](cortex.md) |
| 前端 Path C、路由、codegen | [app-ui.md](app-ui.md) |
| 子模块列表 | [../reference/submodules.md](../reference/submodules.md) |
| 环境变量与本地路径 | [../reference/config-and-environment.md](../reference/config-and-environment.md) |
| 文件 API、语音录制 | [../reference/file-service.md](../reference/file-service.md) |

**Runbooks**：[local-dev.md](../runbooks/local-dev.md) · [local-backends.md](../runbooks/local-backends.md) · [deploy.md](../runbooks/deploy.md) · [build-and-release.md](../runbooks/build-and-release.md) · [cloud-production.md](../runbooks/cloud-production.md) · [troubleshooting.md](../runbooks/troubleshooting.md)

根目录 **`HANDOVER.md`** 仍为全文与变更历史；旧 `docs/...` 文件名见 [**`historical-doc-links.md`**](../historical-doc-links.md)。**`novaic-app/FRONTEND_ARCHITECTURE.md`** — 前端分层详解。

