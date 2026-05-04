# Gateway 云端网关架构总览

本文档基于 `novaic-gateway` 子模块，描述 Gateway 作为 NovAIC 系统**薄边缘网关**的职责与架构。
在当前架构下，Gateway 不再承担业务逻辑、设备通信或 Entangled schema/action 权威；它只负责用户接入层的认证、App WS 信令/推送、Entangled sync endpoint discovery、TURN 与 Blob 代理。

---

## 1. 核心定位

`novaic-gateway` 是面向公网的**薄边缘服务**，绑定内网端口 `19999`，由 Nginx HTTPS 反向代理对外暴露：
- **认证入口**：JWT 签发与校验（`/api/auth/*`），同时为 Nginx `auth_request` 提供 `/internal/auth/validate` 端点。
- **App WebSocket**：维护与前端 Tauri App 的长连接（`/api/app/ws`），承载后端推送、WebRTC 信令中继，以及 Entangled sync endpoint discovery。
- **TURN 凭证**：为 WebRTC 连接下发 TURN/STUN 服务器凭证（`/api/turn/credentials`）。
- **Blob 代理**：将附件/大对象字节访问代理到 Blob Service。
- **窄下游**：业务/信令编排只指向 **Business Service (`:19998`)**；字节代理指向 Blob Service；Gateway 不访问 Entangled HTTP，不直连 Device，也不调 Worker。

---

## 2. 核心架构拆解

### 2.1 API 路由 (`gateway/api`)

所有 FastAPI `Router` 在此处登记：
- **Auth**：`auth.py` 负责用户登录、注册、Token 签发。`infra/deps.py` 提供贯穿所有路由的 `Depends(get_current_user)` 权限校验。
- **App WS**：`app_client.py` 管理前端 WebSocket 连接。职责包括：
  - 推送 Entangled sync endpoint 给客户端
  - 接收 Business Service 的用户定向 push 并下发给对应 App
  - 作为 WebRTC 信令中继的前半段（App ↔ Gateway ↔ Business）
- **TURN**：`turn.py` 生成并下发 TURN 凭证。
- **Blob Proxy**：代理附件/大对象字节访问到 Blob Service。
- **无业务转发通用层**：Gateway 不再保留 generic Business entity client；产品 entity CRUD / action 由 App ↔ Entangled ↔ Business 处理。

### 2.2 本地认证存储 (`gateway/entity`)

- **`store.py` (`AuthEntityStore`)**：本地 SQLite 存储，**仅管理认证相关实体**（`users`、`refresh_tokens`）。不包含任何业务实体（Agent/Message/Tool 等已迁移到 Entangled，由 Business Service 代理访问）。
- 原 Gateway 业务实体存储层已不存在。Gateway 不再是 Entangled 的宿主。

### 2.3 WebRTC 信令转发

Gateway 在 WebRTC 信令链路中仅承担**前端侧中继**角色：

```
App (WS) → Gateway → Business /internal/signaling → Device → CloudBridge → VmControl
VmControl → Device → Business → Gateway → App (WS)
```

Gateway 不拥有 CloudBridge 连接，不直接与 Device Service 通信。

### 2.4 已移除的职责

以下功能已在 Business-Centric 重构中从 Gateway 移除：
- ~~业务实体存储（Entangled EntityStore）~~ → Business Service 代理 Entangled
- ~~CloudBridge WS (`/internal/pc/ws`)~~ → Device Service
- ~~设备管理（`device_client.py`、`pc_client`）~~ → Device Service
- ~~`/internal/*` 业务 API~~ → Business Service（仅保留 `/internal/auth/*`）
- ~~Queue Service 调度~~ → Workers 直接调用 Business Service

---

## 3. 设计思想

Gateway 遵循**薄网关**原则：

- **最小职责**：只做用户无法绕过 Gateway 的事情——认证、面向用户的 WS、TURN、Blob 代理。
- **边界清晰**：业务逻辑统一在 Business Service；实体同步统一在 Entangled；Gateway 只做用户接入必须经过的边缘职责。
- **无状态（接近）**：除本地 SQLite 中的 auth 数据外，Gateway 不持有任何业务状态。
- **故障隔离**：Business / Device / Worker 任一崩溃不影响 Gateway 的认证和连接管理。
