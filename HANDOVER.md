# NovAIC 项目交接文档

> 最后更新：2026-03-26（Gateway 迁移至 Entangled 数据流 - 完成部署及依赖/死锁修复，API 正常唤起）

---

## 快速上手

| 需求 | 操作 |
|---|---|
| 本地跑起来 | `cd novaic-app && npm install && npm run tauri:dev` |
| **部署前端 OTA** | `./deploy frontend [version]` |
| **部署 Gateway** | `./deploy gateway` |
| **部署全部后端** | `./deploy services` |
| **部署 Relay** | `./deploy relay` |
| **构建安装 iOS** | `./deploy ios` |
| **构建桌面 App** | `./deploy desktop` |
| **部署全部** | `./deploy all [version]` |
| **查看服务状态** | `./deploy status` |
| 改前端 UI | 改 `novaic-app/src/components/`，热更新生效 |
| 改消息/日志逻辑 | `messageService.ts`、`logService.ts`、`syncService.ts` |
| 改远程桌面连接 | `useWebRtc.ts`、`WebRtcScrcpyView.tsx`（统一 WebRTC，noVNC 已全部移除） |
| 改设备操控台 | `DeviceConsole.tsx`、`ConsoleToolbar.tsx`、`useWebRtc.ts`、`useRemoteInput.ts` |
| 清空本地缓存 | Settings → Clear Cache → 清空本地 DB 缓存 |
| 查架构 | `novaic-app/FRONTEND_ARCHITECTURE.md`、`docs/design/DESIGN-P2P-UNIFIED.md` |


---

## 一、项目整体架构

### OTA-First 薄壳架构（2026-03-21）

彻底重构为**基于云端 OTA 的 Thin Client (薄壳) 模式**，旨在极大提升跨端（Desktop + Mobile）的前端迭代速度：
1. **体积缩减百倍**：现在 `novaic-app` Release 仅内嵌极简的 24KB 静态 Loading 页面（`src-tauri/loading/index.html`），摒弃了以往动辄数 MB 的全量 assets bundle。
2. **纯云端按需加载**：客户端启动后，请求 Relay 源获取 CDN 链接，无缝跳转（navigate）到最新版的 Frontend-UI，使得修 Bug 终于可以通过 `./deploy frontend` 秒发版而不再需要缓慢打包/升版/引导下载桌面 binary。
3. **Rust 原生 API 透传前端**：集成了极其强劲的官方 `@tauri-apps/plugin-sql`（其底层依赖更新了版本的 `sqlx 0.8.0`），授予通过 OTA 运行于客户端前端的 JS/React 执行本地 SQLite 数据操作的直接权限。自今日起，涉及 App 配置、持久化、离线缓存和消息回看的功能将全部在**纯前端侧直接建表操作原生存储**。

```
用户 macOS 桌面
└── NovAIC.app (Tauri)
    ├── 前端 React/Vite          ← novaic-app/src/
    │   ├── IndexedDB 本地缓存   ← 消息、日志、偏好、附件（按 userId 隔离）
    │   ├── AppBridge WS 推送    ← User 维度（接收 chat_message / config_updated）
    │   └── WebRTC 客户端        ← 所有远程桌面显示（VM/Android/HD/Subuser）
    └── Rust 后端
        ├── Tauri Commands       ← gateway_* HTTP 代理（唯一 IPC 通道）
        ├── vmcontrol（内嵌）     ← novaic-app/src-tauri/vmcontrol/
        │   ├── WebRTC Engine     ← H.264 编码 + peer connection（统一管线）
        │   ├── 管理 QEMU Linux VM (QMP socket)
        │   ├── 管理 Android 模拟器 (scrcpy WebRTC)
        │   ├── VM 准备 API：环境检查、镜像检查/下载、部署等待
        │   └── 供 Gateway 经 Cloud Bridge 调用
        └── CloudBridge WebSocket ──► 云端 Gateway（在 vmcontrol 内）

云端服务器 api.gradievo.com
└── Nginx (HTTPS/443 → 127.0.0.1:19999)
    ├── auth_request → /internal/auth/validate  ← HS256 JWT 验证，注入 X-User-ID
    └── Gateway (Python/FastAPI, port 19999)
        ├── REST: /api/**, /internal/**
        ├── WS Push: 通过 pc_client 下发 gateway_push 事件 (无 SSE 端点)
        ├── CloudBridge WebSocket: /internal/pc/ws
        ├── P2P: /api/p2p/heartbeat, locate, relay-request
        └── SQLite: /opt/novaic/data/gateway.db

云端服务器 relay.gradievo.com + stun.gradievo.com（novaic-quic-service 同机）
└── STUN (UDP 3478) + Relay (QUIC 443) + Nginx 静态前端
    ├── STUN: 供 PC 获取外网地址（RFC 5389）
    ├── Relay: P2P 直连不可达时兜底
    └── relay.gradievo.com/resource/frontend/: App 热更新 CDN
```

### Entity Layer Migration (Phase 1-3 完成，2026-03-23)

**背景**：Gateway 层的数据库操作曾充斥大量手写 SQL 的 `*Repository`，导致数据层和业务层耦合，且缺乏统一的事件通知和 Schema 管理机制。

**新架构**：引入统一的 `EntityStore` (基于 `EntityDef` 实体抽象)，实现：
1. **统一 CRUD**：用统一的 `create`, `list`, `get`, `update`, `delete`, `upsert` 操作替代零散 SQL
2. **声明式 Schema**：所有字段和类型在 `EntityDef` 内定义
3. **自动通知**：执行 CRUD 操作自动调用 `notify_entity_change` 推送给前端

**已完成迁移（Phase 1-3 安全区域）**：
- `agent-tools`：修改了 `agents.py` 及相关 bootstrap-files 逻辑，全面调用 `get_entity_store()`
- `vm-users`：替换了所有用户存取逻辑，并改造了 `_next_display_num` 等副作用函数
- `skills`：重构了 `SkillRepository`，拆分了 builtin 文件加载（只读）与 custom 记录存取（使用 `EntityStore`）
- `agent-binding`：重构 `AgentDeviceBindingRepository`，使其完全代理到 `EntityStore`（忽略 `user_id`）
- `agent-state`：将零散的 `agent_runtime_state` (K-V 模型) 迁移至结构化的 `agent_state` 实体表。淘汰了旧版全局 `get_runtime_state` 方法，完全打通 `EntityStore.upsert` 记录 Agent 休眠与唤醒状态。

**Stream Entities 架构迁移 (2026-03-23)**：
- 扩展了 `EntityStore` 的类型抽象，加入了 `EntityType.STREAM`，支持高频写入和实时广播。
- 添加了 `store.append`，`store.cas_update` 以及高级游标分页 `store.list_stream` 方法，以满足高吞吐场景与 CAS 控制需求并支持复杂的过滤和时间复合排序。
- `messages`：已通过拦截器加底层代理的方式修改了 `MessageRepository` 的内部实现，`add_message` 现委托给 `EntityStore.append` 自动分发事件，`claim_by_id` 和 `confirm_message` 现使用 `EntityStore.cas_update` 移除硬编码的 SQL。`get_messages` 替换为 `list_stream`。
- `execution_logs`：已升级为第一级别 `STREAM` 实体。全线替换 `ChatRepository.upsert_execution_log` / `add_execution_log` 等冗长逻辑为 `EntityStore.cas_update` / `append`，底层完全依赖 `list_stream` 完成带 Cursor 分页。

**大流量文件（Base64 图片）防爆与拦截架构 (2026-03-23)**：
- Gateway 的 `ChatRepository` 已完全剥除所有祖传 `_convert_large_images_to_urls` 防线。
- 剥离脏活逻辑至边缘侧：`novaic-tools-server` 被定义为最终兜底层。
- 引入 `TOOL_ADAPTER_REGISTRY` 与递归扫描拦截：所有 Tool 返回（不论是原生 MCP `content`，还是野节点的深层 JSON 字典）只要被探测到超标大小的 Base64，边缘侧自动将其就地 POST 到 `novaic-storage-a/b` 的 `/api/files/from-base64`，并立刻转化为几十字节的 `fs://images/...` 指针后再发入 Gateway 的 `EntityStore`。Gateway 网络彻底摆脱巨型带宽损耗污染。

**规划外/暂缓迁移（风险区域）**：
- `api-keys`：完全不适用（因安全隔离）

### Entangled Sync Protocol (Phase 1-3 完成，2026-03-25)

**背景**：原有 `EntityStore` 只通过 WS 发送离散颗粒的增量更新（CREATED/UPDATED/DELETED），导致前端为了维持复杂关联（如 Agent 删除了其 Binding 应该同步消失、List 添加或删除需要人工维护顺序）堆砌了大量硬编码 Hook (`entityGraph.ts`, `data/entities/*`)。

**新架构：Entangled Delta Sync (Phase 1-3 Backend 基础设施已迁移)**：
1. **统一缓存协议**：用 Rust (Tauri 内核) 实现高性能、带 LRU 淘汰的本地一致性缓存。服务端 Gateway 发送标准 `Snapshot`（全量快照）和 `Delta` (增量 Ops)，前端无脑还原最新状态。
2. **WebSocket 多路复用**：去掉了原定新增的单独 `/api/sync/ws`，通过复用 `novaic-gateway` 已有的 `/api/app/ws`，下发 `sync` mode 的 action 进行协议融合。 
3. **乐观 UI 与 RequestId 链路**：打通了 `request_id` 的全链路传递 (`React -> AppBridge -> Gateway -> EntityStore -> SyncRegistry -> AppBridge -> React`)，用来确保 UI 乐观操作后收到云端通知时能够精准核销 (`pendingOps`)。
4. **延迟与 Stream 限制**：修复了 `messages` 和 `execution-logs` 等 stream 数据被 `entangled.server.sync` 一次性拉取全部的问题，引入了 `limit: 100` 以确保初始同步不会将上万条历史包发给客户端。
5. **隐式级联自动 Invalidate**：针对 `agent` 删除需要客户端顺带淘汰由于 SQLite `CASCADE` 被静默清理的 `agent-binding` 问题，直接注入 `notify("invalidated", "agent-binding")` 使客户端响应式淘汰陈旧关系。
6. **Rust Tauri 暴露**：`novaic-app/src-tauri` 现已完全集成了 `@entangled/client-rust`，能够接收 `IncomingMessage::Sync` 并通过 Rust 更新本地内存大表库，仅将 `changes` 事件向前端发射。

> **当前交接状态（Phase 4：Frontend Cleanup 待完成）**：后端 + Rust Core 均编译/运转正常。但是，前端 `@entangled/react` 在应用 `ListStore.getData()` 剥离后存在 84 处 TS 静态断言错误（由于没有补齐类型与 `@tauri-apps/api` 的 PeerDependencies）。下一任代理请运行 `cd novaic-app && npm run build` 根据报错修复 TypeScript，以完成全面切流。

### macOS 桌面版 SIGTRAP 崩溃修复（2026-03-22，全面修复）

**问题**：桌面版 (ByClaw.app) 运行时随机崩溃 SIGTRAP，crash 线程总是 `tokio-runtime-worker`。

**根因**：`enigo.key()` / `enigo.text()` 内部调用 macOS `TSMCurrentKeyboardInputSourceRefCreate`（Text Services Manager API），该 API **必须在 main dispatch queue 执行**。tokio worker 线程上调用触发 `dispatch_assert_queue` 断言失败 → SIGTRAP。

**修复（三轮）**：macOS 上所有 enigo 键盘操作替换为 `CGEvent`（`core_graphics` crate，线程安全）。非 macOS 平台不受影响。

| 文件 | 改动 | 轮次 |
|------|------|------|
| `vmcontrol/src/input/handler.rs` | `sync_modifiers()` / `release_all_keys()` 改用 `send_modifier_event()`（CGEvent）| 第 1 轮 |
| `vmcontrol/src/api/routes/hd_tools.rs` | `hd_keyboard()` 全部替换为 `hd_cg_key_event()` / `hd_cg_type_string()`（CGEvent）| 第 2 轮 |
| `vmcontrol/src/input/handler.rs` | 未知键 fallback 从 `enigo.key()` 改为 `cg_type_string()` Unicode 注入 | 第 3 轮 |

**结论**：macOS 上 **零** `enigo.key()` / `enigo.text()` 调用残留。鼠标操作（`enigo.move_mouse` / `enigo.button` / `enigo.scroll`）不触发 TSM，保留使用 enigo。

### TURN 服务器维护（relay.gradievo.com，2026-03-22）

**coturn 配置**：`/etc/turnserver.conf`（端口 3478 UDP/TCP，realm gradievo.com，use-auth-secret）

**TLS 证书权限问题（已修复）**：coturn 以 `turnserver` 用户运行，但 Let's Encrypt `/etc/letsencrypt/live/` 和 `/etc/letsencrypt/archive/` 默认权限 `700`（仅 root），导致 TURNS (5349) 无法启动。修复：`chmod 755` + privkey `chgrp turnserver`。

**coturn 长时间运行问题**：coturn 跑 6+ 天后积累大量僵尸 session（`Connection reset by peer`），可能导致新 TURN allocation 失败。重启即恢复。建议定期重启或设置 session 超时。

**TURN 凭证流转架构（2026-03-22 修复完成）**：

TURN 凭证使用 coturn time-limited credentials（HMAC-SHA1）。

**旧架构（已废弃）**：客户端和 VmControl 各自独立生成 TURN 凭证。VmControl 从 `TURN_SECRET` 环境变量生成，但桌面端没有该变量 → STUN-only → 非局域网黑屏。

**新架构（2026-03-22 修复）**：Gateway 统一注入 TURN 凭证到 `webrtc_offer` 消息，VmControl 直接使用，不再依赖本地 `TURN_SECRET`。

| 端 | 凭证来源 | 关键文件 |
|---|---|---|
| **客户端** (useWebRtc.ts) | Gateway HTTP `/api/turn/credentials` 返回 | `useWebRtc.ts`, `gateway/api/turn.py` |
| **VmControl** (peer.rs) | **Gateway 注入到 webrtc_offer 的 `ice_servers` 字段**（回退：本地 `build_ice_servers()`） | `peer.rs::parse_ice_servers_json()` |

**修改文件（4 个）**：

| 文件 | 改动 |
|---|---|
| `gateway/api/app_client.py` | `_relay_webrtc_offer_to_pc()` 调用 `generate_turn_credentials()` 注入 `ice_servers` 字段 |
| `vmcontrol/src/cloud_bridge.rs` | `WebrtcOffer` 枚举新增 `ice_servers: Option<Value>`，透传到本地 router |
| `vmcontrol/src/api/routes/webrtc_unified.rs` | `UnifiedStartReq` 新增 `ice_servers` 字段，传给 `create_peer_for_broadcaster_with_target` |
| `vmcontrol/src/webrtc/peer.rs` | 新增 `parse_ice_servers_json()` 解析 Gateway JSON → `RTCIceServer`（含 TURN username/credential），None 时回退 `build_ice_servers()` |

**日志确认**：成功时 VmControl 输出 `[WebRTC] Using 2 ICE servers from Gateway (TURN=true)`。

### 远程桌面架构（WebRTC 统一管线 + Device Registry，2026-03-19）

所有设备类型统一走 WebRTC。**前端只传 `device_id`**，VmControl 从本地 SQLite Device Registry 查设备类型并自动分发：

**统一入口（新）**

```
前端 useWebRtc.ts
  ↓  POST /api/vmcontrol/webrtc/start
     { device_id, sdp_offer, [username] }
  ↓
VmControl: GET device FROM sqlite WHERE device_id = ?
  ↓ linux_vm   → webrtc_vm.rs  → VNC socket → H.264
  ↓ android    → webrtc_scrcpy.rs → Scrcpy → H.264
  ↓ host_desktop → webrtc_hd.rs → Screen Capture → H.264
```

**Device Registry 同步流程（Gateway → VmControl）**

```
VmControl CloudBridge 连接 Gateway /internal/pc/ws
  → Gateway 推送 sync_devices（pc_client_id 绑定的设备列表）
  → VmControl upsert 到本地 sqlx SQLite（vmcontrol.db）

触发时机（三重保障）：
  1. PC 连接建立后 200ms（全量）
  2. vm_status_report DB 写完后立即回推（关键补救）
  3. 设备 CRUD 时增量推送
```

| 文件 | 职责 |
|------|------|
| `vmcontrol/src/db/mod.rs` | SQLite 初始化，`devices` 表 schema |
| `vmcontrol/src/db/device_repo.rs` | `get_device()`, `upsert_many()`, `DeviceKind` enum |
| `vmcontrol/src/api/routes/webrtc_unified.rs` | 统一入口 handler，查 registry → dispatch |
| `vmcontrol/src/cloud_bridge.rs` | `SyncDevices` 消息处理，写入 registry |
| `gateway/api/internal/pc_client.py` | `_push_sync_devices()` 推送逻辑 |
| `gateway/api/devices.py` | `_broadcast_device_update()` 增量推送 |
| `src/hooks/useWebRtc.ts` | 前端：统一用 `UNIFIED_START/STOP`，不感知 device_type |

**旧路由（保留兼容，未来计划删除）**

| 设备类型 | 旧路径 | 新路径 |
|----------|--------|--------|
| Linux VM | `/api/vmcontrol/vm/webrtc/start` | `/api/vmcontrol/webrtc/start` |
| Host Desktop | `/api/vmcontrol/host-desktop/webrtc/start` | 同上 |
| Android | `/api/vmcontrol/android/webrtc/start` | 同上 |

> ⚠️ **noVNC 已于 2026-03-19 全栈移除**（前端 14 个文件 + Tauri Rust 6 个文件 + 755 行 vnc_proxy.rs）。所有远程桌面均走 WebRTC。

### WebRTC 全通道 WS 信令（方案 B，2026-03-20）

**旧方案**：SDP 走 HTTP（`gateway_post`），ICE candidates 走 WS。两条通道不同步，导致竞态（session_id 未返回时 candidate 已到达、remoteDescription 未设置时已收到 candidate 等）。

**新方案（方案 B）**：**offer / answer / candidates 全走同一条 AppBridge WS**。WS 保证消息顺序：answer 必在 candidates 之前到达，天然无竞态。

**信令流程**：

```
前端 invoke('send_webrtc_offer')
  → AppBridge WS: {"type":"webrtc_offer","device_id":"...","sdp_offer":"..."}
  → Gateway app_client.py: _relay_webrtc_offer_to_pc()
  → CloudBridge WS: {"type":"webrtc_offer",...} push to PC
  → VmControl cloud_bridge.rs: Router::oneshot("/api/webrtc/start")
  → axum handler 创建 peer + answer
  → CloudBridge WS: {"type":"webrtc_answer","device_id":"...","session_id":"...","sdp_answer":"..."}
  → Gateway pc_client.py: push_webrtc_answer_to_user()
  → AppBridge WS push: {"type":"push","event":"webrtc_answer","data":{...}}
  → 前端 listen('gateway_push') 收到 answer → setRemoteDescription

ICE candidates（双向，同一条 WS）：
  前端 → AppBridge WS → Gateway → CloudBridge WS → VmControl
  VmControl → CloudBridge WS → Gateway → AppBridge WS push → 前端
```

| 文件 | 改动 |
|------|------|
| `useWebRtc.ts` | `invoke('send_webrtc_offer')` 替代 `gateway_post`；单 listener 处理 `webrtc_answer` + `ice_candidate`；Promise 等 answer |
| `commands/webrtc.rs` | 新增 `send_webrtc_offer` Tauri command |
| `app_bridge.rs` | 新增 `OutgoingMessage::WebrtcOffer` + `send_webrtc_offer()` 方法 |
| `app_client.py` | 新增 `_relay_webrtc_offer_to_pc()` + `push_webrtc_answer_to_user()` |
| `pc_client.py` | 新增 `webrtc_answer` 消息处理 |
| `cloud_bridge.rs` | 新增 `IncomingMessage::WebrtcOffer` + `OutgoingMessage::WebrtcAnswer`；`Router::oneshot()` 调本地 axum |
| `permissions/allow-app-commands.toml` | 添加 `send_webrtc_offer` + `send_ice_candidate` 到 Tauri v2 权限 |

### App→Gateway WS 请求/响应通道（2026-03-20）

**问题**：`chat_send`、`interrupt`、`webrtc_stop` 等操作走 HTTP，与 WS 推送通道并行，产生竞态且多一次 TLS 握手。

**方案**：在现有 AppBridge WS 上实现请求/响应信道（类似 JSON-RPC over WS），所有操作型调用全走同一条 WS。WS 未连接时**直接报错，不回退 HTTP**（静默降级掩盖连接问题）。

