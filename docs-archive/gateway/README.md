# Gateway 网关架构拆页地图

> 本目录（`docs/gateway/`）提供 `novaic-gateway` 及 Business/Device 微服务的架构拆解。

与主干架构文档 [docs/gateway-architecture.md](../gateway-architecture.md) 配合食用。

## Business-Centric 架构（2026-04-15）

Gateway 完成了从 "God Module" 到薄边缘服务的拆分。当前数据面是 App 直连 Entangled sync WS；业务动作由 Entangled action 分发到 Business；Gateway 只做用户接入边界。

| 服务 | 端口 | 代码目录 | 职责 |
|------|------|---------|------|
| **Gateway** | `:19999` | `novaic-gateway/` | 薄边缘：Auth（JWT）、Blob edge、App WS（push + WebRTC signaling + Entangled endpoint discovery）、TURN |
| **Business** | `:19998` | `novaic-business/`（submodule） | 产品业务：Entangled action hooks（含 devices/messages）、Environment/Subscriber、内部产品 API、Device 生命周期编排 |
| **Device** | `:19993` | `novaic-device/`（submodule） | 纯硬件：Device registry、CloudBridge typed WS broker、`/internal/hardware/*` 执行、VM/Mobile/HD tool proxy |

**调用链路**：
- `Entangled → (ALL action hooks) → Business` — Entangled 仅回调 Business
- `App ↔ Entangled /entangled/v1/sync` — App 通过 Gateway 发现 endpoint 后直连 Entangled sync
- `Workers → Business / Cortex / LLM Factory` — Runtime 按职责调用产品 API、工作轨迹和模型层
- `Business → Entangled HTTP` — Business 是服务端 entity/action 写入方
- `Business → device_client.hw_*() → Device /internal/hardware/*` — Business 编排，Device 执行
- `Device → Business → Gateway /api/app/push → App` — WebRTC ICE/Answer 和用户定向 push 返回路径

**Gateway 仅保留**：
- `POST /auth/*`（register, login, refresh, logout）
- `GET /internal/auth/validate`（Nginx auth_request）
- `WS /api/app/ws`（App WS + WebRTC signaling）
- Entangled sync endpoint discovery（通过 App WS 首包/push）
- `POST /api/app/push`（server-to-app broadcast）
- `POST /api/blobs/upload-config`、`POST /api/blobs/register`（Blob 控制面）
- `/blob/*`（Nginx edge 直达 Blob Service 字节数据面）
- `GET /api/config/frontend`（前端配置）
- 本地 SQLite：仅 `users`、`refresh-tokens`

## 目录索引

### 网络与连接生命线
| 专题 | 说明 |
|------|------|
| [rest-auth-and-deps.md](rest-auth-and-deps.md) | FastAPI 路由配置栈，双轨鉴权（Token VS. Nginx Header），以及全局权限依赖链 `get_current_user`。 |
| [cloudbridge-vm.md](cloudbridge-vm.md) | `CloudBridge WS`：Device Service ↔ VmControl 的 typed WebSocket 通信协议。PC Client WS 归属 Device Service (`:19993`)，Gateway 不拥有 CloudBridge。 |
| [../architecture/cloudbridge-vmcontrol-hard-cut.md](../architecture/cloudbridge-vmcontrol-hard-cut.md) | CloudBridge / VmControl / Device Service 硬切归档入口；当前协议以 `cloudbridge-vm.md` 为准。 |
| [app-ws-and-signaling.md](app-ws-and-signaling.md) | `App WS`：Gateway 边缘长连接，负责 push、Entangled endpoint discovery、WebRTC Offer/Answer/ICE 信令。 |

### 数据库层融合记录
| 专题 | 说明 |
|------|------|
| [entangled-hooks.md](entangled-hooks.md) | Business 侧 Entangled action hooks：Gateway 不继承 Entangled，不拥有业务 hook。 |
| [db-v63-split.md](db-v63-split.md) | "表消融时代"：v63 版本的 Scheme DROP 操作记录，哪些走了 Entangled（业务表），哪些留在了基础层（运维/全局配置）。 |

### 内部微服务微循环
| 专题 | 说明 |
|------|------|
| [internal-and-workers.md](internal-and-workers.md) | 给内部 Worker / Saga 反向调用的 `/internal` 接口组，以及与 Factory / Cortex 是如何互动的（含 Worker SSE 保活或信号机制的残留说明）。 |
