# Gateway 网关架构拆页地图

> 本目录（`docs/gateway/`）提供 `novaic-gateway` 及 Business/Device 微服务的架构拆解。

与主干架构文档 [docs/gateway-architecture.md](../gateway-architecture.md) 配合食用。

## Business-Centric 架构（2026-04-15）

Gateway 完成了从"God Module"到三层微服务的拆分，Business Service 为中枢编排层：

| 服务 | 端口 | 代码目录 | 职责 |
|------|------|---------|------|
| **Gateway** | `:19999` | `novaic-gateway/` | 薄边缘：Auth（JWT）、File Proxy、App WS（broadcast + WebRTC signaling）、前端配置 |
| **Business** | `:19998` | `novaic-business/`（submodule） | **中枢**：所有 Entangled action hooks（含 devices）、所有 `/internal/*` API、Device 生命周期编排 |
| **Device** | `:19993` | `novaic-device/`（submodule） | 纯硬件：Device registry、CloudBridge typed WS broker、`/internal/hardware/*` 执行、VM/Mobile/HD tool proxy |

**调用链路**：
- `Entangled → (ALL action hooks) → Business` — Entangled 仅回调 Business
- `Workers → /internal/* → Business` — 产品 mutation 和工具执行内部 API 指向 Business
- `Gateway / Device / Workers → /internal/entities/* → Business → Entangled` — **所有 entity CRUD 经 Business 代理**
- `Business → device_client.hw_*() → Device /internal/hardware/*` — Business 编排，Device 执行
- `Business → device_client.hw_*() → Device /internal/hardware/*` — 设备生命周期和硬件动作编排
- `Device → /api/app/push → Gateway` — WebRTC ICE/Answer 推送

**Gateway 仅保留**：
- `POST /auth/*`（register, login, refresh, logout）
- `GET /internal/auth/validate`（Nginx auth_request）
- `WS /api/app/ws`（App WS + WebRTC signaling）
- `POST /api/app/push`（server-to-app broadcast）
- `GET/POST /api/files/*`（File Service proxy）
- `GET /api/config/frontend`（前端配置）
- 本地 SQLite：仅 `users`、`refresh-tokens`

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