**消息格式**：
```json
// 前端 → Gateway（Request）
{ "type": "request", "request_id": "uuid", "action": "chat_send", "path": "/api/chat/send", "data": {...} }
// Gateway → 前端（Response）
{ "type": "response", "request_id": "uuid", "data": {...}, "error": null }
```

**关键实现**：

| 层 | 文件 | 职责 |
|---|------|------|
| Rust AppBridge | `app_bridge.rs` | `OutgoingMessage::Request`/`IncomingMessage::Response` + `pending_requests: Arc<Mutex<HashMap<String, oneshot::Sender>>>` + `send_request()` |
| Tauri Command | `commands/gateway.rs` | `gateway_ws_request(action, path?, data?)` — WS 未连接直接 Err |
| Gateway Python | `app_client.py` | `_handle_ws_request()` + `_dispatch_request()` — 直接调进程内函数，不走内部 HTTP |

**Gateway dispatch 逻辑（进程内直接调用，零 HTTP）**：
- `webrtc_stop` → `send_push_to_device(target_pc, "webrtc_stop", data)` via CloudBridge WS
- `chat_send` → `message_repo.add_message()` + `notify_chat_subscribers()`（直接写 DB + 广播 SSE）
- `interrupt` → `agent.interrupt()`（with ImportError graceful fallback）

**前端已迁移的调用**：
- `useWebRtc.ts`：`disconnect()` + `connect()` 的 pre-stop → `gateway_ws_request("webrtc_stop")`
- `services/api.ts`：`sendChatMessage()` → `gateway_ws_request("chat_send")`
- `services/api.ts`：`interruptAgent()` → `gateway_ws_request("interrupt")`

**Rust 生命周期修复**：`Response` 处理时 clone `Arc<Mutex<pending_requests>>`（先 drop RwLockReadGuard），再 `.lock().await.remove()` 赋值给 `let tx` 后 drop MutexGuard，最后 if-let 使用，避免 E0597。

- **Tauri HTTP 请求**：通过 `gateway_get` / `gateway_post` 等命令，URL 来自 Rust 的 `gateway_url.txt`（`{data_dir}/gateway_url.txt`，默认 `https://api.gradievo.com`）
- **前端 WS 推送**：Rust 统一监听 `gateway_push` 事件，无需维护单独的长连接 URL

---

## 二、代码仓库说明

父仓库 `chriswangcq/novaic`（默认分支 `main`，旧代码在 `legacy` 分支），所有服务均为 **git submodule**（`.gitmodules` 已注册 13 个）。

```bash
# Clone 全部
git clone --recurse-submodules git@github.com:chriswangcq/novaic.git
# 已 clone 后初始化
git submodule update --init --recursive
```

| Submodule | GitHub | 用途 |
|---|---|---|
| `novaic-app` | chriswangcq/novaic-app | Tauri 桌面+移动端应用 |
| `novaic-gateway` | chriswangcq/novaic-gateway | 云端 Gateway（API + DB） |
| `novaic-quic-service` | chriswangcq/novaic-quic-service | STUN + Relay（P2P 兜底） |
| `novaic-agent-runtime` | chriswangcq/novaic-agent-runtime | Agent 运行时 |
| `novaic-runtime-orchestrator` | chriswangcq/novaic-runtime-orchestrator | 运行时编排器 |
| `novaic-contracts` | chriswangcq/novaic-contracts | 共享协议/类型定义 |
| `novaic-shared-kernel` | chriswangcq/novaic-shared-kernel | 共享核心库 |
| `novaic-shared-runtime-common` | chriswangcq/novaic-shared-runtime-common | 共享运行时公共库 |
| `novaic-control-plane` | chriswangcq/novaic-control-plane | 控制面板 |
| `novaic-storage-a` | chriswangcq/novaic-storage-a | 存储服务 A |
| `novaic-storage-b` | chriswangcq/novaic-storage-b | 存储服务 B |
| `novaic-tools-server` | chriswangcq/novaic-tools-server | 工具服务 |
| `novaic-mcp-vmuse` | chriswangcq/novaic-mcp-vmuse | MCP VMuse 集成 |
| `novaic-llm-factory` | chriswangcq/novaic-llm-factory | LLM Factory（集中化 LLM 代理） |

### 仓库目录结构（2026-03-14 整理后）

```
new-build-novaic/
├── README.md              # 项目概览
├── HANDOVER.md            # 接手文档（本文件）
├── .gitmodules            # 13 个 submodule 注册
├── .gitignore             # dist/, .pytest_cache/
├── docs/                  # 文档（分类）
│   ├── design/     (36)   # 系统设计/方案
│   ├── device/     (16)   # 设备管理
│   ├── vnc/        (54)   # VNC 连接（历史文档，代码已迁移至 WebRTC）
│   ├── ota/        (12)   # OTA 热更新
│   ├── p2p/        (12)   # P2P 连接
│   ├── research/   (32)   # 技术调研/分析
│   ├── review/     (32)   # 代码审查/报告
│   ├── misc/       (26)   # 其他
│   └── submodules/ (88)   # 各 submodule 文档副本
├── scripts/               # 构建/部署/运维脚本
│   └── submodules/ (58)   # 各 submodule 脚本副本
├── examples/              # 示例项目 (tauri-ios-hello)
└── 13 个 submodule/
```

---

## 三、本地开发

### 环境准备

```bash
# Node
node >= 18, npm >= 9

# Rust
rustup + cargo (stable)

# macOS only
xcode-select --install
```

### 启动前端开发服务（纯 UI 调试，不含 Rust）

```bash
cd novaic-app
npm install
npm run dev           # http://localhost:5173
```

### 启动完整 Tauri 开发模式（含 Rust VmControl）

```bash
cd novaic-app
npm run tauri:dev     # 会同时编译 Rust 并打开 Tauri 窗口
```

> ⚠️ `tauri:dev` 会启动 Vite 开发服务器（port 1420）。如果报 "Port 1420 is already in use"，先 `kill $(lsof -ti:1420)`。

### 注意事项

- **不要**直接用 `npm run tauri build --ci` —— `--ci` 只接受 `true/false`，会报错
- 正确构建命令：`npm run tauri:build -- --bundles app`
- Rust 改动需要重新编译（约 2-3 分钟），纯 TS/React 改动热更新即时生效

---

## 四、构建与发布

### 构建 .app

```bash
cd novaic-app
npm run tauri:build -- --bundles app
# 输出: src-tauri/target/release/bundle/macos/NovAIC.app
```

### 安装到本机

```bash
cp -r novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app /Applications/NovAIC.app
```

### 构建脚本说明

`tauri:build` 脚本会自动：
1. 如果设置了 `NOVAIC_MCP_VMUSE_REPO` 环境变量，同步 MCP vmuse 资源
2. 运行 `setup-dmg-support.sh`（DMG 签名支持）
3. 执行 `env -u CI tauri build`（取消 CI 环境变量避免 `--ci` 错误）

### 移动端构建（Android / iOS）

**前置条件**：
- **Android**：Android Studio、NDK、`ANDROID_HOME` 环境变量；首次需执行 `tauri android init`
- **iOS**：Xcode、Apple Developer 账号；首次需执行 `tauri ios init`

**init 流程**（首次构建前执行一次）：
```bash
cd novaic-app

# Android：生成 gen/android，配置 signing
tauri android init

# iOS：生成 gen/apple，需在 tauri.ios.conf.json 中填写 developmentTeam
tauri ios init
```

**构建与开发**：
```bash
# Android（使用 custom-protocol）
npm run tauri:build:android   # 或 tauri:dev:android

# iOS（不使用 custom-protocol，避免 WKWebView 黑屏）
npm run tauri:build:ios      # 或 tauri:dev:ios
```

> **iOS 与 Android 差异**：iOS 使用 `--no-default-features --features mobile`（**不含** custom-protocol），因 custom-protocol 在 iOS WKWebView 上有已知问题导致黑屏。Android 仍使用 custom-protocol。

---

### iOS 部署流程（完整）

#### 前置条件

| 项目 | 说明 |
|---|---|
| Xcode | 最新稳定版，已安装 iOS 模拟器 |
| Apple Developer | 已加入 Team，ID 配置在 `tauri.ios.conf.json` |
| 真机 | iPhone 通过 USB 连接，已信任电脑 |
| 环境变量 | `.env` 含 `VITE_GATEWAY_URL`（可选，默认 `https://api.gradievo.com`） |

#### 一键构建并安装到真机

```bash
cd novaic-app
./scripts/build-and-install-ios.sh
```

或手动分步：

```bash
# 1. 确保 gen/apple 存在（首次需 tauri ios init）
test -d src-tauri/gen/apple || env -u CI tauri ios init

# 2. 打补丁（修复 Xcode 构建脚本：cd 到项目根、移除 FORCE_COLOR）
bash scripts/patch-ios-xcode.sh

# 3. 构建 debug IPA
cd novaic-app
npm run tauri:build:ios:debug

# 4. 安装到已连接设备
IPA_PATH="src-tauri/gen/apple/build/arm64/NovAIC.ipa"
DEVICE=$(xcrun devicectl list devices 2>/dev/null | awk '/connected/ && !/Simulator/ {for(i=1;i<=NF;i++) if($i~/^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/) {print $i;break}}' | head -1)
xcrun devicectl device install app --device "$DEVICE" "$IPA_PATH"
```

#### 关键脚本说明

| 脚本 | 用途 |
|---|---|
| `scripts/patch-ios-xcode.sh` | 修复 `tauri ios init` 生成的 Xcode 构建脚本：1) 移除 FORCE_COLOR 导致的 arch 参数错误；2) 改用 `run-ios-xcode-script.sh` 从项目根执行 npm |
| `scripts/run-ios-xcode-script.sh` | Xcode 构建阶段调用，`cd` 到项目根后执行 `npm run tauri ios xcode-script`，解决 SRCROOT 路径问题 |
| `scripts/build-and-install-ios.sh` | 完整流程：`tauri:build:ios:debug` + `devicectl install` |

#### 为何不用 `tauri ios run`？

`tauri ios run` 存在已知 bug：`-exportOptionsPlist` 传入相对路径，xcodebuild 在 `gen/apple` 目录执行时找不到临时文件，报错：

```
Couldn't load -exportOptionsPlist The file ".tmpXXXX" couldn't be opened
```

**workaround**：用 `tauri ios build`（构建成功） + `devicectl device install app`（安装到设备）。

#### 配置文件

| 文件 | 用途 |
|---|---|
| `src-tauri/tauri.ios.conf.json` | iOS 平台覆盖：`developmentTeam`、`minimumSystemVersion`、`windows` 覆盖桌面配置 |
| `src-tauri/tauri.conf.json` | 主配置，`identifier` 为 `com.novaic.app` |
| `src-tauri/gen/apple/project.yml` | XcodeGen 配置，含 `DEVELOPMENT_TEAM`、`PRODUCT_BUNDLE_IDENTIFIER` |

#### iOS 黑屏修复（2026-03 饱和修复）

若出现安装后黑屏，已通过以下修复解决：

1. **移除 custom-protocol**：iOS 构建使用 `--features mobile` 而非 `custom-protocol,mobile`
2. **VITE_GATEWAY_URL 兜底**：`src/config/index.ts` 未设置时用 `https://api.gradievo.com`，避免启动抛错
3. **tauri.ios.conf.json**：覆盖 `decorations`、`transparent`、`center` 等桌面配置
4. **Google Fonts**：`display=optional` 减少首屏阻塞

#### iOS 缩放与键盘行为（2026-03-14 原生修复）

- **防缩放**：`index.html` viewport 含 `maximum-scale=1, minimum-scale=1, user-scalable=no, interactive-widget=resizes-content`；`index.css` 含 `touch-action: manipulation`
- **键盘弹出 — 原生层修复**（`src-tauri/gen/apple/Sources/novaic/main.mm`）：
  1. 移除 WKWebView 的键盘通知观察者 → 阻止 iOS 自动滚动页面（Header 不被推）
  2. 注册自定义键盘通知监听 → 获取精确键盘高度 → 通过 `evaluateJavaScript` 注入 CSS 变量 `--keyboard-height`
  3. 每次键盘事件强制 `contentOffset = CGPointZero`
  - **前端配合**：`LayoutContainer.tsx` 移动端容器用 `position: fixed; bottom: var(--keyboard-height, 0px)` 自动适配
  - **为什么不用 JS 方案**：`visualViewport.height` 在 Tauri WKWebView 中移除键盘观察者后不更新；`scrollEnabled=NO` 不能阻止程序化 contentOffset；`interactive-widget=resizes-content` 在 WKWebView 中无效
- **移动端不自动聚焦**：`ChatInput.tsx` 中 `useEffect` 检测 `ontouchstart`，移动端不调用 `.focus()`，避免进入聊天页键盘自动弹出
- **`main.mm` 注意事项**：`ffi::start_app()` 启动 UIKit run loop 且永不返回，所有 `dispatch_after` 必须在它**之前**调用

#### 调试用 Hello World 项目

独立最小项目 `examples/tauri-ios-hello/` 用于验证 Tauri iOS 构建流程，与主应用解耦。

---

## 五、统一部署 CLI

所有部署操作通过根目录 `./deploy` 脚本统一管理：

```bash
# ── 客户端 ──
./deploy frontend [ver]    # 构建前端 + rsync 到 relay OTA (默认 v0.3.0)
./deploy ios               # 构建 IPA + 安装到已连接 iPhone
./deploy desktop           # 构建 macOS .app

# ── 后端服务 (api.gradievo.com) ──
./deploy gateway           # rsync + start.sh 全部重启
./deploy runtime           # rsync + start.sh 全部重启
./deploy orchestrator      # rsync + start.sh 全部重启
./deploy tools             # rsync + start.sh 全部重启
./deploy storage-a         # rsync + start.sh 全部重启
./deploy storage-b         # rsync + start.sh 全部重启
./deploy services          # rsync 全部 + start.sh 重启（推荐）

# ── 基础设施 ──
./deploy relay             # git pull + cargo build + systemctl restart

# ── 运维 ──
./deploy status            # 检查所有服务状态
./deploy logs [svc]        # 查看日志 (gateway|orchestrator|tools|runtime|worker|relay)
./deploy all [ver]         # 部署全部
```

**原理**：`./deploy` **只负责 rsync 同步代码**，进程管理交给服务器端：
- **所有后端服务（含 Gateway）**：`/opt/novaic/start.sh --stop && /opt/novaic/start.sh`（含完整启动参数、端口检测、独立日志、worker pool 分组）
- **Relay**：`systemctl restart novaic-quic-service`

> ⚠️ `restart_gw.sh` 已于 2026-03-22 删除。它只单独重启 Gateway 而不重启其他服务，导致服务间状态不一致（WebRTC 连不上等问题）。**所有重启必须走 `start.sh`。**

---

## 六、云端部署详细说明

> 日常部署推荐使用 `./deploy` CLI（见第五节）。以下为底层细节和首次配置参考。

### Gateway（api.gradievo.com）

### 服务器信息

| 项目 | 值 |
|---|---|
| 域名 | `api.gradievo.com` |
| SSH | `ssh root@api.gradievo.com` |
| 代码路径 | `/opt/novaic/services/novaic-gateway` |
| 数据目录 | `/opt/novaic/data/` |
| 数据库 | `/opt/novaic/data/gateway.db` (SQLite) |

### 部署流程

```bash
# 推荐：使用统一 CLI
./deploy gateway

# 或手动 rsync 部署
cd novaic-gateway && ./scripts/deploy-gateway.sh root@api.gradievo.com
```

### 重启方式

- **正确方式**：`/opt/novaic/start.sh --stop && /opt/novaic/start.sh`（重启全部服务）
- **依赖**：`/opt/novaic/jwt_secret.env` 含 `JWT_SECRET`、`TURN_SECRET`、可选 `RELAY_URL`、可选 `FRONTEND_CDN_URL`（前端 OTA）
- **模板**：`scripts/jwt_secret.env.example`，首次部署时复制并填写

> ⚠️ 旧脚本 `restart_gw.sh` 已删除，不要手动创建。单独重启 Gateway 会导致服务状态不一致。

### Nginx 配置

- 位置：`/etc/nginx/sites-enabled/novaic`（来源：`novaic-gateway/nginx/novaic-cloud.conf`）
- **生产部署**：`novaic-cloud.conf` 含占位符，需替换后部署。运行 `nginx/deploy-nginx.sh` 生成配置，再 scp 到服务器并 reload。若修改了 novaic-cloud.conf（如新增公开路由），需重新部署 nginx 配置
- HTTP(80) → HTTPS(301) 跳转
- HTTPS(443) 代理到 `127.0.0.1:19999`
- **认证方式（2026-03 起）**：Nginx `auth_request` 调用 `/internal/auth/validate`，验证 HS256 JWT，提取 `sub` 作为 `X-User-ID` 注入下游请求
- 客户端伪造的 `X-User-ID` header 在 Nginx 层被剥离（`proxy_set_header X-User-ID ""`）
- CloudBridge WebSocket：`/internal/pc/ws`，超时 3600s，Auth token 通过 `Authorization: Bearer` header 传入
- **前端 OTA**：`/api/config/frontend` 为公开接口（无需 JWT），App 启动时调用，返回 CDN URL；限流 burst=30

### 查看 gateway 日志

```bash
# 实时追踪今天的日志
ssh root@api.gradievo.com 'tail -f /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log'
```

### Gateway 与 Relay 联动（Phase 4）

`relay-request` 需 `RELAY_URL`。在 `jwt_secret.env` 中设置（见 `scripts/jwt_secret.env.example`），或依赖 `restart_gw.sh` 的默认值。前端 OTA 需 `FRONTEND_CDN_URL`（同上，有默认值 `https://relay.gradievo.com/resource/frontend/v0.3.0/`）。

---

### novaic-quic-service（STUN + Relay）

> P2P 直连不可达时的兜底服务。打洞已移除，手机连接 PC 时直接走 relay 建立 QUIC 连接，用户无感知。

### 服务器信息

| 项目 | 值 |
|---|---|
| 域名 | `stun.gradievo.com`、`relay.gradievo.com`（同机部署，解析到 47.243.221.45） |
| SSH | `ssh -p 52222 root@47.243.221.45`（relay 使用 52222 端口） |
| 代码路径 | `/opt/novaic/novaic-quic-service` |
| 二进制 | `/opt/novaic/novaic-quic-service/novaic-quic-service` |
| systemd | `novaic-quic-service.service` |

### 部署流程（标准）

**方式 A：Git 拉取（推荐，relay 服务器已配置 GitHub SSH 公钥）**

```bash
# 1. 本地提交推送
cd novaic-quic-service
git add -A && git commit -m "..." && git push

# 2. 服务器拉取、编译、重启（relay 用 52222 时加 -p 52222）
# 注：需先 stop 再 cp，否则「Text file busy」
ssh -p 52222 root@47.243.221.45 'cd /opt/novaic/novaic-quic-service && git pull origin main && cargo build --release && systemctl stop novaic-quic-service && cp target/release/novaic-quic-service ./ && systemctl start novaic-quic-service'

# 3. 验证
ssh -p 52222 root@47.243.221.45 'systemctl status novaic-quic-service'
```

**方式 B：rsync 推送源码（git 不可用时）**

```bash
cd novaic-quic-service
rsync -avz -e "ssh -p 52222" --exclude target --exclude .git . root@47.243.221.45:/opt/novaic/novaic-quic-service/
ssh -p 52222 root@47.243.221.45 'export PATH="$HOME/.cargo/bin:$PATH" && cd /opt/novaic/novaic-quic-service && cargo build --release && systemctl stop novaic-quic-service && cp target/release/novaic-quic-service ./ && systemctl start novaic-quic-service'
```

**方式 C：deploy 脚本**（需 relay 默认 22 端口）：`./deploy/deploy.sh root@relay.gradievo.com`

### Relay 服务器 GitHub SSH 配置

relay 服务器已安装 git，SSH 公钥已加入 GitHub Deploy Keys。若需重新配置：

1. 在 relay 上生成或查看公钥：`ssh root@relay.gradievo.com 'cat ~/.ssh/id_ed25519.pub'`
2. GitHub → 仓库 novaic-quic-service → Settings → Deploy keys → Add deploy key
3. 粘贴公钥，保存后即可在 relay 上 `git pull`

### 首次部署：申请 TLS 证书

```bash
# 确保 80 端口已放行（云安全组）
ssh root@relay.gradievo.com "bash -s" < novaic-quic-service/deploy/setup-certbot.sh
# 或指定域名：ssh root@relay.gradievo.com "bash -s relay.gradievo.com stun.gradievo.com" < novaic-quic-service/deploy/setup-certbot.sh
```

证书路径：`/etc/letsencrypt/live/relay.gradievo.com/`。自动续期已配置（crontab 每日 3:00 或 certbot.timer），续期成功后自动重启服务。

