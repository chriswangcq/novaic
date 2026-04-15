# Gateway 网关架构拆页地图

> 本目录（`docs/gateway/`）提供 `novaic-gateway` 及拆分后的 Business/Device 微服务的架构拆解。

与主干架构文档 [docs/gateway-architecture.md](../gateway-architecture.md) 配合食用。

## 微服务拆分（2026-04-14）

Gateway 完成了从"God Module"到微服务的拆分：

| 服务 | 端口 | 代码目录 | 职责 |
|------|------|---------|------|
| **Gateway** | `:19999` | `novaic-gateway/` | 瘦网关：Auth（JWT）、Entity Proxy、Turn（对话调度）、File Proxy、App WS |
| **Business** | `:19994` | `novaic-business/`（submodule） | Agent/Skill/Form/Model CRUD、消息操作、日志查询、Provider 代理 |
| **Device** | `:19993` | `novaic-device/`（submodule） | Device registry、CloudBridge typed WS broker、VmControl typed command routing、northbound 设备 API |

**关键设计决策**：
- 三个服务共享 `novaic-common` 配置和 `novaic-gateway` 的 Python venv（Business/Device 没有独立 venv）
- 所有服务统一使用 `uvicorn.run(app, ...)` 直传 app 对象（避免字符串 import 导致 CLI args 在 worker 进程中丢失）
- 通过 Nginx `/device/` 前缀路由区分 Device Service 流量
- 所有业务实体 CRUD 通过 `RemoteEntityStore` 代理到 Entangled

## 目录索引

### 网络与连接生命线
| 专题 | 说明 |
|------|------|
| [rest-auth-and-deps.md](rest-auth-and-deps.md) | FastAPI 路由配置栈，双轨鉴权（Token VS. Nginx Header），以及全局权限依赖链 `get_current_user`。 |
| [cloudbridge-vm.md](cloudbridge-vm.md) | `CloudBridge WS`：Device Service ↔ VmControl 的 typed WebSocket 通信协议。PC Client WS 归属 Device Service (`:19993`)，Gateway 不拥有 CloudBridge。 |
| [../architecture/cloudbridge-vmcontrol-hard-cut.md](../architecture/cloudbridge-vmcontrol-hard-cut.md) | CloudBridge / VmControl / Device Service 的硬切设计文档：删除本地 QEMU、VNC 与 `proxy_request`，收敛到 typed WS 协议。 |
| [app-ws-and-signaling.md](app-ws-and-signaling.md) | `AppBridge WS`：不仅提供数据推送，且承载了 WebRTC Offer/Answer/ICE 打洞信令的共轨传输。 |

### 数据库层融合记录
| 专题 | 说明 |
|------|------|
| [entangled-hooks.md](entangled-hooks.md) | 业务侵入点剖析：网关继承自 `Entangled` 且用各种 `before/after` Hook 发送附带行为。 |
| [db-v63-split.md](db-v63-split.md) | "表消融时代"：v63 版本的 Scheme DROP 操作记录，哪些走了 Entangled（业务表），哪些留在了基础层（运维/全局配置）。 |

### 内部微服务微循环
| 专题 | 说明 |
|------|------|
| [internal-and-workers.md](internal-and-workers.md) | 给内部 Worker / Saga 反向调用的 `/internal` 接口组，以及与 Factory / Cortex 是如何互动的（含 Worker SSE 保活或信号机制的残留说明）。 |
