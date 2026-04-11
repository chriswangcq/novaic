# Gateway 云端网关架构总览

本文档基于 `novaic-gateway` 子模块，全景展现作为 NovAIC 后端网络和存储核心枢纽的 Gateway 组件体系。
在整个系统拓扑中，Gateway 处理了从对外 HTTP 服务暴露、用户鉴权、全链路长连接下发、WebRTC 信令桥接、以及最终到业务记录的底层挂载。

---

## 1. 核心定位

`novaic-gateway` 是整个业务请求的总入口与中转枢纽，绝大部分代码运行在 HTTP/WebSocket 协议之上：
- **云端接入点**：绑定内网端口 `19999`，通常由 Nginx 通过 HTTPS 代理并处理前置的 `auth_request` 校验。
- **业务存储宿主**：引入并实例了 `Entangled.sql` 引擎。提供业务实体（Agent/Message/Tool）管理；以及自有的 `gateway.db` 维护运维、配额管控。
- **云桥中继 (CloudBridge)**：作为远端代理服务器，桥接云端与分布在各种用户本机/边缘硬件之上的 Tauri `VmControl`（实现内网穿透能力和本地指令下发）。

---

## 2. 核心架构拆解

在 `gateway` 目录下，按职责域划分为以下几组重点骨架，详细说明见同级目录下的 `docs/gateway/` 专题系列记录集。

### 2.1 高度聚合的 API 路由 (`gateway/api`)
所有的 FastAPI `Router` 在此处登记：
- **Auth 与鉴权**：不只是颁发 Token 的 `auth.py`，更有 `infra/deps.py` 提供贯穿所有的路由的权限验证推断依赖项 `Depends(get_current_user)`。
- **设备与 VM 管理**：提供给 UI 获取绑定信息的 `devices.py`，并将底层操作指向给 `pc_client` 和 `vmcontrol`。
- **内部调度代理**：提供 `/api/internal` 给局域网的其他子系统（例如 `Queue Service` 等任务处理器）反向执行宿主请求。以及包含给无端操作准备的 `TURN` 下发票据中心。

### 2.2 Entangled 同步生命周期的继承拦截 (`gateway/entity`)
基于 `Entangled` 的继承覆写体系：
- **`store.py` (业务挂载)**: 直接派生 `GatewayEntityStore`。所有向 `agents`, `chat_messages` 写入的数据会流经此类。我们将插入各种 `before_insert`, `after_update` Hook 用于例如分配 Agent 不重复的 Nano ID 或分发设备开机指令。
- **`entangled_bridge.py`**: 用来做初始化的网桥：在程序刚拉起时探察所有的实体 Schema 并告诉推送端它们的层级关系(`Relations`)和功能基线。
- **`defs.py`**: NovAIC 项目真正的核心配置表白处，所有的表结构约束（`FieldDef`）均由这边静态定义给到底层 Sqlite。

### 2.3 无界端侧通信与事件下发桥 (`gateway/api/app_client.py` 等)
为了支撑端侧 React Path C （见 Entangled 架构），网关包含复杂的 WebSocket 中心管理：
- **`AppBridge WS` (`/api/app/ws`)**: 用户 UI 连线的全骨架协议出口：处理 CRUD 下发、配置推回（Push_To_User）、WebRTC Answer/ICE 信令合并。绝不仅限纯粹数据下发。
- **`CloudBridge WS` (`/internal/pc/ws`)**: 提供给客户端内嵌运行的 Tauri 背后那个 `VmControl` 二进制连接回云端的后门，双边组成反向代理长连接（实现云指令打入内网的能力）。

### 2.4 v63 剥离时代的纯数据库管控 (`gateway/db`)
由于 `gateway/entity` 负责了 90% 的实时业务操作（甚至生成表）。那原本的 `gateway.db` 中还剩什么？
- **表消亡与留存 (v63 Schema)**：大量的表已经在 schema `v63` 之后执行了 `DROP`：由于已切换 Entangled 规范，`agents` / `chat_messages` 等影子表全部销毁。保留下的主要是 `users`、应用级偏好统计等非实时的基建数据。
- 对应遗留的那些 `repositories/...` 依然保留有原生的 SQLAlchemy/原石 Sqlite 逻辑管理这些底仓。

### 2.5 事件驱动分发阵列 (Queue Service Dispatch)
在 v2 架构演进中，原有的 Watchdog `status="sending"` 轮询机制已被完全废弃。现在 Gateway 中的高频触发行为（例如来自前端交互的 `USER_MESSAGE` 发送、以及 `agents.interrupt`）会直接被转化为无状态的 HTTP 调用，推向 Queue Service 的 `/api/queue/dispatch` 或 `/recover/cancel-all` 端点，实现纯基于事件的毫秒级调度唤醒，并将内部冗余的轮询探活彻底扫除了历史堆填区。

---

## 3. 设计思想补充说明

Gateway 的职责逐渐被削去了“任务流编排”，但补强了“网络穿透与元数据分发”：
当你在处理本地的 Saga/Queue 长进程运行库时，任何想要与外部建立链接的数据，均是以回调 `gateway` `/internal` 或被 `Gateway` 下发推给客户端去完成闭环呈现的！