### 端口与协议

| 服务 | 端口 | 协议 |
|------|------|------|
| STUN | 3478 | UDP |
| Relay | 443 | QUIC (UDP) |
| relay.gradievo.com | 80/443 | HTTP/HTTPS（Nginx 静态，路径 /resource/frontend/，复用 relay 证书） |

### 前端热更新（relay.gradievo.com/resource/frontend/）

> App 启动时请求 Gateway `GET /api/config/frontend` 获取 CDN URL，成功则 `navigate(remote_url)`，失败或超时则使用本地 bundled 前端。Hybrid Local First 方案。桌面+手机均生效。

**OTA 开关**：默认启用（`is_ota_enabled()` 始终返回 `true`）。Release 构建启动时自动请求 Gateway 获取 CDN URL 并 navigate。Dev 模式下跳过。

**OTA 三处同步**：新增或变更 CDN 域名时，需同时修改以下三处，否则会 navigate 失败或 invoke 不可用：

| 位置 | 修改项 |
|------|--------|
| `novaic-app/src/config/index.ts` | `OTA_ORIGINS` 数组 |
| `novaic-app/src-tauri/capabilities/remote-frontend.json` | `remote.urls` |
| `novaic-app/src-tauri/src/setup.rs` | `OTA_ALLOWED_HOSTS` 常量 |

当前允许的 host：`relay.gradievo.com`、`api.gradievo.com`。

**CI 校验**：`scripts/check-ota-sync.sh` 校验三处一致性，已在 `.github/workflows/tauri-ci.yml` 中执行。本地运行：`bash scripts/check-ota-sync.sh`。

**OTA 调试**：浏览器打开 CDN URL 时，`sessionStorage.setItem('novaic_ota_debug', '1')` 后刷新，控制台输出 `[OTA] Debug` 信息。

#### 一键部署

```bash
./deploy all [version]    # 推荐，见第五节
```

#### 前端部署完整流程（三步）

**一、部署前端到 Relay**

```bash
cd novaic-app
VITE_BASE="/resource/frontend/v0.3.0/" npm run build
```

若 relay 使用 **SSH 端口 52222**（relay 已迁移到 47.243.221.45 时）：

```bash
ssh -p 52222 root@47.243.221.45 "mkdir -p /opt/novaic/static/v0.3.0"
rsync -avz --delete -e "ssh -p 52222" dist/ root@47.243.221.45:/opt/novaic/static/v0.3.0/
```

若 relay 使用默认 22 端口：

```bash
./scripts/deploy-frontend.sh root@relay.gradievo.com 0.3.0
```

验证：访问 https://relay.gradievo.com/resource/frontend/v0.3.0/ 应能看到前端页面。

**二、更新 Gateway 配置**

在 `jwt_secret.env` 或 `restart_gw.sh` 中设置：

```bash
export FRONTEND_CDN_URL=https://relay.gradievo.com/resource/frontend/v0.3.0/
export FRONTEND_VERSION=0.3.0
```

重启全部服务：`ssh root@api.gradievo.com 'bash /opt/novaic/start.sh --stop && bash /opt/novaic/start.sh'`

**三、手机端构建**

iOS 一键构建并安装：`./deploy ios`

Android：`npm run tauri:build:android`

详见本文档第四「构建与发布 → 移动端构建」及「iOS 部署流程（完整）」。

---

**Relay 服务器前置配置（首次部署时）**：

```bash
# relay 使用 52222 时加 -p 52222
ssh -p 52222 root@47.243.221.45 "bash -s" < novaic-quic-service/deploy/setup-cnd-frontend-nginx.sh
```

- **静态目录**：`/opt/novaic/static/v{version}/`，URL 路径 `/resource/frontend/v{version}/`
- **Nginx 配置**：`/etc/nginx/conf.d/relay-frontend.conf`（CentOS）或 `sites-available/relay-frontend`（Debian）

**后续热更新**：修改前端 → 执行上述一、二步（版本号按需调整）→ 用户下次启动自动加载新版本。

详见 `docs/design/HOT_UPDATE_DEPLOY_STEPS.md`。

### 本地开发

```bash
cd novaic-quic-service

# 开发（自签名证书，无 RELAY_TLS_* 时自动生成）
cargo run

# 生产（需证书）
RELAY_PORT=443 \
RELAY_TLS_CERT_PATH=/path/to/fullchain.pem \
RELAY_TLS_KEY_PATH=/path/to/privkey.pem \
cargo run
```

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| GATEWAY_URL | https://api.gradievo.com | Relay 鉴权时调用 Gateway validate |
| RELAY_PORT | 443 | Relay 监听端口 |
| STUN_PORT | 3478 | STUN 监听端口 |
| RELAY_TLS_CERT_PATH | - | 生产 TLS 证书 PEM 路径 |
| RELAY_TLS_KEY_PATH | - | 生产 TLS 私钥 PEM 路径 |

### 客户端开发调试

- **跳过 relay 证书校验**（仅本地/测试）：`NOVAIC_RELAY_INSECURE=1`。**严禁生产使用**。
- **覆盖 relay 地址**：`NOVAIC_RELAY_URL=https://your-relay/p2p/relay`，用于自建 relay 或调试。

### 故障排查

| 现象 | 可能原因 |
|------|----------|
| Relay 连接失败 | 检查 RELAY_TLS_CERT_PATH/KEY_PATH、防火墙 443/udp |
| Relay handshake timeout | Relay 需用 `accept_bi()` 接受客户端 stream，不能用 `open_bi()` |
| STUN 无响应 | 检查防火墙 3478/udp、云安全组 |
| 鉴权失败 | Relay 为外部服务，无法访问 Gateway `/internal/`；需用 Gateway `/api/p2p/validate-device` |
| Invalid relay address | p2p 模块需对 hostname 做 DNS 解析，不能直接用 `SocketAddr::parse()` |

### Relay 关键修复（2026-03）

| 问题 | 根因 | 修复位置 |
|------|------|----------|
| Relay handshake timeout | 客户端用 `open_bi()` 发起，服务端误用 `open_bi()` 无法配对 | `relay.rs`：改为 `accept_bi()` |
| Relay 鉴权 401 | `/internal/auth/validate-device` 仅允许 127.0.0.1，relay 为外部服务 | Gateway 新增 `GET /api/p2p/validate-device`；`auth.rs` 调用该接口 |
| Invalid relay address | `SocketAddr::parse()` 只接受 IP:port，不接受 hostname | `novaic-app` p2p 模块：对 hostname 做 DNS 解析 |
| rustls 启动失败 | 需显式安装 ring crypto provider | `main.rs`：`rustls::crypto::ring::default_provider().install_default()` |

### 相关文档

- `docs/design/HOT_UPDATE_DEPLOY_STEPS.md` — 前端热更新部署
- `docs/design/DESIGN-novaic-quic-service.md` — 服务设计
- `docs/design/DESIGN-P2P-UNIFIED.md` — P2P 架构总览

---

## 七、认证体系（自定义 JWT）

### 整体流程

```
用户 → App 登录/注册表单 → POST /auth/login 或 /auth/register
     → Gateway 返回 HS256 JWT（sub = uuid） + refresh_token
     → 存入 localStorage（access_token / refresh_token / user_info）
     → App.tsx 调用 update_cloud_token(jwt) 推送给 Rust
     → Rust gateway_*/CloudBridge 请求携带 Authorization: Bearer <jwt>
     → Nginx auth_request → /internal/auth/validate
          → 成功：提取 sub，设置 X-User-ID 响应头
          → Nginx 将 X-User-ID 注入转发给 Gateway 的请求
     → Gateway FastAPI Depends(get_current_user) 读取 X-User-ID
     → 所有数据库操作携带 user_id 过滤
```

### 关键文件

| 文件 | 用途 |
|---|---|
| `novaic-app/src/App.tsx` | 自定义 `AuthScreen`（邮箱+密码表单），登录态存 localStorage |
| `novaic-app/src/services/auth.ts` | `login/register/logout/getAccessToken()`，token 存 localStorage，55min 自动 refresh |
| `novaic-app/src-tauri/src/main.rs` | 单一入口，setup 内 `#[cfg]` 分支；桌面：Tray、VmControl；`update_cloud_token` 命令 |
| `novaic-app/src-tauri/src/mobile.rs` | 移动端 setup：调用 setup::setup_shared，默认云端 Gateway |
| `novaic-app/src-tauri/src/setup.rs` | 共享 setup：Gateway URL、StorageBackend、P2P 状态统一注入（桌面+移动端） |
| `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | Cloud Bridge：WebSocket 握手读取 token，设置 `Authorization: Bearer` |
| `novaic-gateway/gateway/api/auth.py` | `/auth/login`、`/auth/register`、`/auth/refresh`、`/auth/logout`、`/internal/auth/validate` |
| `novaic-gateway/gateway/db/repositories/user.py` | users / refresh_tokens 表 CRUD |
| `novaic-gateway/gateway/api/deps.py` | `get_current_user(x_user_id: Header)`，缺失返回 401 |
| `novaic-gateway/nginx/novaic-cloud.conf` | `auth_request` 配置，剥离客户端 X-User-ID |

### Token 参数

| 参数 | 值 |
|---|---|
| 签名算法 | HS256 |
| Access Token TTL | 60 分钟（`ACCESS_TOKEN_EXPIRE_MINUTES` 环境变量） |
| Refresh Token TTL | 30 天（轮换式，每次 refresh 旧 token 作废） |
| 前端刷新时机 | 距过期 < 5 分钟时自动调用 `/auth/refresh`；定时每 55 分钟推送最新 token 给 Rust |
| JWT_SECRET 位置 | `/opt/novaic/jwt_secret.env`（不进 git） |

> ⚠️ Clerk 曾被引入（PR: multi-user branch），后因桌面 App 与 Clerk Production origin 限制不兼容而放弃。Clerk 相关代码已全部回滚。

### 多用户数据隔离

- 所有业务表（`agents`、`api_keys`、`config`、`ssh_keys`、`skills` 等）均有 `user_id` 字段
- Repository 层所有查询强制带 `WHERE user_id = ?`，不存在 fallback 到空值
- SSH Key 路径通过 `user_id` hash 隔离：`{DATA_DIR}/.ssh/id_rsa_{user_hash}`
- 历史数据已迁移到用户 `5ac19cc9-40b1-4c87-8cf7-64ceebd45079`（备份：`gateway.db.backup_before_migration`）

---

## 八、关键架构决策与注意点

### ⚠️ `getCachedUser()` 不可放进 useEffect 依赖

`auth.ts` 的 `getCachedUser()` 每次调用返回 **新对象**（`return { user_id, email, display_name }`）。若写成 `useEffect(..., [user])`，**必然触发无限 re-render 循环**并冻结 UI。

**正确做法**：提取稳定的基础类型值作为依赖。
```typescript
// ❌ 错误 — 无限循环
const user = getCachedUser();
useEffect(() => { ... }, [user]);

// ✅ 正确 — string 引用稳定
const userId = getCachedUser()?.user_id ?? null;
useEffect(() => { ... }, [userId]);
```

涉及 hook: `useAgentsFromDB`、`useDevicesFromDB`、`useAgentConfigFromDB`（均已修复）。

### VmControl — VM 状态检测（Scheme A）

**决策**：判断 Linux VM 是否运行，只检查 QMP socket 文件是否存在，不尝试连接。

**原因**：QMP 是单客户端协议，连接会失败且破坏现有连接。

**文件**：`novaic-app/src-tauri/vmcontrol/src/api/routes/vm.rs` — `is_vm_running()`

### SSH Key 路径约定

路径格式：`{DATA_DIR}/.ssh/id_rsa_{user_hash}`（`user_hash` 为 `user_id` 的前 16 位 sha256 hex）

- Gateway 写入：`novaic-gateway/gateway/vm/ssh.py` — `get_private_key_path(user_id)`
- Gateway 获取 key 内容：`get_private_key_for_agent(agent_id)` — 用于 deploy-wait 转发给 vmcontrol
- VmControl 读取：`vm.rs` — 只查这一个路径（`user_id` 经 CloudBridge 从 X-User-ID 传入）

### scrcpy 控制流断线恢复

**问题**：scrcpy TCP 控制连接断开（Broken Pipe）时，VmControl 旧代码只 log 不 break，导致 WebSocket 永远不关闭无法重连。

**修复**：`scrcpy/mod.rs` 控制任务 Text 分支加 `break`，WebSocket 关闭触发前端 2s 后自动重连。

### WebRTC Scrcpy 多客户端 Broadcaster 架构（2026-03-15）

**目标**：让多个客户端（桌面 + 手机）同时连接观看/操控同一台 Android 设备。

**架构**：
- **ScrcpyBroadcaster**：每个 `device_serial` 一个 broadcaster，持有唯一的 scrcpy TCP 连接
- **tokio::sync::broadcast**：broadcaster 从 scrcpy TCP 读帧 → broadcast 到所有订阅者
- **session_id**：每个客户端连接获得唯一 UUID session_id，stop 时只断自己
- **keyframe_cache**：独立 `Arc<Mutex<(Option<Bytes>, Option<Bytes>)>>`，分别存 codec config (SPS/PPS) 和 last IDR
- **alive flag**：broadcaster pump 结束时标记 `alive=false`，新连接检测到死 broadcaster 会重建

**关键文件**：
- `api/routes/webrtc_scrcpy.rs`：`ScrcpyBroadcaster`、`subscriber_pump`、`detect_nalu_type`
- `WebRtcScrcpyView.tsx`：前端 WebRTC 组件，存 `sessionIdRef` 用于精确 stop

**三个关键 bug 修复**：

| Bug | 症状 | 修复 |
|-----|------|------|
| keyframe 在 ICE 连接前 `write_sample` | DTLS 未协商完，帧被丢弃 → 黑屏 | subscriber_pump 轮询等待 `peer_connection.connection_state() == Connected` 再写 |
| SPS/PPS 和 IDR 用同一缓存字段 | IDR 覆盖 SPS/PPS → 解码器没有 codec config → 黑屏 | 拆为 `(codec_config, last_idr)` 分别缓存，按顺序发送 |
| broadcaster pump 内双重锁 `BROADCASTERS → broadcaster` | 死锁导致帧停推 | keyframe cache 改为独立 `Arc<Mutex>` |

**H.264 NALU 检测**：`detect_nalu_type()` 扫描 Annex B start codes，分类返回 `CodecConfig`（SPS=7/PPS=8）、`Idr`（type=5）、`Other`。

### WebRTC HD/LVM 连接修复与操控实现（2026-03-15）

**问题**：HD 和 Linux VM 的 WebRTC 连接完全无法建立，点击展开无任何反应。Android 正常。

**根因与修复**：

| # | 问题 | 根因 | 修复 | 文件 |
|---|------|------|------|------|
| 1 | **连接不发起** | `useWebRtc.ts` 的 `connectingRef` 在 HMR/re-mount 时未重置，卡死为 `true`，`connect()` 被防重入 guard 永远跳过 | useEffect 开头加 `connectingRef.current = false` | `useWebRtc.ts` |
| 2 | **LVM 颜色失真** | VNC SetPixelFormat red_shift=16 → 字节序 [B,G,R,X]，但 `rgba_to_yuv420` 按 [R,G,B] 读取，R/B 互换 | 交换 `rgba[idx]` 和 `rgba[idx+2]` | `webrtc_vm.rs` |
| 3 | **HD/LVM 无操控** | 前端发 `type:'mouse'` + 归一化坐标，后端期望 `type:'mousedown'` + 像素坐标 | 统一消息格式，使用 RFB button_mask | `WebRtcScrcpyView.tsx` |
| 4 | **LVM 操控未实现** | control_task 收到消息直接丢弃（TODO） | 拆分 VNC socket 读写，control task 通过 mpsc channel 发 RFB PointerEvent/KeyEvent | `webrtc_vm.rs` |
| 5 | **坐标偏移** | 视频 `object-contain` 有黑边，坐标计算未排除 letterbox/pillarbox 偏移 | 计算实际渲染区域，扣除黑边偏移 | `WebRtcScrcpyView.tsx` |

**LVM 操控架构**（消除 Mutex 竞争）：

```
Control Task ──(mpsc channel 零等待)──► Capture Loop ──(独占 VNC WriteHalf)──► VNC socket
                                           │
                                        每帧开始时 try_recv 批量 drain 控制消息
                                        然后发 FramebufferUpdateRequest + 读帧
```

- `build_rfb_message()`: 纯 CPU 函数，JSON → RFB 字节（PointerEvent/KeyEvent/Scroll）
- capture loop 独占 VNC write，先 drain 控制消息再发 FBUR，零锁竞争

**前端鼠标操作**：
- `buttonMaskRef` (bitmask) 跟踪所有按键状态：bit0=left, bit1=middle, bit2=right
- `jsButtonToRfbBit()` 映射 JS `e.button` → RFB button_mask bit
- 每个 mousedown/mouseup 更新 mask，每个事件发送完整 mask（RFB 协议要求）
- `handleContextMenu` 屏蔽右键菜单（HD/Linux 需要右键）
- `handleMouseLeave` 清零所有按键
- mousemove 节流到 ~30fps

**性能优化**：
- 帧率 15fps → 30fps
- 双缓冲 `std::mem::swap` 消除每帧 `full_fb.clone()` 8MB 拷贝

**已知限制**：
- **openh264 软编码延迟**：1080p 单帧 30-80ms，是操控延迟的主要来源
- **已知限制**：openh264 软编码 1080p 单帧 30-80ms，是操控延迟的主要来源

### macOS 输入注入架构修复（2026-03-16）

**问题**：HD（Host Desktop）模式下，从手机端发送键盘输入或剪贴板内容会导致 App 崩溃。

**根因**：`enigo` 库的 `key()` 方法内部调用 macOS `TSMGetInputSourceProperty`（Text Services Manager），此 API **必须在主线程（main dispatch queue）调用**。但 input-handler 运行在工作线程，导致 `dispatch_assert_queue_fail` → SIGTRAP 崩溃。类似地，`arboard` 库的 `Clipboard::new()` 访问 `NSPasteboard`，也有主线程限制。

**修复方案**：

| 功能 | 旧方案（崩溃） | 新方案（线程安全） |
|------|---------------|-------------------|
| 键盘注入 | `enigo::Keyboard::key()` → TSMGetInputSourceProperty | `CGEvent::new_keyboard_event()` + `event.post(HID)` |
| 剪贴板设置 | `arboard::Clipboard::set_text()` → NSPasteboard | `pbcopy` 命令（子进程，任意线程） |
| 剪贴板读取 | `arboard::Clipboard::get_text()` → NSPasteboard | `pbpaste` 命令 |

**CGEvent 键盘**：完整映射了 macOS virtual keycodes（0x00-0x7E），覆盖所有字母、数字、功能键、修饰键、方向键。对于没有直接映射的 Unicode 字符，使用 `CGEvent.set_string_from_utf16_unchecked()` 注入。

**新增依赖**：`core-graphics = "0.24"` (macOS only, `[target.'cfg(target_os = "macos")'.dependencies]`)

**关键文件**：
- `vmcontrol/src/input/handler.rs`：`cg_key_event()`, `cg_type_string()`, `enigo_key_to_cg_keycode()`, `char_to_keycode()`
- `vmcontrol/src/input/clipboard.rs`：`set_text_clipboard()` 使用 pbcopy, `get_local_clipboard()` 使用 pbpaste
- `vmcontrol/Cargo.toml`：新增 `core-graphics` 条件依赖

### 虚拟物理键盘 VirtualKeyboard（2026-03-16）

手机端原来的"键盘"按钮会弹出系统输入法，但系统输入法无法发送功能键（F1-F12）、修饰键组合（Ctrl+C）等。

**新实现**：`VirtualKeyboard.tsx` 虚拟物理键盘，还原完整 PC 键盘布局：

```
┌─────────────────────────────────────────────┐
│ ‹ │ Esc F1 F2 F3 F4 F5 F6 ... F12 │ ›   │ ← Fn 行，可左右滚动
├─────────────────────────────────────────────┤
│ !  @  #  $  %  ^  &  *  (  )   ←          │ ← 数字行 + shift 提示 + ⌫
│ 1  2  3  4  5  6  7  8  9  0               │
├─────────────────────────────────────────────┤
│ Q  W  E  R  T  Y  U  I  O  P              │ ← QWERTY 行
├─────────────────────────────────────────────┤
│ A  S  D  F  G  H  J  K  L  ↵              │ ← ASDF 行 + Enter
├─────────────────────────────────────────────┤
│ Shift  Z  X  C  V  B  N  M  Shift         │ ← ZXCV 行
├─────────────────────────────────────────────┤
│ Ctrl  Alt  ⌘  │  Space  │ ← ↓ ↑ →         │ ← 底部行
└─────────────────────────────────────────────┘
```

**修饰键 toggle 模式**：Shift/Ctrl/Alt/⌘ 点按后高亮激活，按完其他键后自动释放（单次使用模式），类似 iOS AssistiveTouch。

**深色毛玻璃背景**：`rgba(13,13,20,0.92)` + `backdrop-filter: blur(20px)`，与设计图一致。

**关键文件**：
- `useWebRtc.ts`: WebRTC 连接 hook，`connectingRef` 重置修复
- `WebRtcScrcpyView.tsx`: 统一鼠标/键盘事件处理，object-contain 坐标修正
- `api/routes/webrtc_vm.rs`: VNC socket 拆分读写，RFB 控制消息注入，颜色修正
- `api/routes/webrtc_hd.rs`: HD 截屏 + openh264 + InputInjector（操控已实现）

### 统一设备操控台 DeviceConsole（2026-03-16）

**背景**：统一设备操控为浮层式操控台 `DeviceConsole`，全链路走 WebRTC。

#### 组件体系

```
src/components/Console/
├── index.ts             — 统一导出
├── types.ts             — 类型定义（DeviceType, ConsoleViewMode, ConsoleInputMode 等）
├── DeviceConsole.tsx     — ★ 主组件（fixed 浮层 z-[9999]）
├── ConsoleToolbar.tsx    — 固定底部工具栏（不覆盖画面，有自己的空间）
├── VirtualKeyboard.tsx  — ★ 虚拟物理键盘（完整 QWERTY + Fn + 修饰键 toggle）
├── PipMinimap.tsx       — PiP 缩略图（缩放时角落显示全景 + 蓝色视口矩形）
├── RemoteCursor.tsx     — 远程光标（服务端推送坐标，前端渲染）
├── CursorMagnifier.tsx  — 放大镜（precision mode）
└── SoftwareCursor.tsx   — 软件光标（PC 端箭头 / 手机端红点）

src/hooks/
├── useViewTransform.ts — 缩放/平移管理 Hook（pinch + 滚轮 + 鼠标拖动）
├── useWebRtc.ts        — WebRTC PeerConnection + DataChannel
└── useRemoteInput.ts   — 鼠标/键盘/触摸 → DataChannel 序列化
```

#### 协议与信令

> 信令路径详见第一节「远程桌面架构」表格。所有设备类型统一通过 WebRTC + DataChannel 连接。

#### 接入点

| 入口文件 | 触发方式 | 改动说明 |
|:---|:---|:---|
| `DeviceFloatingPanel.tsx` | overlay div `onDoubleClick` | 替换了旧的 `expand() + setOperating(true)` 逻辑；展开工具栏的"操控台"按钮也可触发 |
| `PcClientDeviceList.tsx` | MousePointer2 按钮 | 新增操控台按钮；Eye 按钮保留做内联 WebRTC 预览 |
| `DeviceSidebar.tsx` | "显示"按钮 | 替换旧的 `DeviceDisplayModal`（已删除） |
| `DeviceManagerPage.tsx` | 右面板"→ 打开操控台"链接 | 内联预览保留 + DeviceConsole 叠加 |

#### 两段式布局

```
┌─────────────────────────────┐
│                             │
│      画面区 (flex-1)         │ ← video + transform + cursor
│                             │
├─────────────────────────────┤
│  工具栏 (固定 52px)          │ ← DeviceInfo | 模式 | 按钮
│  状态行 (18px, optional)     │ ← 分辨率 / fps / 延迟 / 码率
└─────────────────────────────┘
```

**工具栏不浮在画面上方**，有独立的固定空间。

#### Adjust ↔ Fixed 模式

| 模式 | 功能 | 视觉反馈 |
|:---|:---|:---|
| **Fixed (操控中)** | 鼠标/键盘/触摸事件发送到远程 | indigo 发光边框、光标隐藏 |
| **Adjust (缩放调整)** | 滚轮缩放 + 鼠标拖动平移 + 双指 pinch | 琥珀色提示条 "缩放调整中" |

- ESC 键：Fixed → Adjust；再按 ESC → 关闭操控台
- 切换按钮在工具栏中间区域（PC 和手机都显示）

#### 工具栏功能

| 功能 | PC 端 | 手机端 |
|:---|:---|:---|
| 模式切换（操控/缩放） | ✅ | ✅ |
| 输入模式（鼠标/Trackpad/Touch/View） | 显示"鼠标操控"badge | 三选一切换 |
| 快捷键菜单 | ✅ Linux 7项 / macOS 3项 | ✅ |
| Android 导航键 | ✅ Back/Home/Recent | ✅ |
| 虚拟键盘 | ✅ VirtualKeyboard（完整 QWERTY） | ✅ |
| 剪贴板发送 | ✅ 文本框 + 发送 + 自动 Ctrl+V 粘贴 | ✅ |
| 刷新画面 (keyframe) | ✅ | ✅ |
| 截图 (下载 PNG) | ✅ | ✅ |
| 全屏 | ✅ | ✅ |
| 状态行 | 分辨率/fps/延迟/码率/编码器 | 同左 |

#### ⚠️ 关键实现注意事项

1. **containerRef 挂载**：`useRemoteInput` 内部创建 `containerRef = useRef(null)`，其 useEffect 依赖 `containerRef.current`。DeviceConsole 通过 ref callback 同步赋值，并用 `const [mounted, setMounted] = useState(false) + useEffect(() => setMounted(true), [])` 强制二次 render，否则 hook 内部 effect 拿不到 DOM 元素，输入事件不会绑定。

2. **不要用 forceUpdate 在 ref callback 里**：会导致无限循环（inline ref function 每次 render 新建 → React cleanup+re-call → setState → re-render → 循环）。

3. **onPanStart 闭包陷阱**：`useCallback([viewMode, transform])` 依赖 transform，滚轮缩放后 transform 频繁变化导致 onPanStart 重建，useEffect 重新绑定事件。解决：`setTransform(prev => {...})` 读取最新值，依赖只保留 `[viewMode]`。

4. **overlay div 的 onDoubleClick**：`DeviceFloatingPanel.tsx` 有一个覆盖在画面上的透明 div（z-20），原来的 `onDoubleClick` 直接调用 `expand() + setOperating(true)` 走旧路径。必须改这里，而非 handleClick 函数。

#### 关键文件

| 文件 | 用途 |
|---|---|
| `Console/DeviceConsole.tsx` | 主组件：WebRTC + 输入 + 缩放 + 工具栏整合 |
| `Console/ConsoleToolbar.tsx` | 工具栏：模式切换、快捷键、剪贴板、导航键 |
| `Console/VirtualKeyboard.tsx` | 虚拟物理键盘组件 |
| `Console/PipMinimap.tsx` | PiP 缩略图 |
| `Console/SoftwareCursor.tsx` | 软件光标 |
| `Console/types.ts` | 类型定义 |
| `hooks/useViewTransform.ts` | 缩放/平移（pinch + wheel + drag） |
| `hooks/useWebRtc.ts` | WebRTC 连接管理 |
| `hooks/useRemoteInput.ts` | 输入事件 → DataChannel 序列化 |

> `start_device` 允许状态：`READY` / `STOPPED` / `ERROR`（ERROR 状态可以重试启动）；`stop_device` 无状态门控，无论 DB 状态如何都尝试停止。**文件**：`novaic-gateway/gateway/api/devices.py`

### CloudBridge — 本地与云端通信

Tauri App 与云端 Gateway 通过 WebSocket (`/internal/pc/ws`) 保持长连接，所有 VM 操作从 Gateway 发出，经 CloudBridge 转发给本地 VmControl，再由 VmControl 操作 QEMU/ADB。

- **认证**：WebSocket 握手时在 `Authorization: Bearer <token>` header 里携带 JWT
- **token 动态刷新**：Cloud Bridge 每次重连前从 `Arc<RwLock<String>>` 读取最新 token
- **Tauri HTTP 客户端必须加 `.no_proxy()`**，否则会走系统代理失败
- **所有 gateway_* Tauri 命令**（`gateway_get/post/patch/put/delete`）使用 `cloud_token.read().await.clone()` 获取 JWT，注意必须用 `.await`（不能用 `blocking_read()`，否则在 Tokio async 上下文中 panic）

### VM 准备 API（2026-03 迁移至 vmcontrol）

环境检查、镜像检查/下载、部署等待已迁入 vmcontrol，前端统一走 Gateway，不再用 Tauri invoke：

| 能力 | 前端调用 | Gateway 转发 | vmcontrol 路由 |
|---|---|---|---|
| 环境检查 | `gateway_get('/api/vm/environment')` | → Cloud Bridge | `GET /api/vm/environment` |
| 镜像检查 | `gateway_get('/api/vm/cloud-image/check?os_type=&os_version=')` | → Cloud Bridge | `GET /api/vm/cloud-image/check` |
| 镜像下载 | `gateway_post('/api/vm/cloud-image/download', body)` | → Cloud Bridge | `POST /api/vm/cloud-image/download` |
| 部署等待 | `gateway_post('/api/vm/deploy-wait', {agent_id, ssh_port})` | 获取 private_key 后转发 | `POST /api/vm/deploy-wait` |

- **deploy-wait**：Gateway 从 `get_private_key_for_agent(agent_id)` 获取 SSH 私钥，在请求体中传给 vmcontrol
- **vmcontrol 路由**：`vmcontrol/src/api/routes/vm_prep.rs`

### 远程桌面架构详细（WebRTC 代码流程）

**信令流程**：
```
前端 useWebRtc.ts
  → createOffer()
  → invoke('gateway_post', { path: '/api/vmcontrol/vm/webrtc/start', body: { sdp_offer, vm_id } })
  → VmControl api/routes/webrtc_vm.rs → create peer + broadcaster
  → SDP Answer 返回 → setRemoteDescription()
  → H.264 video stream via DTLS-SRTP → <video> 标签
  → DataChannel 双向传输键盘/鼠标输入
```

**Tauri Rust 层**（清理后仅保留 7 个 commands 模块）：

```
src-tauri/src/
├── lib.rs              # Tauri Builder + 20 个命令注册 + VmControl 启动
├── setup.rs            # 共享状态初始化 + 前端 OTA 热更新（spawn_frontend_ota_task）
├── p2p_state.rs        # P2P 启动状态（41 行，替代旧 755 行 vnc_proxy.rs）
├── commands/
│   ├── gateway.rs      # ★ gateway_get/post/patch/put/delete（所有后端调用的唯一通道）
│   ├── config.rs       # Gateway URL 管理
│   ├── auth.rs         # Cloud token 更新
│   ├── app_instance.rs # App 实例身份查询
│   ├── file.rs         # 文件下载/打开
│   └── secure_storage.rs # 安全存储
├── state/vmcontrol.rs  # VmControlEmbedded 嵌入式 HTTP 服务
└── (core/, platform/)  # 启动引导 + 平台差异
```

**VmControl WebRTC Engine**（`vmcontrol/src/webrtc/`）：

| 文件 | 职责 |
|------|------|
| `broadcaster.rs` | WebRTC 广播器，管理 peer connections |
| `peer.rs` | 单个 peer connection（ICE + DTLS + SRTP + DataChannel） |
| `encoder.rs` | 视频编码管理器 |
| `vt_encoder.rs` | macOS VideoToolbox H.264 硬编码 |
| `ffmpeg_encoder.rs` | FFmpeg 软编码（fallback） |
| `video_qos.rs` | 自适应码率/帧率 |
| `h264.rs` | H.264 Annex B NALU 解析与处理 |
| `cursor.rs` | 远程光标数据处理 |
| `audio_capture.rs` | 音频采集（预留） |

**已删除的旧模块**（2026-03-19）：
- `vnc_proxy.rs` (755行) — P2P QUIC 隧道 + Scrcpy WS 代理
- `commands/vnc_bridge.rs` — VNC IPC 桥接
- `commands/vnc_stream.rs` — VNC IPC 流
- `commands/vnc_urls.rs` — VNC/Scrcpy 代理 URL
- `commands/webrtc_scrcpy.rs` — WebRTC scrcpy IPC
- `commands/host_desktop.rs` — Host Desktop IPC
- 前端 14 个 VNC 相关文件（services/hooks/types/components）

---

## 九、前端关键文件

> 前端采用 **Render / Business / DB 三层架构**（详见 `novaic-app/FRONTEND_ARCHITECTURE.md`）。

### 应用启动与 Agent 选择流程

1. **登录**：`auth.ts` 存 token → `App.tsx` 调用 `pushToken()` → `invoke(update_cloud_token)` 推给 Rust → 成功后 `agentService.initialize()`（pushToken 失败则 3s 轮询重试）
2. **恢复 Agent**：从 `prefsRepo.getSelectedAgent()` 或 localStorage 恢复上次选中的 agentId
3. **选择 Agent**：`AgentService.selectAgent(agentId)` → store 写入 + prefs → 监听 `gateway_push` (User 维度) 不断开 → `switchAgent(agentId)` 并行 load 消息/日志 + `modelService.loadForAgent`
4. **登出**：`getSyncService().disconnect()` 停止派发事件，`resetServices()` 清空 Service 单例

### DB 层 `src/db/`（DB 驱动渲染）

> 文件清单见 `src/db/` 目录，schema 与版本号见 `src/db/index.ts`。

- **原则**：IndexedDB 为单一事实来源，UI 通过 `*Subscription.ts` 订阅响应变更
- **数据流**：`repo.put*()` → `notify*Change()` → `use*FromDB` 回调 → `refetch()` 从 DB 读 → 渲染
- **注意**：DB 按 `userId` 隔离，表名 `novaic_local_{userId}`

### Gateway 子层 `src/gateway/`

> WS Push 事件监听（`sse.ts` 已重构为 PushManager）、Token 注入（`auth.ts`）

### Business 层 `src/application/`

> 详见 `FRONTEND_ARCHITECTURE.md`，文件清单见 `src/application/` 目录。

- **核心 Services**：`messageService`（消息生命周期）、`logService`（日志）、`syncService`（WS 推送整合 + delta sync）、`agentService`（Agent CRUD + VM setup）、`modelService`（模型配置）
- **状态**：`store.ts`（Zustand 全局状态）、`*PaginationStore`（分页）、`logFilterStore`（日志过滤）
- **⚠️ 注意**：日志/消息等 WS 推送事件属于 User 维度，接收后需匹配当前选中的 agentId

### Render 层 `src/components/` 与 `src/hooks/`

> DB 驱动 hooks 见 `src/hooks/use*FromDB.ts`，组合 hooks 见 `src/components/hooks/`。

- `useAgentConfigFromDB.ts`：**Agent 配置 SWR hook**，UI 层唯一数据源

### VM Setup 服务

| 文件 | 用途 |
|---|---|
| `src/services/setup.ts` | 环境检查、镜像检查/下载、VM 创建、部署等待（均通过 gateway_get/post 调用 Gateway） |
| `src/components/Setup/EnvironmentCheck.tsx` | 环境检查 UI（调用 `gateway_get('/api/vm/environment')`） |

### 远程桌面服务（WebRTC 统一）

| 文件 | 用途 |
|---|---|
| `src/hooks/useWebRtc.ts` (17KB) | ★ 统一 WebRTC 连接管理（PeerConnection + DataChannel + 自动重连） |
| `src/hooks/useRemoteInput.ts` (35KB) | 远程输入采集（鼠标/键盘/触摸 → DataChannel 序列化） |
| `src/hooks/useViewTransform.ts` | 视图缩放/平移管理（pinch + 滚轮 + 拖动） |
| `src/components/Visual/WebRtcScrcpyView.tsx` (17KB) | 统一 WebRTC 视图组件（VM + Android + HD） |
| `src/components/Visual/DeviceVNCView.tsx` | 设备显示容器（名字遗留，内部全 WebRTC） |


> 信令路径详见第一节「远程桌面架构」表格。所有信令通过 `invoke('gateway_post', ...)` 中转。

### 前端布局与交互

> 详细布局参数见各组件文件顶部常量，以下仅记录关键设计决策。

#### 核心布局

- **ChatPanel**：`MessageList` + 展开式 `ExecutionLog`（可拖拽高度）+ `ChatInput`；右上角 `DeviceFloatingPanel` 浮层
- **DeviceFloatingPanel**：preview/expanded/operating 三态，参数集中在 `FLOATING_PANEL_LAYOUT` 常量（见 `DeviceFloatingPanel.tsx`）
- **LayoutContainer**：PC 三栏（PrimaryNav | AgentDrawer | Main）/ 手机 narrowPage 单栏切换（见 `LayoutContainer.tsx`）
- **Devices tab**：PC Client 列表 → 设备卡片 + 内联 WebRTC 展开（见 `PcClientDeviceList.tsx`）

#### 关键设计决策

- **currentAgentId 隔离**：Chats 用 `currentAgentId`（Zustand），Agents 用 `configAgentId`（local state），Skills 用 `selectedSkillId`（local state）。切换 tab 不互相干扰
- **模型选择**：在 Agent Tools 中配置，ChatInput 不含模型选择器。`modelService.setModel(agentId, compositeId)`
- **Skills tab**：从 Settings 独立为主导航 tab，懒加载（见 `AgentDrawer.tsx`）
- **Header**：`...` 按钮替代原 Settings 图标，左右循环切换 Agent


## 十、前端实现细节

#### Tauri 窗口拖拽区

`data-tauri-drag-region` 用于无边框窗口拖动，已加在：

| 组件 | 位置 |
|---|---|
| PrimaryNav | 红绿灯区、Logo 区、空白区 |
| AgentDrawer | Agents/Devices 标题栏 |
| Header | 左右占位 div |
| DeviceManagerPage | 标题栏 |
| SettingsModal | 标题栏 |
| NarrowHeader | 整行（macOS 58px / 手机 58px + safe-area-inset-top） |

#### Header 回调

- **onHeaderMore**：右上角 `...` 点击，由 App 传入，可打开设置/更多菜单
- **onToggleDrawer**：切换 AgentDrawer 展开/收起
- **onBackToSidebar**：手机式下返回第二栏

#### prefsRepo 偏好键

| 键 | 用途 |
|---|---|
| `selectedAgent` | 当前选中的 Agent ID |
| `selectedModel` | 当前模型 composite（`api_key_id:model_id`） |

> 消息与日志的 delta 游标均从 DB 派生（`getLastSyncTime` / `getMaxLogId`），不存 prefs。

#### 本地 DB 缓存清空

- **入口**：Settings → Clear Cache →「清空本地 DB 缓存」
- **作用**：删除 IndexedDB `novaic_local_{userId}`，清空消息、日志、偏好、附件缓存
- **后续**：刷新页面后从服务端重新拉取

#### Agent 创建（含 VM 初始化）

- **CreateAgentModal**：创建时可选 `modelId`（composite 格式）
- **agentService.create**：`create(data, modelId?)`，创建后调用 `gateway.setAgentModel` 设置模型
- **VM 初始化流程**（`setup.ts`、`OnboardingFlow.tsx`）：
  1. 环境检查：`gateway_get('/api/vm/environment')`
  2. 镜像检查/下载：`gateway_get/post` → `/api/vm/cloud-image/check`、`/api/vm/cloud-image/download`
  3. VM 创建：`gateway_post('/api/vm/setup', ...)` → vmcontrol
  4. 部署等待：`gateway_post('/api/vm/deploy-wait', {agent_id, ssh_port})` → vmcontrol（Gateway 注入 private_key）

### 多用户相关表字段

所有业务数据表均含 `user_id TEXT NOT NULL DEFAULT ''` 字段（schema v44+ 迁移后不再有空值）。

### execution_logs 的 subagent_id 历史遗留

旧日志的 `subagent_id = 'main'`（DB default），新日志为 `'main-{agent_id[:8]}'`。  
前端 `groupLogsBySubagent` 会把两者分到不同 key，`sortedCapsuleIds` 逻辑会跳过 legacy `'main'` 避免重复显示。

---

## 十一、实时推送事件（WS Push）

### 架构（2026-03-22 SSE→WS 完成）

- **前端 SSE 已完全删除**：`GET /api/user/chat/stream` 和 `GET /api/user/logs/stream` 两个端点已移除
- **所有前端实时事件走 AppBridge WS**：`app_client.push_to_user()` → Rust `gateway_push` Tauri event
- **前端**：登录后 `connectUserStream()` 监听 `gateway_push` 事件；`switchAgent(agentId)` 仅 load，不断连
- **Worker SSE（`gateway/sse/broadcaster.py`）保留**：这是 Gateway→Worker 进程间通信，不是前端通道

### 文件变更

- `gateway/sse_state.py` → **`gateway/push_state.py`**（已重命名全部 import）
- `push_state.py` 只包含 3 个公开函数：`notify_chat_subscribers`、`notify_log_subscribers`、`broadcast_subagent_update`
- 不再有 `asyncio.Queue`、`register/unregister_*_subscriber` 等 SSE queue 机制

### WS Push 事件（gateway_push payload）

| event | data 关键字段 | 说明 |
|---|---|---|
| `chat_message` | `type`, `agent_id`, `content` | 聊天消息推送 |
| `logs_updated` | `event`, `agent_id`, `log_id` | 日志通知（轻量通知，前端 GET 拉取） |
| `config_updated` | `scope` (settings/default_model/agent_model) | 配置变更同步（新增） |

### Chat 消息类型

| type | 说明 |
|---|---|
| `AGENT_REPLY` / `USER_MESSAGE` | 文字消息 |
| `AGENT_ASK` | Agent 提问 |
| `AGENT_NOTIFY` | Agent 通知 |
| `STATUS_UPDATE` | 消息已读状态 |
| `AGENT_METADATA_UPDATED` | Agent 元数据变更 |
| `DEVICE_METADATA_UPDATED` | 设备元数据变更 |

### Log 事件子类型（`data.event`）

| event | 说明 |
|---|---|
| `log_entry` | 单条新日志 |
| `log_batch` | 批量日志 |
| `logs_updated` | 有新日志通知 |
| `subagent_update` | SubAgent 生命周期变更 |

---

## 十二、常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| LVM 启动失败（设备状态 `error`） | DB 状态为 `error` 被 `start_device` 拒绝 | 已修复：`error` 状态允许重试启动 |
| VM 状态检测不准确 | QMP 单客户端限制 / 内存状态丢失 | Scheme A：只检查 socket 文件存在性 |
| scrcpy 操作模式无响应（Broken Pipe 刷屏） | 控制 TCP 连接断了但 task 不退出 | 已修复：write 失败后 break，触发重连 |
| AVD 停机失败 | DB `device_serial` 为空 | 已修复：从 live 设备列表动态解析 serial |
| WebRTC 多端同连被互踢/崩溃报警 | `stop_peers` 疯狂杀同设备连接，且没启 `UDPMux` 致 UDP 端口逐渐泄漏枯竭 | 已修复：移除 aggressive 强杀，开启 `UDPMuxDefault` 复用本地单一 UDP 端口并设置候选收集超时丢弃 |
| Port 1420 已占用 | 上次 tauri:dev 未退出 | `kill $(lsof -ti:1420)` |
| `npm run tauri build --ci` 报错 | `--ci` 只接受 true/false | 改用 `npm run tauri:build -- --bundles app` |

| CloudBridge 500 / auth validate 500 | gateway 进程没有 `JWT_SECRET` 环境变量 | 用 `bash /opt/novaic/restart_gw.sh` 而非直接 nohup 启动 |
| App 一直显示 "Connecting..." | Rust `initialize()` 在 JWT 推送前执行 | `App.tsx` 已修复：`await pushToken()` 后再调 `initialize()` |
| Rust panic "Cannot block current thread" | 在 async fn 里用了 `blocking_read()` | 改为 `token.read().await.clone()` |
| Gateway 无响应 / 注册登录 500 | `UserRepository` 写操作未用 `transaction()` 包裹，导致事务悬挂、写锁永不释放 | 已修复（`user.py`）：所有 INSERT/UPDATE/DELETE 改为 `with db.transaction("global")` |
| Gateway 无响应（重启后恢复） | 强制 kill gateway 后 WAL/SHM 文件损坏，新进程被旧锁卡住 | `rm -f /opt/novaic/data/gateway.db-wal /opt/novaic/data/gateway.db-shm` 后再 `bash /opt/novaic/restart_gw.sh` |
| Gateway 注册/登录 500（写锁悬挂） | `UserRepository` 写操作缺少 `db.transaction()` 包裹，INSERT 后事务未提交，写锁永不释放 | 已修复（`user.py`）：所有写操作改为 `with db.transaction("global")` |
| 数据迁移后数据丢失 | 在 gateway 有未提交事务时执行了 `PRAGMA wal_checkpoint(TRUNCATE)`，把未提交数据截断 | **禁止**在 gateway 运行时执行 `wal_checkpoint(TRUNCATE)`；正常迁移直接用 `BEGIN/COMMIT` 即可 |
| 本地 DB 缓存异常 | IndexedDB 数据损坏或需强制刷新 | Settings → Clear Cache → 清空本地 DB 缓存，然后刷新页面 |
| **Device tab 点击卡死 / UI 全面冻结** | `getCachedUser()` 每次返回新对象，放进 `useEffect([user])` 导致无限 re-render 循环 | 已修复：`useDevicesFromDB`/`useAgentsFromDB`/`useAgentConfigFromDB` 全部改为 `const userId = getCachedUser()?.user_id ?? null` 用 `string` 做依赖 |
| `...` 按钮（MoreVertical）点不开 | 同上，无限循环占满主线程导致 UI 无响应 | 同上 |
| **宽屏模式消息不可见（能复制但看不到）** | 两个叠加原因：① `opacity-0`/`isReady` timer 在早期推送同步期间被反复取消；② `h-full` 在 flex-column 父元素无明确 height 时解析为 0 | 已修复：彻底移除 opacity-0 模式，MessageList 改用 `flex-1 min-h-0` 替代 `h-full` |
| LLM think 失败（429 / engine_overloaded） | Moonshot 等 API 限流或过载 | 间歇性，非 context 问题；建议对 429 做指数退避重试 |
| 截图无法截到指定 subuser 的屏幕（shell 可以） | `runtime_context` 缺少 `display` 字段 | 已修复：`build_runtime_context` 为 vm_user 注入 `display: ":11"` 等 |
| iOS 安装后黑屏 | custom-protocol 在 WKWebView 有已知问题；或 VITE_GATEWAY_URL 缺失导致启动抛错 | 已修复：iOS 用 `--features mobile` 不含 custom-protocol；config 兜底默认 Gateway URL |
| `tauri ios run` 报 exportOptionsPlist 找不到 | Tauri CLI 传相对路径，xcodebuild 工作目录不对 | 用 `tauri ios build` + `devicectl device install app`，见 `scripts/build-and-install-ios.sh` |
| iOS 构建报 "Arch specified by Xcode was invalid" | project.yml 含 `${FORCE_COLOR}` 被解析为 arch 参数 | 运行 `bash scripts/patch-ios-xcode.sh` 修复 |
| iOS 构建报 `no method named 'show' found for WebviewWindow` | `WebviewWindow::show` 仅 `#[cfg(desktop)]` 存在，移动端无此方法 | 已修复：`setup.rs` 中 `show_main_window` 用 `#[cfg(desktop)]` 包裹，移动端窗口默认可见 |
| 排查 P2P 请求是否到达 Gateway | 需确认 locate 是否被调用 | `GET /api/p2p/debug`（需 JWT）返回最近 50 条 P2P 事件 |
| 调试 STUN 是否可用 | 验证本机能否获取外网地址 | `python3 novaic-app/scripts/test-stun.py [port]` |
| 自建 STUN 服务器 | 默认 stun.gradievo.com:3478（novaic-quic-service） | 覆盖用 `NOVAIC_STUN_SERVER=stun.l.google.com:19302` |
| Relay 连接失败（P2P 兜底） | relay 服务未部署、TLS 证书、防火墙 443/udp | 检查 novaic-quic-service 状态；`NOVAIC_RELAY_INSECURE=1` 仅限本地调试 |
| Relay handshake timeout | Relay 用 open_bi 而非 accept_bi | 已修复：relay.rs 改为 accept_bi() |
| P2P registry missing field 'ok' | 401 时 body 为 `{"detail":"..."}`，按 HeartbeatResponse 解析失败 | 已修复：rendezvous.rs 先判断 status 再解析 body |

### Subuser 截图修复说明

当 agent 绑定到 **vm_user**（subuser）时，screenshot 需要正确的 `DISPLAY` 才能截取该用户的 Xvnc 会话。此前 `build_runtime_context` 未设置 `display`，导致 VMUSE 的 `_get_desktop_env` 无法注入 `DISPLAY`，scrot/import 使用默认 display（:10，main 桌面）。shell 能正确执行是因为 `sudo -u {linux_user}` 在用户 session 下运行，环境已正确。修复：在 `novaic-gateway/gateway/agent_binding.py` 的 `build_runtime_context` 中为 Linux subject 添加 `display`：main 用 `:10`，vm_user 用 `:{display_num}`。

### LLM 调用失败排查方法

当 LLM 频繁报错（如 429）时，需区分是 **API 限流** 还是 **context 装错**。方法：

1. **查日志定位失败 task**：`grep -E "429|think.*failed" /opt/novaic/data/logs/task-worker-*.log`，记下 `task_id`。
2. **取正确 context**：Saga 任务的 messages 来自 `read_context` 的 step_results，**不能**用 `runtime.context`（后者是当前状态，已含后续 round）。正确来源：`tq_sagas.step_results -> read_context.context`。
3. **重放 llm.call**：从 saga 取出 context，`POST /api/queue/tasks/publish` 发布 `topic=llm.call`，payload 含 `runtime_id`、`round_id`、`messages`、`agent_id`、`subagent_id`。
4. **对比结果**：若相同 context 重放成功 → API 间歇性限流；若仍失败 → 排查 context 格式或 API 配置。

脚本：`novaic-agent-runtime/scripts/trace_llm_call.py`（需从 saga 取 context，勿用 `runtime.context`）。

### 服务器数据维护

> 2026-03-14 执行清理后：内存 52%→28%，磁盘 10GB→6.1GB

#### 定期清理项目

| 项目 | 命令 | 说明 |
|---|---|---|
| **Orchestrator 已完成 context** | `sqlite3 runtime_orchestrator.db "UPDATE agent_runtimes SET context='[]' WHERE status='completed'; VACUUM;"` | 已完成 runtime 保留了 LLM context JSON，不清理会膨胀到数百 MB；上次清理后 473MB→9MB |
| **Queue 已完成任务** | `sqlite3 queue.db "DELETE FROM tq_tasks WHERE status IN ('done','failed'); DELETE FROM tq_sagas WHERE status!='active'; VACUUM;"` | 上次清理后 1.9GB→3MB |
| **日志轮转** | `find /opt/novaic/data/logs/ -name '*.log' -mtime +7 -delete` | 删除 7 天前的日志 |
| **日志截断** | `find /opt/novaic/data/logs/ -name '*.log' -size +50M -exec truncate -s 10M {} \;` | 截断超大日志文件 |

所有操作在 `/opt/novaic/data/` 目录下执行，gateway 运行时可安全执行（SQLite WAL 模式）。清理后建议 `./deploy orchestrator` 重启释放内存。

#### 服务器资源概况（2026-03-14）

| 服务器 | 配置 | 内存 | 磁盘 |
|---|---|---|---|
| api.gradievo.com | 1核 3.3GB | 28% (953MB/3.3GB) | 6.1GB data |
| relay (47.243.221.45) | 2核 1.6GB | 29% (462MB/1.6GB) | 6GB total |

后端共 16 个 Python 进程：6 个 HTTP 服务 + 4 task-worker + 2 saga-worker + watchdog + health + scheduler + STUN。

---

## 十三、环境变量与配置

### 本地 Tauri App

**App 数据目录**（`app.path().app_data_dir()`）：
- macOS：`~/Library/Application Support/com.novaic.app`
- 内含：`gateway_url.txt`（Gateway URL，默认 `https://api.gradievo.com`）、`api_key.txt`、`app.pid` 等

**VmControl 读取的路径约定**：
- SSH Key：`~/.novaic/.ssh/id_rsa`（`DATA_DIR` 由 App 启动时确定）
- QMP Socket：`/tmp/novaic/novaic-qmp-{agent_id}.sock`
- VNC Socket（VmControl 内部使用）：`/tmp/novaic/novaic-vnc-{id}.sock`

### 云端 Gateway 启动参数

```
--host 127.0.0.1
--port 19999
--data-dir /opt/novaic/data
--runtime-orchestrator-url http://127.0.0.1:19993
--queue-service-url        http://127.0.0.1:19997
--tools-server-url         http://127.0.0.1:19998
--file-service-url         http://127.0.0.1:19995
--tool-result-service-url  http://127.0.0.1:19994
```

可选环境变量：`RELAY_URL=https://relay.gradievo.com/p2p/relay`（relay-request 返回给手机，未设置时用默认值）。

### 本地 App 环境变量

```bash
# novaic-app/.env
VITE_GATEWAY_URL=https://api.gradievo.com
```

### novaic-quic-service 环境变量

| 变量 | 说明 |
|------|------|
| GATEWAY_URL | Gateway 地址（relay 鉴权） |
| RELAY_PORT | Relay 监听端口（生产 443） |
| STUN_PORT | STUN 监听端口（3478） |
| RELAY_TLS_CERT_PATH | TLS 证书 PEM 路径 |
| RELAY_TLS_KEY_PATH | TLS 私钥 PEM 路径 |

### 前端配置（novaic-app/src/config/index.ts）

| 配置块 | 关键项 |
|---|---|
| API_CONFIG | GATEWAY_URL, HTTP_TIMEOUT |
| LAYOUT_CONFIG | LAYOUT_THRESHOLD(1024), DRAWER_WIDTH(304) |
| SSE_CONFIG | RECONNECT_DELAY, MAX_RECONNECT_ATTEMPTS |
| POLL_CONFIG | GATEWAY_HEALTH_INTERVAL |
| STORAGE_KEYS | selectedAgent, selectedModel 等 prefs 键名 |

---

## 十四、待办 / 技术债

- [ ] **iOS 键盘输入框适配**：原生 `--keyboard-height` 注入方案已实现（main.mm），Header 固定 OK，但输入框仍可能不可见。需要在真机上验证并调试
- [ ] **服务端数据自动清理**：runtime 完成时自动清空 context（修改 `RuntimeRepository.complete_runtime`）；queue 定期清理已完成任务；日志 logrotate
- [ ] **Watchdog v2：Per-Agent 轮询**：将 Watchdog 从逐条消息创建 Saga 改为按 Agent 分组批量处理，防止消息积压导致同一 Subagent 创建多个 Runtime（详见二十三节）
- [ ] WebRTC 多客户端操控冲突处理（当前多端操控不互斥，可能产生输入冲突）
- [ ] Gateway DB 访问改为异步（当前同步 SQLite 在 async FastAPI 中，高并发下仍有阻塞风险）
- [ ] **Skill 商店 / ClawHub 集成**：需要 ClawHub API 端点和文档，在 Skills tab 第二栏增加「商店」入口，支持浏览/搜索/安装 skill
- [ ] **原生视频渲染（全客户端）**：所有客户端（iOS/Android/macOS/Web）用原生解码替代 WebRTC `<video>` 标签渲染，降低功耗+延迟+画质损失。iOS: VideoToolbox+Metal；Android: MediaCodec+GL；macOS: VideoToolbox+Metal；Web: WebCodecs API（见二十五节）

### 前端修改注意事项

- **DeviceFloatingPanel**：所有设备类型使用 WebRtcView；`isMain` 条件含 `'main' | 'default' | 空值`，确保 HD（host_desktop）设备也走 isMain 分支；改布局参数只改 `FLOATING_PANEL_LAYOUT` 和 `getPreviewSize`
- **ChatInput 状态**：`chatUnreadCount` 从 Zustand store 读；`scrollToBottom` 从 `chatScrollRegistry` 调用；不再 prop drill
- **CollapsibleExecutionLog**：inline 时 Tab 在底部；非 inline 时已废弃（不再使用顶部浮动）
- **模型相关**：`useModels` 读 store；`getModelService().setModel` 写 store + prefs + gateway

### AgentToolsTab 数据架构（SWR — 2026-03-14 重构）

**原则**：与 chat/log 完全一致 —— **render 只读 DB，永不直连 API**。

**数据流**：
```
打开 Agent Tab / 切换 Agent
  → useAgentConfigFromDB(agentId)  // Phase 1: 从 IndexedDB 瞬间读取缓存
  →   有缓存 → setState → 立即渲染
  →   无缓存 → 骨架屏
  → revalidate()                   // Phase 2: 后台静默从 API 拉取最新
  →   Promise.allSettled(6 个配置请求)
  →   agentConfigRepo.putAgentConfig()  // 写入 IDB
  →   notifyAgentConfigChange()         // subscription 通知
  →   useAgentConfigFromDB 收到回调 → 重新读 IDB → setState → 无感更新

  → binding / model / devices       // Phase 1b: 从 Zustand store 直读
  →   agent.binding（agent 列表 API 已包含）
  →   agent.model_id + availableModels
  →   getDevices(userId) from IDB
  → revalidate() 也会后台刷新这些
```

**handleSave 写通**：Save 成功后 → API 写入 + `agentConfigRepo.patchAgentConfig()` 写入 IDB → subscription 触发 UI 刷新。

**第一次**打开某个 Agent 配置时，IDB 无缓存，等后台 revalidate 完成后写入 IDB，UI 自动填充。**第二次以后**瞬间从 IDB 缓存渲染。

### ExecutionLog 与 CollapsibleExecutionLog

- **ExecutionLog**：完整日志视图，`showHeader` 时显示 subagent tabs（全部/各 subagent 切换）
- **MainAgentLogPreview**：主 Agent 日志预览，独立组件
- **SubagentList**：Subagent 列表，独立组件，点击打开 AgentLogModal

### 关键文件速查

| 需求 | 文件 |
|---|---|
| 改远程桌面连接 | `useWebRtc.ts`、`WebRtcScrcpyView.tsx`（统一 WebRTC） |
| 改设备操控台 | `DeviceConsole.tsx`、`ConsoleToolbar.tsx`、`useWebRtc.ts`、`useRemoteInput.ts`、`useViewTransform.ts` |
| 改浮窗尺寸/位置 | `DeviceFloatingPanel.tsx` → FLOATING_PANEL_LAYOUT |
| 改 Execution Log 布局 | `MainAgentLogPreview.tsx`、`SubagentList.tsx`、`ChatPanel.tsx` |
| 改模型选择 UI | `SettingsModal.tsx` → AgentToolsTab |
| 改消息发送 | `ChatInput.tsx`、`messageService.ts` |
| 改 Agent 列表 | `AgentDrawer.tsx`、`useAgent.ts` |
| 改主布局/导航 | `LayoutContainer.tsx`、`PrimaryNav.tsx`、`BottomTabBar.tsx`、`App.tsx` |
| 改 Skills 列表/详情 | `AgentDrawer.tsx`（skillsContent）、`SettingsModal.tsx`（SkillsTab） |
| 改 Devices tab / PC Client 管理 | `PcClientDeviceList.tsx`、`AgentDrawer.tsx`（devicesContent） |
| 改 Gateway 配置 API | `novaic-gateway/gateway/api/internal/config.py` |
| 改 VM 准备（环境/镜像/部署） | `novaic-gateway/gateway/api/vm.py`、`vmcontrol/src/api/routes/vm_prep.rs` |
| 改 Relay 服务 | `novaic-quic-service/src/relay.rs`、`protocol.rs`、`auth.rs` |
| 一键部署全部 | `scripts/deploy-all.sh` |
| OTA 三处一致性校验 | `scripts/check-ota-sync.sh`（CI 已集成） |

### Gateway 内部配置（LLM 调用用）

`/internal/config` 返回 agent 的 model 配置：优先用 `agents.model_id`，否则用 `config.default_model`；从 `candidate_models` 解析 `api_key`、`api_base` 供 runtime 调用 LLM。

### 相关文档

> 注：文档已于 2026-03-14 分类整理到 `docs/` 子目录。路径格式：`docs/{category}/{filename}.md`

| 文档 | 说明 |
|---|---|
| `novaic-app/FRONTEND_ARCHITECTURE.md` | Render/Business/DB 三层、hooks 约束、数据流 |
| `docs/submodules/novaic-app/ARCHITECTURE_OVERVIEW.md` | 架构总览、数据流图 |
| `docs/design/SSE_USER_LEVEL_MIGRATION.md` | SSE 改为 User 维度改造方案 |
| `docs/design/COMMANDS_SPLIT_DESIGN.md` | Tauri 命令拆分、vm/vmcontrol 关系 |
| `docs/design/DESIGN-P2P-UNIFIED.md` | P2P 架构、Relay 兜底、Registry/Discovery |
| `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md` | OTA 重新启用实施方案 |
| `docs/design/SYSTEM_DESIGN.md` | 系统设计 |
| 本文档「四 → iOS 部署流程」 | iOS 完整部署流程、黑屏修复、键盘原生修复 |

---

## 十五、数据库操作安全规范

SQLite WAL 模式下，**gateway 运行时可以直接用 sqlite3 读写 DB**（多读单写并发）。

正常情况下操作不需要停 gateway，只有以下两种情况需要注意：

### ⚠️ 危险操作：PRAGMA wal_checkpoint(TRUNCATE)

**禁止**在 gateway 运行时执行 `PRAGMA wal_checkpoint(TRUNCATE)`。  
这会截断 WAL 文件，可能把 gateway 正在进行中的事务数据直接丢弃。

### gateway 无响应时的恢复步骤

gateway 卡死（health check 超时）通常是 WAL/SHM 文件损坏：

```bash
kill -9 $(pgrep -f main_gateway.py)
sleep 2
rm -f /opt/novaic/data/gateway.db-wal /opt/novaic/data/gateway.db-shm
bash /opt/novaic/restart_gw.sh
```

### 数据迁移模板（gateway 运行时也可执行）

```bash
# 备份（建议先做）
cp /opt/novaic/data/gateway.db /opt/novaic/data/gateway.db.backup_$(date +%Y%m%d_%H%M%S)

# 迁移（gateway 跑着也没问题，sqlite3 busy_timeout=3s 会等锁）
sqlite3 /opt/novaic/data/gateway.db <<'EOF'
BEGIN TRANSACTION;
UPDATE agents SET user_id = 'new-uid' WHERE user_id = 'old-uid';
-- 其他表...
COMMIT;
EOF
```

> 若迁移的表正在被频繁写入（如 `chat_messages`、`execution_logs`），可以先停 gateway 再操作以避免冲突等待。

---

## 十六、（已归档：VNC 连接竞态消除与架构重构）


> 原 noVNC 管线（IPC 竞态修复、transportFactory 热重载、Tight 编码优化等）已于 2026-03-19 随 WebRTC 统一迁移全部移除。
> 当前所有远程桌面均走 WebRTC，架构详见第八节「远程桌面架构（2026-03-19 WebRTC 统一）」。
---

## 十七、RustDesk 优化落地（2026-03-16）

深入分析 RustDesk 源码后，将其 8 大优化类别逐一落地到 NovAIC 远程流管线中。

### 1. BGRA 直接 GPU 编码（消除 CPU 色彩转换）

**旧路径**：ScreenCaptureKit BGRA → `bgra_to_yuv420_fast()` (CPU ~5ms) → I420 → `fill_nv12()` → NV12 CVPixelBuffer → VT 编码

**新路径**：ScreenCaptureKit BGRA → BGRA CVPixelBuffer → VT **GPU 自行 BGRA→NV12** → 编码

- H264Encoder trait 新增 `encode_bgra()` 方法，默认实现走 BGRA→YUV→encode（软编码 fallback）
- VT 编码器覆盖 `encode_bgra()`：创建 `kCVPixelFormatType_32BGRA` CVPixelBuffer，填入 BGRA 数据，GPU 内部自行转换
- SCK 捕获循环已切换为优先调用 `encode_bgra()`
- 新增 `fill_bgra()` + 公共 `encode_pixelbuffer()` 消除 NV12/BGRA 路径的代码重复

**关键文件**：
- `vmcontrol/src/webrtc/vt_encoder.rs`：`encode_bgra()`, `fill_bgra()`, `encode_pixelbuffer()`
- `vmcontrol/src/webrtc/encoder.rs`：trait 新增 `encode_bgra()`, `set_bitrate()`, `is_hardware()`
- `webrtc_hd.rs`：SCK 捕获循环改用 `encoder.encode_bgra()`

### 2. 分辨率感知码率公式（学习 RustDesk base_bitrate + calc_bitrate）

替换旧的固定三档码率（3/5/8 Mbps）为 RustDesk 风格的查表插值 + 衰减因子：

```rust
// 12 档分辨率预设查表（含 MacBook Air/Pro 特殊分辨率）
const PRESETS: &[(u32, u32, u32)] = &[
    (640, 480, 400), (1280, 720, 1000), (1512, 982, 1500),
    (1920, 1080, 2073), (2880, 1800, 4000), (3840, 2160, 5000), ...
];
// 找最近分辨率，按像素比插值，再乘衰减因子防爆
let factor = if base > 2000 { 1.0 + 1.0 / (1.0 + (base - 2000) * 0.001) } else { 2.0 };
```

**函数**：`base_bitrate(w, h) -> kbps`，`calc_bitrate(w, h, ratio) -> kbps`

### 3. 动态码率调整 API

- H264Encoder trait 新增 `set_bitrate(kbps) -> bool`
- VT 编码器实现：`VTSessionSetProperty(kVTCompressionPropertyKey_AverageBitRate)` 实时生效
- SCK 捕获循环每秒检查 QoS ratio 变化，自动调用 `encoder.set_bitrate()`

### 4. VideoQoS 自适应控制器（学习 RustDesk video_qos.rs）

新模块 `vmcontrol/src/webrtc/video_qos.rs`，基于网络延迟动态调整 FPS 和码率比率：

| 延迟范围 | FPS 调整 | 码率调整（每 3 秒） |
|:---|:---|:---|
| < 50ms | +2 fps | ratio × 1.15（仅动态屏幕） |
| 50-100ms | +1 fps | ratio × 1.10 |
| 100-150ms | 维持 | ratio × 1.05 |
| 150-200ms | fps × (150/delay) | ratio × 0.95 |
| 200-300ms | max(8, 150×8/delay) | ratio × 0.90 |
| > 300ms | MIN_FPS=5 | ratio × 0.80 |

- 新连接前 1 秒限制 15fps 防突发冲击
- `update_delay(ms)` 接收延迟样本（来自 WebRTC getStats 或 DataChannel ping）
- `update_send_count(count)` 每秒调用，驱动码率 ratio 调整
- SCK 捕获循环基于 `qos.spf()` 控制帧间隔

### 5. 编码失败自动 Fallback（学习 RustDesk encode_fail_counter）

- `qos.encode_failed()` 追踪连续失败次数
- 硬件编码器（VT）连续 3 次失败 → 自动降级到 openh264 软编码
- 降级后不黑屏，平滑切换
- H264Encoder trait 新增 `is_hardware()` 区分编码器类型

**关键代码**（webrtc_hd.rs SCK 捕获循环）：
```rust
None => {
    encode_fail_count += 1;
    if qos.encode_failed() && encoder.is_hardware() {
        encoder = Box::new(OpenH264Encoder::new(cap_w, cap_h).expect("fallback"));
    }
}
```

### 优化效果汇总

| 优化 | 效果 | 状态 |
|:---|:---|:---|
| VideoToolbox GPU 编码 | 编码 30ms→2ms | ✅ 已上线 |
| BGRA 直接编码 | 消除 ~5ms CPU 色彩转换 | ✅ 本次新增 |
| 分辨率感知码率 | 更优画质/带宽平衡 | ✅ 本次新增 |
| 动态码率调整 | 网络波动自适应 | ✅ 本次新增 |
| VideoQoS 控制器 | FPS+码率双维自适应 | ✅ 本次新增 |
| 编码失败 Fallback | 硬件异常不黑屏 | ✅ 本次新增 |
| broadcast 通道缩容 | 延迟 -3.5s | ✅ 已上线 |

---

## 十八、虚拟键盘 Apple 风格视觉反馈（2026-03-16）

增强 `VirtualKeyboard.tsx` 按键反馈，对标 iOS 系统键盘体验：

| 效果 | 实现 |
|:---|:---|
| **弹出气泡** | 按字母/数字键时，在按键上方弹出放大字符气泡（底部小三角指向按键），150ms 后消失 |
| **缩放动画** | 按下 `scale(0.88)`，松开 `scale(1)` + `ease-out` 缓动 |
| **发光效果** | `box-shadow: 0 0 18px rgba(99,102,241,0.65)` + `inset 0 0 8px rgba(255,255,255,0.15)` + `brightness(1.3)` |
| **基础阴影** | 所有按键默认 `box-shadow: 0 1px 2px rgba(0,0,0,0.3)` 立体感 |
| **弹出动画** | CSS `@keyframes vk-popup`：`scale(0.6)→scale(1.05)→scale(1)` 弹性展开 |

气泡仅对普通键和数字键显示，修饰键（Shift/Ctrl/Alt/⌘）和功能键（F1-F12）不显示。

**关键文件**：`src/components/Console/VirtualKeyboard.tsx`

---

## 十九、PiP 缩略图操控模式点击修复（2026-03-16）

**问题**：在操控模式（`viewMode === 'fixed'`）下缩放画面后，点击角落的 PiP 全景缩略图无法恢复全景。

**根因**：`useRemoteInput` 在 viewport 容器上注册了原生 `touchstart`/`mousedown` 事件监听器（bubble 阶段）。PiP 缩略图虽然用了 `e.stopPropagation()`，但 React 事件系统的 `stopPropagation` 无法阻止同一 DOM 元素上通过 `addEventListener` 注册的原生监听器。

**修复**：

| 修改 | 说明 |
|:---|:---|
| `stopImmediatePropagation()` | 阻止同一元素上所有后续监听器（包括原生注册的 useRemoteInput 处理器） |
| 全方位事件拦截 | `onTouchStart` + `onMouseDown` + `onPointerDown` + `onTouchEnd` + `onTouchMove` |
| z-index 提升 | `z-40` → `z-50`，确保在操控边框等覆盖层之上 |
| `pointerEvents: 'auto'` | 显式声明可交互 |

**关键文件**：`src/components/Console/PipMinimap.tsx`

---

## 二十、远程光标通道与放大镜优化（2026-03-17）

### 1. 远程光标 DataChannel

RustDesk 风格双 DataChannel 架构：control channel（UI→远程）+ cursor channel（远程→UI）。

- **后端**：`cursor.rs` 追踪 macOS 光标形状，变化时序列化 RGBA + 宽高 + 热点坐标，通过 `cursor_shape` JSON 消息发送
- **前端**：`useWebRtc.ts` 接收 `cursor_shape` → base64 解码 → canvas 生成 data URL → 更新 `remoteCursor` state
- **渲染**：`RemoteCursor.tsx` 在视频画面上叠加光标图像

### 2. DPR 缩放统一

**决策**：光标尺寸缩放逻辑集中在 `DeviceConsole.tsx`，`RemoteCursor` 和 `CursorMagnifier` 直接消费缩放后的值。

```
DeviceConsole (统一 dpr 缩放)
  ├── scaledCursorWidth = width / devicePixelRatio
  ├── scaledHotx = hotx / dpr
  ├── scaledHoty = hoty / dpr
  ├── → RemoteCursor (直接用)
  └── → CursorMagnifier (直接用)
```

**原因**：macOS `NSImage.size` 返回 pt 而非 px，16pt 在 2x Retina = 32px 图像但报 `width:16`。除以 dpr 使得 CSS 像素下的显示大小约为系统光标的 2 倍。

### 3. CursorMagnifier 闪烁修复

**问题**：光标形状变化时（箭头→手指→I-beam），`cursorHotx/hoty/width` 在 useEffect 依赖数组中，触发 RAF 循环重启，`currentOpacity` 归零导致闪烁。

**修复**：将 `cursorHotx`、`cursorHoty`、`cursorWidth` 改为 ref 存储，从 useEffect deps 移除。RAF 循环不中断，下一帧自然读到新值。

### 4. ConsoleToolbar 竖屏布局重构

**旧布局**：所有控件挤一行 `flex-wrap`，竖屏换行后无结构。

**新布局**：
```
Row 1: 设备名+状态 | (flex) | 输入模式切换 | 操控/缩放切换
Row 2: 操作按钮居中 (键盘/剪贴板/刷新/截图/全屏/关闭)
状态行: 分辨率·fps·延迟·码率·编码 (居中)
```

- 移除了快捷键（`ShortcutMenu`）和 Android 导航（`AndroidNav`）组件
- 操作按钮统一 `p-2 rounded-lg` + `size={16}`，触摸友好

### 5. 剪贴板发送 Modal（iOS 键盘兼容）

**旧实现**：`absolute bottom-full` 小弹窗 → iOS 上超出屏幕 + 被软键盘遮挡。

**新实现**：`fixed` 顶部居中 Modal，`top: max(safe-area-inset-top, 44px)`，400px max-width 居中。

- iOS 软键盘弹出不遮挡（对话框在屏幕顶部）
- 横屏：max-w-400px 居中，不撑满
- textarea `stopPropagation` 防止按键同时发到远程桌面

### 6. VirtualKeyboard 收起按钮

"收起键盘 ▾" 从键盘底部移到顶部（Fn 行上方），始终可见。

### 关键文件

| 文件 | 变更 |
|:---|:---|
| `CursorMagnifier.tsx` | ref 存储光标属性，消除闪烁 |
| `RemoteCursor.tsx` | 消费 DPR 缩放后的值 |
| `DeviceConsole.tsx` | 统一 dpr 缩放计算 |
| `ConsoleToolbar.tsx` | 多行竖屏布局，移除快捷键，Modal 剪贴板 |
| `VirtualKeyboard.tsx` | 收起按钮移至顶部 |

---

## 二十一、反慢动作修复与自动 Keyframe 恢复（2026-03-17）

### 1. 反慢动作（Anti-Slowmo）

**问题**：前端画面偶尔出现慢动作效果，特别是在网络波动或编码器产出不均匀时。

**根因**：
- `subscriber_pump`（`peer.rs`）使用固定 `Sample.duration = 16ms`，但帧到达并不均匀
- 当帧积压后一次性发出，浏览器按 16ms 间隔逐帧渲染，产生慢放效果
- `frame_tx` channel 满时调用 `force_keyframe()`，HDR 帧 5-10x 大于 P 帧，加剧拥塞

**修复**：

| 修改 | 文件 | 说明 |
|:---|:---|:---|
| 动态 Sample.duration | `peer.rs` subscriber_pump | 使用 wall-clock 经过时间代替固定 16ms，让浏览器正确解释帧时序 |
| 帧 drain 机制 | `peer.rs` subscriber_pump | 循环 `try_recv` 丢弃旧帧，只发最新帧，消除积压 |
| drain 后请求 keyframe | `peer.rs` subscriber_pump | drain 导致帧不连续，立即请求 IDR 帮助解码器恢复 |
| 移除 backpressure keyframe | `webrtc_hd.rs` SCK+xcap | channel 满时不再 `force_keyframe()`，只降码率 |

**关键代码**（`peer.rs` subscriber_pump）：
```rust
// 使用 wall-clock 经过时间作为 sample duration
let elapsed = last_write.elapsed();
let duration_us = elapsed.as_micros().max(1) as u64;
sample.duration = Duration::from_micros(duration_us);

// drain 旧帧，只保留最新
let mut drained = 0;
while let Ok(newer) = frame_rx.try_recv() {
    latest = newer;
    drained += 1;
}
if drained > 0 {
    keyframe_tx.send(true).ok(); // 请求 keyframe
}
```

### 2. 切应用后画面冻结自动恢复

**问题**：切出应用再切回来，WebRTC 画面冻结，需手动点 IDR 刷新按钮。

**根因**：浏览器在页面不可见时暂停 WebRTC 视频解码，恢复后无法自动续播。

**修复**：`DeviceConsole.tsx` 添加 `useEffect` 监听 `visibilitychange` + `window.focus` 事件，200ms 延迟后自动请求 keyframe。

**关键文件**：

| 文件 | 变更 |
|:---|:---|
| `peer.rs` | subscriber_pump 动态 duration + drain 机制 |
| `webrtc_hd.rs` | 移除 SCK/xcap 路径的 backpressure force_keyframe |
| `DeviceConsole.tsx` | visibilitychange/focus 自动请求 keyframe |

---

## 二十二、工具执行架构概览（2026-03-17 分析）

### Agent 工具调用全链路

```
LLM tool_call (e.g. shell_exec)
  → Tools Server (ToolExecutor._execute_builtin)
    → VM_TOOL_MAPPING: "shell_exec" → ("shell", "command")
    → POST /internal/agents/{agent_id}/vm/shell/command
  → Gateway (proxy_vm_tool)
    → resolve_agent_runtime_context → binding + device + mounted_tools
    → is_tool_mounted → 检查权限
    → PC Client WebSocket 转发
  → VmControl (vmuse_agent_proxy)
    → reqwest POST http://127.0.0.1:{vmuse_port}/api/shell/command
  → VMUSE Server (Python, VM 内 port 8080)
    → ShellTools.run_command → asyncio.create_subprocess_shell
```

### 工具分类与路由

| 类别 | 工具数 | 路由路径 |
|:---|:---|:---|
| VM (desktop/shell/file/browser/window/context) | 25 | Gateway → PC Client WS → VmControl → VMUSE |
| Mobile (screen/shell/file/app/browser/ui) | 22 | Gateway → PC Client WS → VmControl → adb |
| Memory/Notebook/Chat/Goal/Task | ~30 | 直接调 Gateway API |
| QEMU (ssh_exec/status/start) | 5 | Gateway → PC Client WS → VmControl |

### Agent Binding 与 Mounted Tools

Agent 绑定设备时选择 `mounted_tools` 控制工具权限：

| 设备类型 | 支持的 Tool Categories |
|:---|:---|
| Linux VM | desktop, file, shell, clipboard, qemu |
| Android | screen, file, shell, app, browser, ui |
| Host Desktop | ❌ 未定义（当前走 Android else 分支，返回错误的 supported_tools） |

### 关键文件速查

| 需求 | 文件 |
|:---|:---|
| 工具定义（schema） | `novaic-tools-server/common/tools/definitions.py` |
| 工具路由+执行 | `novaic-tools-server/tools_server/executor.py` |
| 工具权限+挂载 | `novaic-gateway/gateway/agent_binding.py` |
| VM 代理路由 | `novaic-gateway/gateway/api/internal/agent.py` (proxy_vm_tool) |
| VmControl VMUSE 代理 | `novaic-app/src-tauri/vmcontrol/src/api/routes/vmuse.rs` |
| VMUSE Shell 实现 | `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/shell.py` |
| Mobile 工具路由 | `novaic-app/src-tauri/vmcontrol/src/api/routes/mobile.rs` |
| 前端工具配置 UI | `novaic-app/src/components/Settings/SettingsModal.tsx` (AgentToolsTab) |

---

## 二十三、Agent Runtime 后端架构（2026-03-17 深度分析）

### 后端服务组件一览

| 进程 | Repo | 职责 |
|:---|:---|:---|
| Gateway | novaic-gateway | API、DB (chat_messages/subagents/agents)、SSE |
| Runtime Orchestrator (RO) | novaic-runtime-orchestrator | Runtime CRUD、agent_runtimes 表 |
| Queue Service | novaic-agent-runtime/queue_service | Task/Saga 队列管理 |
| Watchdog | novaic-agent-runtime | 轮询 `sending` 消息，创建 MessageProcess Saga |
| Task Worker | novaic-agent-runtime | 执行 Task（LLM 调用、工具执行、context 读写等）|
| Saga Worker | novaic-agent-runtime | Saga 流程编排（步骤推进、决策、触发子 Saga）|
| Health Worker | novaic-agent-runtime | 超时任务/Saga 回收 |
| Scheduler Worker | novaic-agent-runtime | 定时唤醒 sleeping agent（检查 wake_at）|
| Tools Server | novaic-tools-server | 工具执行（shell/browser/file 等）|

### 消息 → Runtime 完整链路

```
用户发消息
  → Gateway: chat_messages INSERT (type=USER_MESSAGE, status=sending, read=0)
  → Watchdog: find_sending() → 创建 MessageProcess Saga
  → Saga Step 1 (claim_message): sending → sent
  → Saga Step 2 (route_message): RO get_or_create_runtime()
    → 有 active runtime? → skip（消息由 context.read 消费）
    → 无 active? → 创建 rt-xxx（status=active）→ just_created=true
  → Saga Step 3 (decide): just_created → action=start_runtime
  → Saga Step 4 (trigger): 创建 RuntimeStart Saga
    → Set subagent awake
    → Build initial context (historical_summary + HRL summaries + system prompt)
    → Trigger ReactThink
```

### Agent Loop（ReactThink ↔ ReactActions）

```
ReactThink:
  Step 1 (context.read):     读 RO context + Gateway 未读消息(read=0) → 合入 context
  Step 2 (context.mark_read): 标记消息 read=1
  Step 3 (llm.call):          调 LLM（kimi-k2.5/gpt-4o）
  Step 4 (context.save):      保存 assistant response 到 context
  Step 5 (decide):            有 tool_calls? → trigger ReactActions
                              无 tool_calls? → 重试机制 → 最终 subagent_rest

ReactActions:
  Step 1 (execute_tools):    并行执行所有 tool_calls（Tools Server）
  Step 2 (save_results):     保存 tool results 到 context
  Step 3 (check_continue):   调 has_new_messages + check_and_clear_need_rest
  Step 4 (decide):
    has_new=false && need_rest=true → trigger RuntimeComplete
    else                            → trigger 下一轮 ReactThink
```

### subagent_rest 完成流程

```
LLM 调 subagent_rest
  → Tools Server: POST Gateway /internal/subagents/{agent_id}/{subagent_id}/rest
  → Gateway: set need_rest=1, wake_at=now+30min, wake_triggers=[{type:user_response}]
  → ReactActions check_continue:
    → Gateway check-and-clear-rest (CAS): 读 need_rest=1 并清零
    → has_new_messages: 查 read=0 的 USER_MESSAGE
    → should_complete = !has_new && need_rest → true → RuntimeComplete
  → RuntimeComplete Saga:
    → Generate simple_summary
    → Add to HRL
    → Set runtime status=completed
    → Set subagent sleeping
```

### 关键数据库分布

| 数据 | 所在 DB | 表 |
|:---|:---|:---|
| 用户消息 | Gateway (gateway.db) | chat_messages (status: sending/sent, read: 0/1) |
| SubAgent 状态 | Gateway | subagents (status, need_rest, wake_at, hrl) |
| Runtime 及 Context | RO (runtime_orchestrator.db) | agent_runtimes (status, context JSON, round) |
| Task/Saga 队列 | Queue Service (queue.db) | tasks, sagas |

### 已知 Bug：消息积压导致重复 Runtime（2026-03-17 定位）

**问题**：SYSTEM_WAKE 风暴（scheduler 对过期 wake_at 反复触发）导致数百条 `sending` 消息积压。Watchdog 为每条消息创建独立的 MessageProcess Saga。这些 Saga 排队执行，当前一个 Runtime 已 completed 后，后续 Saga 的 `get_or_create_runtime` 发现无 active runtime，又创建新的。

```
T=0s    Watchdog: 为 100 条消息创建 100 个 Saga（毫秒级）
T=0.1s  Saga-1: get_or_create → 创建 rt-aaa (active)
T=0.2s  Saga-2: get_or_create → rt-aaa active → skip ✅
T=30s   rt-aaa completed
T=30.1s Saga-50: get_or_create → 无 active → 创建 rt-bbb ❌
...循环
```

**三个 agent 在 16:43~16:57 都创建了 5~10 个串行 runtime**，时间高度对齐。

**根因**：`get_or_create_active_runtime` 有全局锁、单次调用原子正确。但 Saga 排队执行跨越了 Runtime 的整个生命周期（30s+），锁早已释放。

**临时修复**：清理了所有 active runtime，重置 subagent 为 sleeping，杀掉 scheduler 进程，清理 SYSTEM_WAKE 消息。

**设计中的根治方案 — Watchdog v2 Per-Agent 轮询**：
- Watchdog 一次拿全部 sending 消息（`find_all_sending`）
- 按 `(agent_id, subagent_id)` 分组，每组只创建 1 个 Saga
- 每轮 `sleep(3s)` 天然冷却
- SPAWN_SUBAGENT 不合并（不同 subagent），INTERRUPT 直接处理不走 Saga
- 详细方案见 artifacts: `watchdog_v2_design.md`

### 关键文件速查

| 需求 | 文件 |
|:---|:---|
| Watchdog 主循环 | `novaic-agent-runtime/task_queue/workers/watchdog_sync.py` |
| MessageProcess Saga | `novaic-agent-runtime/task_queue/sagas/message_process.py` |
| route_message handler | `novaic-agent-runtime/task_queue/handlers/message_handlers.py` |
| ReactThink Saga | `novaic-agent-runtime/task_queue/sagas/react_think.py` |
| ReactActions Saga | `novaic-agent-runtime/task_queue/sagas/react_actions.py` |
| check_new_messages handler | `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py` |
| get_or_create_runtime (RO) | `novaic-runtime-orchestrator/gateway/db/repositories/runtime.py` |
| subagent_rest endpoint | `novaic-gateway/gateway/api/internal/subagent.py` (line 453) |
| has_new_messages / get_pending_count | `novaic-gateway/gateway/db/repositories/message.py` (line 486) |
| Scheduler Worker | `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py` |

## 二十四、WebRTC 统一入口代码精简（2026-03-19）

### 背景

前期已完成 WebRTC 统一入口（所有设备类型走 `/api/webrtc/start` + `/api/webrtc/stop`），本次清理所有旧的 per-type 路由和前端死代码。

### 删除的代码

#### Gateway (`novaic-gateway/gateway/api/vmcontrol.py`)

删除 6 个旧路由函数（~150 行）：
- `POST /android/webrtc/start` / `stop`
- `POST /host-desktop/webrtc/start` / `stop`
- `POST /vm/webrtc/start` / `stop`

保留：`POST /webrtc/start` 和 `/webrtc/stop`（统一入口）

#### VmControl (`vmcontrol/src/api/routes/mod.rs`)

删除 6 个旧 axum 路由注册（8 行）。模块文件 `webrtc_vm.rs`、`webrtc_hd.rs`、`webrtc_scrcpy.rs` **保留**（`webrtc_unified.rs` 内部仍调用它们的函数）。

#### 前端

| 文件 | 变更 |
|---|---|
| `useWebRtc.ts` | 删除 3 处 `?? 'host_desktop'` fallback |
| `DeviceFloatingPanel.tsx` | `deviceId="host_desktop"` → `deviceId={device.id}` |
| `DeviceSidebar.tsx` | 同上 |
| `PcClientDeviceList.tsx` | `deviceId="host-desktop"` → `deviceId={device.id}`（x2）+ `showToolbar={false}` |
| `DeviceVNCView.tsx` | 123→33 行，删除 Linux/Android 分支和 start/stop 按钮，统一走 WebRtcView |
| `vm.ts` | 删除 `getVncStatus()`（零调用）+ unused imports |
| `main.tsx` | 删除 noVNC console.error 过滤器 |
| `types/novnc.d.ts` | **删除文件** |
| `types/novnc-rfb.d.ts` | **删除文件** |

### Bug 修复

#### 1. Subuser 进入操控台连到 main desktop

**根因**：`PcClientDeviceList.tsx` 蒙层点击 `onClick={() => { setConsoleOpen(true); onToggleExpand(); }}` 同时收起面板 → `useEffect` 检测到 `!expanded` → `setSelectedUser(null)` → `DeviceConsole` 拿到的是 `subjectType='main'`。

**修复**：蒙层点击只开操控台不收起面板：`onClick={() => setConsoleOpen(true)}`

#### 2. 设备预览页工具栏无法点击

**根因**：预览区有蒙层覆盖（"进入操控台"），底部工具栏按钮点不到。

**修复**：`WebRtcView` 传 `showToolbar={false}`；触控/鼠标切换按钮改为仅 Android 显示。

#### 3. Subuser WebRTC 连接后光标不显示

**根因**：VNC Cursor pseudo-encoding 是被动的——只在光标形状变化时推送。Subuser VNC 会话的 X11 root window 默认光标为空，直到打开窗口后窗口管理器才设置光标。

**修复**：`RemoteCursor.tsx` 在没有远程 cursor shape 时显示默认白色箭头 SVG。同时在 `webrtc_vm.rs` VNC 握手后发 PointerEvent 尝试触发服务端光标（辅助措施）。

### 当前架构

```
前端 → device.id
  → POST /api/vmcontrol/webrtc/start { device_id, sdp_offer }
  → Gateway forward_request
  → VmControl /api/webrtc/start
  → webrtc_unified.rs: SQLite Device Registry → DeviceKind → 分发
```

**零硬编码、零 fallback、单一路由入口。**

### 关键文件速查

| 需求 | 文件 |
|:---|:---|
| 统一 WebRTC 路由 | `vmcontrol/src/api/routes/webrtc_unified.rs` |
| 远程光标组件 | `Console/RemoteCursor.tsx`（默认箭头 fallback） |
| 设备预览列表 | `Layout/PcClientDeviceList.tsx`（showToolbar=false、蒙层修复） |
| 设备显示统一组件 | `Visual/DeviceVNCView.tsx`（精简后 33 行） |

## 二十五、移动端原生视频渲染方案调研（2026-03-19）

### 背景

当前移动端视频渲染走 WebRTC MediaTrack → `<video>` 元素，在 WKWebView 中解码。问题：
- 手机发烫（软解码吃 CPU）
- 延迟较高（jitter buffer + WebView 渲染管线）
- 光标合成用 DOM overlay，有异步延迟

### 方案：Rust 原生解码 + Metal/GL 渲染

```
H.264 NALUs → VideoToolbox (iOS) / MediaCodec (Android)
  → GPU texture → Metal/GL 渲染 → CAMetalLayer
  → 放在 WKWebView 后面，WebView 视频区透明
```

### 可行性结论：✅ 可行

1. **WKWebView 原生支持透明**：`isOpaque = false` + `backgroundColor = .clear` 是 Apple 官方 API
2. **已有控制权**：`main.mm` 已拿到 `g_webView` + `UIWindow`，可以 `insertSubview:belowSubview:`
3. **性能影响可忽略**：`isOpaque=false` GPU 混合开销 < 1ms
4. **不需要触摸穿透**：触摸仍在 WebView 透明 div 上捕获，通过 invoke 发给 Rust
5. **服务端不需要改**：`VideoBroadcaster` 已输出裸 H.264 Bytes，只需新增 WebSocket 推送端点

### 实施计划（6 个 Phase，~13 天）

| Phase | 内容 | 工期 |
|-------|------|------|
| 0 | 传输通道：服务端 WebSocket 裸帧推送（复用 VideoBroadcaster） | 2天 |
| 1 | 原生解码器：VideoToolbox (iOS) / MediaCodec (Android) | 3天 |
| 2 | 原生渲染层：CAMetalLayer + WKWebView 透明 ★ | 4天 |
| 3 | 光标合成：Metal drawcall 同帧渲染 | 1天 |
| 4 | 输入桥接：触摸 invoke → Rust → VNC PointerEvent | 1天 |
| 5 | 前端集成：`useNativeVideo` hook + 协议切换 | 2天 |

### 验证 PoC（半天）

在 `main.mm` 加 30 行代码：创建红色 UIView 插在 WebView 后面，前端视频区 CSS 透明。手机上能透过 WebView 看到红色方块 → 方案确认可行。

### 关键文件

| 需求 | 文件 |
|:---|:---|
| iOS 原生入口 | `gen/apple/Sources/novaic/main.mm`（已有 WKWebView 控制权） |
| H.264 帧广播 | `vmcontrol/src/webrtc/broadcaster.rs`（VideoFrame 裸 NALUs） |
| 详细方案 | artifacts: `native_video_plan.md`、`native_render_feasibility.md` |

## 二十六、语音录制功能（2026-03-19）

### 背景

聊天需要语音输入，能录音并作为音频文件附件上传。

### 技术难点

Tauri macOS WebView（WKWebView + HTTP）中 `navigator.mediaDevices` 为 `undefined`，`getUserMedia` 完全不可用。

### 方案：Rust cpal 原生录音

```
前端 → invoke('start_audio_recording')
        ↓
Rust: cpal 打开麦克风 → 采集 PCM f32 数据 → 缓存
        ↓
前端 → invoke('stop_audio_recording')
        ↓
Rust: 停止采集 → hound 写 WAV → base64 返回
        ↓
前端: base64 → File 对象 → attachments → 现有上传流程
```

### 改动文件

| 文件 | 改动 |
|:---|:---|
| `Cargo.toml` | 新增 `cpal = "0.15"` + `hound = "3.5"` |
| `src/audio_recorder.rs` | 新模块：录音状态管理 + cpal 采集 + WAV 编码 + base64 输出 |
| `src/lib.rs` | 注册 `mod audio_recorder` + 两个 Tauri command |
| `permissions/allow-app-commands.toml` | 新增 `start_audio_recording` / `stop_audio_recording` 权限 |
| `ChatInput.tsx` | 删除 MediaRecorder 代码 → 改用 `invoke` 调 Rust 录音，点击切换模式 |

### 注意事项

- `cpal::Stream` 不是 `Send`，用 `SendStream` newtype wrapper + `unsafe impl Send/Sync` 绕过
- WAV 格式通用性好但文件较大（48kHz 立体声 ~11MB/分钟），未来可压缩为 Opus
- macOS 首次使用需要授权麦克风权限（系统弹窗）
- 前端 UI：点击 🎙️ 开始 → 按钮变红脉冲+计时 → 再次点击停止

## 二十七、VideoToolbox 固定帧预算编码调研（2026-03-19）

### 背景

需要适配固定带宽信道（移动端 4G/5G），要求编码帧大小不超过信道带宽预算，且零额外延迟。

### 当前编码器架构

```
create_best_encoder() 优先级：
  1. macOS VideoToolbox GPU ← 当前在用（~2ms/帧，CPU ≈ 0%）
  2. FFmpeg 硬件编码  ← 未启用
  3. openh264 软编码   ← fallback
```

### H.264 帧大小不恒定的原因

- I 帧（IDR）：50-200KB，完整画面
- P 帧（无变化）：0.5-2KB
- P 帧（大变化）：10-50KB
- CBR 只是时间窗口平均码率恒定，单帧仍波动

### 解决方案：VT DataRateLimits 硬上限

VideoToolbox 的 `kVTCompressionPropertyKey_DataRateLimits` 属性：

```
DataRateLimits = [bytes_limit, seconds_limit]

举例：2 Mbps 信道, 30fps
  → 每帧预算 = 2M / 8 / 30 = ~8333 bytes
  → DataRateLimits = [8333 bytes, 0.033s]
```

效果：编码器内部自动调 QP，保证每 33ms 窗口内输出不超标。宁可降画质也不排队。

### I 帧突发解决

| 方案 | 原理 |
|:---|:---|
| 降低 IDR 频率 | `MaxKeyFrameInterval = 600`（20s） |
| **Intra Refresh** | 每帧别几行宏块，永远没有完整 IDR 突发 |

### 已实现（2026-03-19）

| 文件 | 改动 |
|:---|:---|
| `vt_encoder.rs` | 新增 `DataRateLimits` FFI（CFArrayCreate + kCFTypeArrayCallBacks），构造函数设 AverageBitRate=80% + DataRateLimits=100% |
| `encoder.rs` | 删除 `set_bitrate` trait 方法、`base_bitrate`、`calc_bitrate`；`create_best_encoder` 新增 `bandwidth_kbps` 参数 |
| `video_qos.rs` | 从 200 行精简到 33 行，只保留 `encode_failed` 检测 |
| `webrtc_hd.rs` | 删除 Layer1/Layer2 滑动窗口 + 场景预判 + 动态 `encoder_kbps`（~150 行） |
| `webrtc_vm.rs` | 删除每秒粗调 + per-frame 紧急刹车 + 带宽门控（~60 行） |

### 架构决策

- **删除动态码率 ABR**：DataRateLimits 是编码器硬件级硬上限，外部再调 `set_bitrate()` 会和它打架
- **保留动态帧率逻辑**：不在此次删除，因为动态帧率省电省包，与 DataRateLimits 不冲突
- **静态区域不受影响**：H.264 P 帧只编码变化区域，DataRateLimits 只在超标时介入

### 关键文件

| 文件 | 内容 |
|:---|:---|
| `vmcontrol/src/webrtc/vt_encoder.rs` | VT GPU 编码器，已设 AverageBitRate + DataRateLimits |
| `vmcontrol/src/webrtc/encoder.rs` | H264Encoder trait（无 set_bitrate） + openh264 fallback |
| `vmcontrol/src/webrtc/video_qos.rs` | 仅 encode_failed 检测，无 fps/ratio 调整 |
| `api/routes/webrtc_hd.rs` | HD 捕获循环，无滑动窗口码率控制 |
| `api/routes/webrtc_vm.rs` | VM 编码线程，无闭环反馈码率调整 |

---

## 二十八、HTTP→WS 全通道迁移（2026-03-20）

### 背景与决策

将所有操作型 HTTP 调用迁移到 AppBridge WS：
- **消除竞态**：chat_send 消息 ID 与 WS 推送在同一有序通道，不再乱序
- **减少延迟**：复用已建立的 TLS/WS 连接，无需新建
- **架构一致性**：App ↔ Gateway 只有一条双向通道

**原则：WS 未连接直接失败，不静默回退 HTTP。** 回退会掩盖连接问题，让用户看不到实际错误。

### 变更清单

| 文件 | 变更 |
|------|------|
| `src-tauri/src/core/app_bridge.rs` | 新增 `OutgoingMessage::Request`、`IncomingMessage::Response`；新增 `pending_requests: Arc<Mutex<HashMap>>` 字段；实现 `send_request()` 方法（30s 超时）；修复 E0597：clone Arc + 分两步 remove |
| `src-tauri/src/commands/gateway.rs` | 新增 `gateway_ws_request(action, path?, data?)` — WS 未连接直接返回 Err，移除 HTTP 回退逻辑 |
| `src-tauri/src/lib.rs` | 注册 `gateway_ws_request` 到 invoke_handler |
| `src-tauri/permissions/allow-app-commands.toml` | 添加 `gateway_ws_request` 权限 |
| `gateway/api/app_client.py` | 新增 `_handle_ws_request()`、`_dispatch_request()`；`app_ws_endpoint` 处理 `type=="request"` 消息 |
| `src/hooks/useWebRtc.ts` | `disconnect()` + `connect()` pre-stop 改用 `gateway_ws_request("webrtc_stop")` |
| `src/services/api.ts` | `sendChatMessage()` 改用 `gateway_ws_request("chat_send")`；`interruptAgent()` 改用 `gateway_ws_request("interrupt")` |

### Gateway 进程内 dispatch（无内部 HTTP）

`_dispatch_request` 直接调用进程内函数，不走任何 HTTP 中转：

```python
# webrtc_stop
await send_push_to_device(target_pc, "webrtc_stop", data)  # CloudBridge WS

# chat_send
message_repo = get_message_repo()
msg = message_repo.add_message(agent_id, "USER_MESSAGE", content_str, metadata)
notify_chat_subscribers(user_msg, user_id, agent_id)  # SSE broadcast

# interrupt
agent = get_agent()  # with ImportError fallback
agent.interrupt()
```

### 关键 imports（已验证在服务器 venv 可用）

```python
from gateway.db import get_database
from gateway.db.repositories import get_message_repo
from gateway.sse_state import notify_chat_subscribers
from gateway.api.deps import check_agent_access
```

### 后续 TODO

- [ ] `vm_start`/`vm_stop`/`android_start`/`android_stop` 迁移到 WS（当前暂未迁移，仍走 HTTP）
- [ ] 考虑 WS 连接断开时的前端提示（当前只是 invoke 报错，可加 toast 提示）

---

## 二十九、文件服务统一：/api/images/ → /api/files/（2026-03-20）

### 背景与决策

历史上文件存储有两套独立系统：
- **`/api/images/`**：Agent 截图，`ImageStorage` 直接写磁盘，Gateway 和 Runtime Orchestrator 各自维护
- **`/api/files/`**：聊天附件，File Service（novaic-storage-a）统一管理

两套系统导致：鉴权不一致、无法统一迁移到 OSS、前端需判断两个 URL 前缀。

**决策：全部统一到 /api/files/，/api/images/ 路由完全删除。**

### 变更清单

**Gateway（novaic-gateway）**

| 文件 | 变更 |
|------|------|
| `gateway/files/registry.py` | 新增：`files` 表 DDL（file_id/user_id/storage_key 等）；`register_file()`、`check_file_access()`、`delete_file_record()` |
| `gateway/files/__init__.py` | 新增：package init |
| `main_gateway.py` | 删除 4 个 `/api/images/` 路由（`get_image`、`get_image_with_subagent`、`get_image_stats`、`cleanup_images`）；upload 端点注册 file_id + user_id；GET `/api/files/{file_id}` 验证归属；DELETE `/api/files/{file_id}` 验证归属后删除 |
| `common/utils/image_storage.py` | 新增 `file_service_url` 参数；`save_image()` 分发到 `_save_via_file_service()`（POST `/api/files/from-base64`）或 `_save_to_disk()`（backward compat）；`resolve_image_to_base64` 支持 `/api/files/` URL |

**novaic-shared-runtime-common**

| 文件 | 变更 |
|------|------|
| `shared_runtime_common/common/utils/image_storage.py` | 同 Gateway 版本，加 `file_service_url` + `_save_via_file_service()` |

**Runtime Orchestrator（novaic-runtime-orchestrator）**

| 文件 | 变更 |
|------|------|
| `main_runtime_orchestrator.py` | lifespan 中 `set_image_storage(ImageStorage(file_service_url=...))` —— 截图写到 File Service |

**Frontend（novaic-app）**

| 文件 | 变更 |
|------|------|
| `src/services/api.ts` | `uploadChatFile` 返回 `file_id`；`sendChatMessage` attachments 包含 `file_id?` |
| `src/application/messageService.ts` | `Attachment.id = file_id ?? generated`；存储 `file_id` 字段 |
| `src/types/index.ts` | `Attachment` 接口加 `file_id?: string` |
| `src/components/Visual/SmartValue.tsx` | `isImageUrl` 只识别 `/api/files/`，删掉 `/api/images/` |

### 数据流（新）

```
截图（Agent/Execution Log）
  ImageStorage.save_image()
    → POST http://127.0.0.1:19995/api/files/from-base64
    → File Service 写磁盘 /opt/novaic/data/files/files/images/{agent_id}/xxx.png
    → 返回 URL: /api/files/images/{agent_id}/xxx.png

聊天附件
  前端 uploadChatFile()
    → Gateway POST /api/files/upload
    → 注册到 files 表，返回 { file_id, url }
    → file_id 存入 messageService Attachment.id

文件访问（鉴权）
  GET /api/files/{file_id}  → Gateway 查 files 表验证 user_id → 代理到 File Service
  GET /api/files/{any_path} → 历史兼容路径直接代理（无 registry 校验）
```

### 服务器状态（2026-03-20）

- `/opt/novaic/data/images/` — 已删除（历史文件已清空）
- `/opt/novaic/data/files/files/images/` — File Service 存新截图
- Gateway `[ImageStorage] Wired to File Service: http://127.0.0.1:19995` — 已确认
- Runtime Orchestrator `ImageStorage wired to File Service: http://127.0.0.1:19995` — 已确认

---

## 三十、实时同步与 WebSocket 稳定性修复（2026-03-20）

**问题背景**：客户端无法实时接收来自其他设备发出的消息和 Agent 运行日志，经常发生 WebSocket 短期内断开连接、消息未送达问题。

**排查与修复流程**：

### 1. Tauri (Rust) WebSocket Ping/Pong 解析修正
- **病因**：Rust 端的心跳机制之前误用协议层 WebSocket Ping 帧（`Message::Ping`）。而 Gateway FastAPI 端的 `app_ws_endpoint` 是通过接收 JSON `{"type": "ping"}` 处理心跳机制，进而重置 90 秒的断开超时时间。因为格式不匹配，心跳未被 Gateway 注册，导致 Gateway 在 90 秒无完整 API 请求后主动断开了 App 端的连接。
- **修复**：修改 `novaic-app/src-tauri/src/core/app_bridge.rs` 中心跳定时器的发送逻辑，改为发出 `{"type": "ping"}` 并在对端返回 `pong` 消息时正确重置。彻底解决了客户端随机掉线重连问题。

### 2. Gateway Python 推送线程静默异常修复
- **病因**：在 `sse_state.py` 里的 `_ws_push` 等消息分发逻辑，由于部分是通过非异步的 worker 或其他位置调用，原先的 `create_task()` 直接由于不在 async 事件循环内抛出 `RuntimeError: no running event loop` 并被 `debug` 日志静默吃掉。这使得很多重要的 WebSocket 推送从没进入到队列。
- **修复**：恢复了 `loop.create_task`（基于传入的或获取的 loop），将这种 `RuntimeError` 的捕捉升级为 `WARNING` 级别日志。
- **日志强化**：并在 `app_client.py::push_to_user` 内增加了 `INFO` 级别统计，详细打印事件（`chat_message`, `logs_updated` 等）成功推送的 clients 数量。

### 3. 前端 WS Message 捕获与去重
- **病因**：前端在 `sse.ts` 捕获到 WS 分发的事件后，对于 `USER_MESSAGE` 并没有回调给上层的 `messageService` 或 UI，只 `break` 出了 Switch，因此自己手机端发送的话，电脑端永远无法展示内容。
- **修复**：
  1. `sse.ts` 里对 `USER_MESSAGE` 调用 `onAgentReply` 并携带正确的 User ID 头像和内容。
  2. 加入去重保障。在 `messageRepo.ts` 中加入 `findTempByContent()` 按格式化文本查重。在 `messageService.ts` 收到 `USER_MESSAGE` 时，比对自己本地暂存或刚刚乐观保存（Optimistic Write）的相同结构信息，如果已经存在则直接丢弃，不导致 UI 短暂看到两条相同信息。解决了本地乐观更新和云端推回重复碰撞的问题。

---

## 三十一、iOS 构建失败：aws-lc-sys + Xcode 26.x 兼容性问题（2026-03-21，**未解决**）

### 问题现象

`./deploy ios` 执行 `tauri ios build` 时，`aws-lc-sys` crate 的 build script（通过 `cc-rs`）编译 HOST（macOS）端 C 代码失败：

```
error occurred in cc-rs: command did not execute successfully:
  "cc" "--target=arm64-apple-macosx" "-mmacosx-version-min=26.2" ...
  "-isysroot /path/to/iPhoneOS26.2.sdk" ...
  "-c" ".../aws-lc-sys-0.38.0/aws-lc/crypto/rand_extra/getentropy.c"
```

关键警告：`clang: warning: using sysroot for 'iPhoneOS' but targeting 'MacOSX'`

### 根因分析

1. **Xcode 26.3 beta** 的 macOS SDK 命名为 `MacOSX26.2.sdk`（而实际 macOS 是 15.7.4）
2. `xcodebuild` 在 iOS 构建环境中设置 `SDKROOT` 为 iPhoneOS SDK
3. `aws-lc-sys` 的 build.rs 使用 `cc-rs` 编译 HOST 端（macOS）代码，`cc-rs` 错误地使用了 iPhoneOS 的 sysroot 来编译 macOS 目标代码
4. 这导致两个问题：(a) sysroot 不匹配（iPhoneOS SDK 缺少 macOS 头文件），(b) `-mmacosx-version-min=26.2` 不合理

### aws-lc-sys 进入依赖树的路径

```
tokio-tungstenite → tokio-rustls (default features 含 aws_lc_rs)
                  → rustls (default features 含 aws_lc_rs)
                  → aws-lc-rs → aws-lc-sys
```

注意：`tauri-plugin-sql → sqlx → sqlx-core → rustls` 也通过 Cargo feature unification 参与了 `aws_lc_rs` feature 的启用。

### 为什么之前能构建？

最可能的原因：**Xcode 版本更新**。之前使用非 beta 的 Xcode（如 16.x），macOS SDK 命名为 `MacOSX15.x.sdk`，`-mmacosx-version-min=15.x` 完全正常，sysroot 也正确。更新到 Xcode 26.3 beta 后，SDK 路径和版本号发生了变化，导致 `cc-rs` 的自动检测逻辑出错。

### 已尝试但未成功的方案

| 方案 | 为什么不行 |
|------|-----------|
| `rustls = { default-features = false }` | Cargo feature unification：其他 crate 仍启用 `aws_lc_rs` |
| 顶层加 `tokio-rustls = { default-features = false, features = ["ring"] }` | 不能阻止 `rustls` 自身被其他 dep 启用 default features |
| `.cargo/config.toml` 设 `MACOSX_DEPLOYMENT_TARGET = "15.0"` | xcodebuild 环境的 `SDKROOT` 指向 iPhoneOS，cc-rs 用 SDKROOT 而非此变量来检测 |
| `run-ios-xcode-script.sh` 里 `export MACOSX_DEPLOYMENT_TARGET="15.0"` | cc-rs 不使用此变量来设置 sysroot，核心问题是 SDKROOT 不对 |
| 先 `cargo build --release` 再跑 iOS build（预热 HOST 缓存） | cargo fingerprint 不同（xcodebuild 环境变量不同），不复用缓存 |

### 推荐的下一步修复方向

**方向 A（修复 sysroot）**：在 `scripts/run-ios-xcode-script.sh` 里设置 `SDKROOT` 为 macOS SDK + `CFLAGS_aarch64_apple_darwin="-isysroot $(xcrun --sdk macosx --show-sdk-path)"`。当前已部分实现但未测试。需注意不能破坏 iOS 交叉编译（`tauri ios xcode-script` 通过 `--sdk-root` CLI 参数接收 iOS SDK 路径）。

**方向 B（移除 aws-lc-sys）**：使用 `[patch.crates-io]` 将 `aws-lc-rs` 替换为空 crate，或找到 Cargo 配置方式强制全局禁用 `rustls/aws_lc_rs` feature。

**方向 C（降级 Xcode）**：回退到正式版 Xcode（非 beta），macOS SDK 命名恢复正常。

### 当前文件状态

以下文件在本次 session 中被修改：

| 文件 | 状态 | 说明 |
|------|------|------|
| `novaic-app/src-tauri/Cargo.toml` | ⚠️ 已修改 | `rustls` 改回了 `features = ["ring"]`（无 default-features=false），`tauri-plugin-sql` 保留 |
| `novaic-app/src-tauri/Cargo.lock` | ⚠️ 已修改 | 从 commit `2d9a8ba` 恢复后被 `cargo generate-lockfile` 更新 |
| `novaic-app/scripts/run-ios-xcode-script.sh` | ⚠️ 已修改 | 加了 SDKROOT + CFLAGS 修复（未验证） |
| `novaic-app/src-tauri/.cargo/config.toml` | 🆕 新增 | MACOSX_DEPLOYMENT_TARGET force=true（可能无效，可删除） |
| `deploy` | ⚠️ 已修改 | deploy_ios() 加了 MACOSX_DEPLOYMENT_TARGET export（可能无效） |
| `novaic-app/package.json` + `package-lock.json` | ⚠️ 已修改 | NPM 包版本对齐到 Cargo crate 版本 |


## 三十二、LLM Factory 集中化重构（2026-03-22）

### 架构概述

**决策**：所有 LLM 调用统一走 LLM Factory 的 `POST /v1/chat/completions` 端点。api_key 只在 Factory 内部解密，其他服务（Gateway、agent-runtime、tools-server、runtime-orchestrator）不接触明文密钥。

**动机**：之前 api_key 在多个服务间传递（Gateway resolve → agent-runtime 直接调 OpenAI），存在安全风险和维护负担。

```
调用方（agent-runtime / tools-server / orchestrator）
  → Gateway: 查 agent.model_id + user.default/audio_model
  → 返回 {model_id, model_name, user_id, factory_url}（不含 api_key）
  → Factory POST /v1/chat/completions
  → Factory 内部: resolve_model → 解密 api_key → 创建 provider → 调 LLM → 记日志 → 返回结果
```

### LLM Factory 服务

| 项目 | 值 |
|---|---|
| 域名 | `newapi.gradievo.com` |
| SSH | `ssh root@newapi.gradievo.com` |
| 代码路径 | `/opt/novaic/llm-factory` |
| 端口 | 19990（systemd: `llm-factory.service`） |
| 部署 | `./deploy factory` |
| 数据库 | SQLite（加密存储 api_key） |

**Factory API 端点**：

| 端点 | 用途 |
|------|------|
| `POST /v1/chat/completions` | LLM 代理调用（唯一 LLM 出口） |
| `GET/POST/DELETE /v1/config/api-keys/*` | 管理 API Key（前端设置页） |
| `GET/POST/PUT/DELETE /v1/config/models/*` | 管理模型 |
| `GET /v1/config/models/{model_id}` | 查询单个模型元数据（不含 api_key） |
| `POST /v1/config/api-keys/{id}/test` | 测试 API Key 有效性 |
| `GET /v1/config/api-keys/{id}/fetch-models` | 从 provider 拉取可用模型 |
| `GET /v1/logs` | 查询 LLM 调用日志 |

**已删除的端点**（安全加固）：
- ~~`GET /v1/config/resolve`~~（返回明文 api_key，已删除）
- ~~`GET/PUT /v1/config/defaults/{user_id}`~~（用户偏好迁至 Gateway 本地 DB）

### 改动文件清单

| 服务 | 文件 | 改动 |
|------|------|------|
| **agent-runtime** | `task_queue/factory_client.py` (新) | `FactoryLLMClient` — 接口兼容 `OpenAIClient.chat()`，实际 POST Factory |
| **agent-runtime** | `task_queue/handlers/llm_handlers.py` | 3 个 handler 全部使用 `FactoryLLMClient`；广播用 `model_display`（人类可读名字） |
| **agent-runtime** | `task_queue/handlers/summary_handlers.py` | `handle_merge_history` 使用 `FactoryLLMClient` |
| **tools-server** | `tools_server/executor.py` | `audio_qa` 直接 POST Factory，删除 provider 分支 |
| **orchestrator** | `gateway/core/task_manager.py` | `_generate_summary` 直接 POST Factory |
| **gateway** | `gateway/api/internal/factory_client.py` | 删除 `resolve_model_from_factory`/`set_user_defaults`；新增 `_resolve_model_name` 带 TTL 缓存 |
| **gateway** | `gateway/api/routes.py` | `GET /config` 从本地 DB 读 defaults；`set_default_model` 写本地 DB |
| **factory** | `factory/routes/config_routes.py` | 删除 `/resolve`、`/defaults` 端点；新增 `GET /models/{model_id}` |

### 用户偏好存储（default_model / audio_model）

**单一来源**：Gateway 本地 `config` 表（SQLite）。

| 操作 | 端点/方法 | 存储 |
|------|-----------|------|
| 设置默认模型 | `POST /api/config/default-model` | Gateway config 表 |
| 设置语音模型 | `PATCH /api/config/settings` `{audio_model}` | Gateway config 表 |
| 读取（前端设置页） | `GET /api/config` → `default_model` 字段 | Gateway config 表 |
| 读取（LLM 调用时） | `build_llm_config_for_agent_via_factory()` | Gateway config 表 |

### Model Name 缓存

`_resolve_model_name(model_id)` 在 Gateway 内存缓存 model_id → model_name 映射：
- **命中**：直接返回（0ms）
- **未命中**：调 Factory `GET /models/{model_id}`，缓存 5 分钟
- **Factory 不可达**：fallback 用 UUID，30s 短 TTL 后重试

权威来源始终是 Factory，Gateway 只缓存避免重复调用。

### 查看 Factory 日志

```bash
# 从 Factory 机器查最近调用日志
ssh root@newapi.gradievo.com 'curl -s "http://127.0.0.1:19990/v1/logs?limit=5"'
```

## 三十三、多端配置同步 & SSE Legacy 清除（2026-03-22）

### 问题

1. **Agent 模型保存后再次进入显示空**：`GET /{agent_id}/model` 查 Gateway 本地 `candidate_models` 表，但表中模型 ID 是旧格式（非 UUID），与 Factory 的 UUID 不匹配
2. **双端模型列表不一致**：一端改了 audio_model / default_model / agent model，另一端看到的还是旧值
3. **SSE 命名误导**：`sse_state.py`、import、注释都说 SSE，但实际通道是 WS push

### 解决方案

#### Agent 模型持久化

`agents.py` 里 `GET/PUT /{agent_id}/model` 改为调 Factory `get_models(user_id)` 获取权威模型列表。不再查本地 `candidate_models` 表。

#### 多端配置同步（WS push 通知 + 按需拉取）

```
客户端 A 改 audio_model
  → Gateway 写 DB + push_to_user("config_updated", {scope:"settings"})
  → 客户端 B 的 SSEManager 收到 config_updated 事件
  → SyncService.debouncedReloadConfig()（500ms 去抖）
  → modelService.loadConfig()（从服务端重新拉取全部配置）
  → Zustand store 更新 → UI 自动刷新
```

**Gateway 端**（3 个触发点）：

| 函数 | 文件 | scope |
|------|------|-------|
| `update_settings` | `routes.py` | `settings` |
| `set_default_model` | `routes.py` | `default_model` |
| `set_agent_model` | `agents.py` | `agent_model` |

均通过 `_broadcast_config_updated(user_id, scope)` → `push_to_user()` 广播。

**前端**：
- `gateway/sse.ts`：`SSEManager` 增加 `config_updated` 事件处理
- `application/syncService.ts`：`onConfigUpdated` handler 调用 `debouncedReloadConfig()`

#### SSE Legacy 清除

| 项目 | 变更 |
|------|------|
| `gateway/sse_state.py` | 重命名 → `gateway/push_state.py` + 删除所有 SSE queue 代码（163 → 85 行） |
| 6 个 import 文件 | `sed` 批量替换 `gateway.sse_state` → `gateway.push_state` |
| `main_gateway.py` | 删除 `GET /api/user/chat/stream` 和 `/api/user/logs/stream` 两个 SSE 端点（~60 行） |
| `main_gateway.py` | 删除 `register/unregister_*_subscriber` import |
| 注释清理 | `main_gateway.py` ~20 处 "SSE" → "WS push" |
| `gateway/sse.ts` | 日志前缀 `[SSEManager]` → `[PushManager]` |
| `syncService.ts` | 日志 "SSE" → "WS" |

**保留不动的**：`gateway/sse/broadcaster.py`（Worker SSE）——这是 Gateway→Worker 进程间通信，属于不同层级。

## 三十四、Gateway 迁移至 Entangled 数据流部署修复（2026-03-26）

### 问题背景

在完成了 Entangled 基础设施的重排以及 `novaic-gateway` 后端依赖代码的切割后，尝试部署到 `api.gradievo.com` 时遭遇严重阻碍，导致服务无法启动。主要问题包含底层环境的依赖缺失、数据库 DDL 语句锁级别导致的 SQLite 死锁、以及 Entity 继承与底层 schema 处理的生命周期错位。

### 核心崩溃点与修复记录

#### 1. Entangled 模块依赖解析失败

**故障**：`gateway/api/internal/pc_client.py` 内部调用的 `import entangled.server` 等操作在服务器环境中出现 `ModuleNotFoundError`。但在本地开发环境中（Pycharm）正常工作。
**根因**：服务器环境和部署构建 (`./deploy gateway` 和 `./deploy services`) 在设计时只专注对 `novaic-gateway`（以及各微服务 repo）进行同步。由于 Entangled 现重构作为一个独立的子仓库，它在服务器的 `/opt/novaic/Entangled` 路径下缺失代码，导致 Python `sys.path` (即 `__file__.parent.parent / 'Entangled...`) 加载失败。
**修复**：在 `deploy` 核心脚本的 `deploy_gateway_func` 及 `rsync_all` 函数中增加了对 `Entangled/`（排除了 `packages/client-rust`、`node_modules`）的强制 rsync 同步。确保了 `gateway` / `tools` / `runtime` 启动前一定拥有最新的 `entangled.server` 包副本。

#### 2. DDL SQLite Scheme 构建死锁（LockType Sharded）

**故障**：服务尝试执行 `gateway.entity.store.EntityStore.ensure_schema` 创建底层表结构时抛出 `ValueError`。
**根因**：原定 `ensure_schema()` 会引用该实体指定的默认 `lock_type`（比如 `skills` 是 `ShardedFIFOLock`)，但 sharded lock 要求传入 `resource_id` 参数。由于 `CREATE TABLE / ALTER TABLE` 这样的 DDL 语言属于数据库全局操作，并不涉及资源子集，因此强行利用局部锁导致锁工厂报措。
**修复**：修改 `store.py` 内部机制，令 `ensure_schema` 内的 `self.db.transaction()` 实参强行固定传入 `"global"`，不再复用具体的实例 `lock_type`。

#### 3. AgentState Timestamp 空白指针对齐崩溃

**故障**：`/api/subagents/xxx/awake` 等核心守护进程发出的状态转换使得 `EntityStore.upsert('agent-state', ...)` 触发，抛出 SQLite `OperationalError: no such column: updated_at`。
**根因**：在 `EntityDef` 默认中 `auto_timestamps = True`。框架会自动尝试注入 `updated_at = datetime('now')` 到 `upsert` 的 `UPDATE` 参数里。然而在 `gateway/entity/defs.py` 关于 `AGENT_STATE` 的 `fields` 列表里没有明确定义该列（因为该模型实际设计只使用了 `last_active_at`）。由于 `ensure_schema` 检测不到应当创建该列，造成后续注入该列时 SQL 引擎报错。
**修复**：直接在 `gateway/entity/defs.py` 的 `AGENT_STATE` 定义末尾补充了 `auto_timestamps=False` 后端开关。

#### 4. SubagentStatus 全局变量缺失报错

**故障**：内部 Daemon 服务轮询 `get_subagents_due_for_wake` 并调用 `set_subagent_sleeping` 强制将 SubAgent 切入睡眠状态时应用层崩溃：`NameError: name 'SubagentStatus' is not defined.`
**根因**：API 拆分与迁移重排后，遗漏了 `common.enums` 的依赖包倒入。
**修复**：在 `gateway/api/internal/subagent.py` 头加入了 `from common.enums import SubagentStatus`，修复调度挂起 bug。

### 总结

以上 4 个点阻塞了 Entangled 代码树的第一版全面部署。修复完成后，`api.gradievo.com` 的 Gateway 能正常连通至本地 SQLite 以及拉起所有后端服务，`19999` 端口顺利监听。客户端终于可以正常与重排过的 Entangled 数据层交互。
