# NovAIC 项目交接文档（2026 重构版）

> 最后更新：2026-04-02 — **Skills 领域文档 + OpenClaw 子模块**：新增 `docs/skills-domain-investigation-reports.md`（五份独立子领域报告：发现与存储、Prompt/Token、运行时匹配与 Agent 绑定、安装分发与市场、安全运维；对照 OpenClaw 文件模型与 NovAIC 的 DB+builtin `mcp_client/skills`）。**`thirdparty/openclaw`** 为 `.gitmodules` 登记的 **git 子模块**（上游 `openclaw/openclaw`），用于代码级审计与能力对比；初始化：`git submodule update --init thirdparty/openclaw`。架构速览仍见 `docs/agent-approve-points/02-openclaw-architecture.md`。OpenClaw 侧可借鉴点（skills 多根合并/compact 限额、tool profile、before_tool_call 类钩子）见该调查报告与对话归档，**不**改变当前 NovAIC 运行时拓扑。
> 最后更新：2026-04-01 — **Sync Contract 审查修复**：`/api/app/ws` 首次 **schema push** 的 `data` 已含 **`syncContractVersion`**（`gateway.entity.sync_contract`，与 REST、Entangled `ws_handler` 一致；此前 AppWS 仅 `{ entities, hash }`，桌面多靠 REST 设 Rust 原子量）。**`tests/unit/gateway/test_sync_contract_schema.py`**：无 monorepo 下 `Entangled/packages/server-python` 时 **skip** 与 `ws_handler` 的版本 parity，独立 checkout `novaic-gateway` 的 CI 可过。**桌面**：`App.tsx` 中 `handleSelectAgent` / `handleAgentCreated` 依赖 **`agents`** 防陈旧闭包；**登出** 置 **`settingsOpen: false`**；CloudBridge 日志仅记 token **长度**（不打印前缀）。**`client.ts`**：`syncContractVersion` 非有限数字时 **`console.warn`**。**`app_bridge.rs`**：慢路径 / join 失败日志与模块注释统一为 **`process_sync_with_contract`**。
> 最后更新：2026-04-01 **Sync Contract Phase 1–3**：规范与清单见 `docs/SYNC_CONTRACT.md`、`docs/sync-contract-execution-checklist.md`。要点：主槽 `navChanged`/`nav_release_slot` 串行 + Rust 每槽 `tokio::Mutex`；Gateway REST/WS schema 携带 `syncContractVersion`（`gateway/entity/sync_contract.py` 与 Entangled `ws_handler.SYNC_CONTRACT_VERSION` 须同号）；Rust `process_sync_with_contract` 在合约 ≥2 且 snapshot/head_n 缺 `idField` 时记 ERROR（`metric=sync_frame_missing_id_field_v2`，仍用 build 回退）；TS `loadSubscriptionSchema` 解析 `{ entities, syncContractVersion }` 并 `invoke('entangled_set_sync_contract_version')`，`defaultIdFieldForEntity` 优先用 schema 的 `idField`。**1.4**：`deriveDesiredMainNav`（`nav.ts`）+ `App.tsx` 单一 effect；**1.3**：`npm run verify:sync-contract-schema`（需环境变量）+ 发版前仍建议桌面清缓存 spot-check。
> 最后更新：2026-04-01 — **Form 写后 UI + agent-binding + 执行日志预览**：非乐观 `upsert` 成功即用返回行 `setQueryData` 并 invalidate（`hooks.tsx` `createFormStore`）；`agent-binding` 支持无记录 `allowMissing`、无设备保存用 `bindingData?.device_id` 触发清绑（`agentBinding.ts`、`AgentToolsPanel.tsx`）；`ChatPanel` 主 Agent 日志预览改 `flex justify-center px-4`，避免 Framer Motion 与 `translate-x` 抢 `transform`。细节与排障见 **§十五** 表内三行新条目。
> 最后更新：2026-04-01 **全局订阅丢失与主键解析 Bug 排查**：定位了清空本地缓存后 models/skills/devices 数据消失的线上问题。根因之一（时序竞争）：`App.tsx` 启动时 `navChanged('home')` 和 `navChanged('conversation')` 并发使用默认 `slot: "main"`，发生即时覆盖，导致 `home` 被迅速取消订阅。根因之二（主键硬编码）：Rust Entangled 客户端底层持久化时硬编码查找 JSON 属性 `"id"`，而针对主键非 `id`的实体（如 models 为 `model_id`），在连接不含升级补丁的云端 Gateway（未下发 `idField` 机制）时被默默丢弃。相关修复计划转移至纯客户端侧，如提供基于 schema 的回退机制或拆分独立 slot。
> 最后更新：2026-03-31 **Agent-Binding 持久化修复**：彻底修复了 agent-device 绑定保存后消失的问题。根因：前端 dispatch `update`（SQL UPDATE），但绑定记录可能不存在 → 0 行更新；且 `nav.rs` 路由表缺少 `agent-binding` 订阅导致 Rust 缓存永远为空，UI 读不到数据。修复：`agentBinding.ts` 改 `optimistic:false` 走 `upsert`；`nav.rs` conversation/settings 路由新增 `agent-binding(agentId)` 订阅；`App.tsx` settings 打开时传 `agentId`；`useAgentBinding.ts` 完全迁移至 `agentBindingStore.useForm()`，设备面板实时响应。
> 本文档由原始近 3000 行变更日志按功能模块重新组织，完整保留所有有价值的技术细节、文件速查、排障指南与架构决策。

---

## 一、快速上手

| 需求 | 操作 |
|---|---|
| 本地跑起来 | `cd novaic-app && npm install && npm run tauri:dev` |
| 纯 UI 调试 | `cd novaic-app && npm run dev` (http://localhost:5173) |
| **部署前端 OTA** | `./deploy frontend [version]` |
| **部署 Gateway** | `./deploy gateway` |
| **部署全部后端** | `./deploy services` |
| **部署 Relay** | `./deploy relay` |
| **构建安装 iOS** | `./deploy ios` |
| **构建桌面 App** | `./deploy desktop` |
| **部署全部** | `./deploy all [version]` |
| **查看服务状态** | `./deploy status` |
| **查看日志** | `./deploy logs [gateway|orchestrator|tools|runtime|worker|relay]` |
| 改前端 UI | 改 `novaic-app/src/components/`，热更新生效 |
| 改消息/日志逻辑 | `messageService.ts`、`logService.ts`、`syncService.ts` |
| 改远程桌面连接 | `useWebRtc.ts`、`WebRtcScrcpyView.tsx`（统一 WebRTC，noVNC 已全部移除） |
| 改设备操控台 | `DeviceConsole.tsx`、`ConsoleToolbar.tsx`、`useWebRtc.ts`、`useRemoteInput.ts` |
| 清空本地缓存 | Settings → Clear Cache → 清空本地 DB 缓存 |
| 查架构 | `novaic-app/FRONTEND_ARCHITECTURE.md`、`docs/design/DESIGN-P2P-UNIFIED.md` |

---

## 二、项目整体架构

### 2.1 OTA-First 薄壳架构

彻底重构为**基于云端 OTA 的 Thin Client (薄壳) 模式**：
1. **体积缩减百倍**：Release 仅内嵌 24KB 静态 Loading 页面（`src-tauri/loading/index.html`）
2. **纯云端按需加载**：启动后请求 Relay CDN 获取最新包跳转，修 Bug 通过 `./deploy frontend` 秒发版
3. **Rust 原生 API 透传前端**：集成 `@tauri-apps/plugin-sql`（底层 `sqlx 0.8.0`），OTA 前端可直接操作本地 SQLite

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

### 2.2 macOS SIGTRAP 崩溃修复（全面修复）

**根因**：`enigo.key()` / `enigo.text()` 内部调用 macOS `TSMCurrentKeyboardInputSourceRefCreate`，**必须在 main dispatch queue 执行**。tokio worker 线程调用触发 `dispatch_assert_queue` 断言失败 → SIGTRAP。

**修复**：macOS 上所有 enigo 键盘操作替换为 `CGEvent`（`core_graphics` crate，线程安全）。

| 文件 | 改动 |
|------|------|
| `vmcontrol/src/input/handler.rs` | `sync_modifiers()` / `release_all_keys()` 改用 `send_modifier_event()`（CGEvent）|
| `vmcontrol/src/api/routes/hd_tools.rs` | `hd_keyboard()` 全部替换为 `hd_cg_key_event()` / `hd_cg_type_string()` |
| `vmcontrol/src/input/handler.rs` | 未知键 fallback 从 `enigo.key()` 改为 `cg_type_string()` Unicode 注入 |

**结论**：macOS 上 **零** `enigo.key()` / `enigo.text()` 调用残留。鼠标操作（move/button/scroll）不触发 TSM，保留 enigo。

### 2.3 TURN 服务器与凭证流转

**coturn 配置**：`/etc/turnserver.conf`（端口 3478 UDP/TCP，realm gradievo.com，use-auth-secret）

**TURN 凭证流转架构（当前）**：Gateway 统一注入 TURN 凭证到 `webrtc_offer` 消息，VmControl 直接使用。

| 端 | 凭证来源 | 关键文件 |
|---|---|---|
| **客户端** (useWebRtc.ts) | Gateway HTTP `/api/turn/credentials` 返回 | `useWebRtc.ts`, `gateway/api/turn.py` |
| **VmControl** (peer.rs) | Gateway 注入到 webrtc_offer 的 `ice_servers` 字段（回退：本地 `build_ice_servers()`） | `peer.rs::parse_ice_servers_json()` |

**TLS 证书权限**：coturn 以 `turnserver` 用户运行，Let's Encrypt 需 `chmod 755` + privkey `chgrp turnserver`。
**coturn 长时间运行问题**：跑 6+ 天后积累僵尸 session，重启即恢复。

---

## 三、代码仓库与目录结构

父仓库 `chriswangcq/novaic`（默认 `main`），服务与依赖多为 **git submodule**（见 `.gitmodules`；含 **`thirdparty/openclaw`** 等参考树，非线上服务）。

```bash
git clone --recurse-submodules git@github.com:chriswangcq/novaic.git
# 已 clone 后初始化：git submodule update --init --recursive
```

| Submodule | 用途 |
|---|---|
| `novaic-app` | Tauri 桌面+移动端应用 |
| `novaic-gateway` | 云端 Gateway（API + DB） |
| `novaic-llm-factory` | LLM Factory（集中化 LLM 代理） |
| `novaic-quic-service` | STUN + Relay（P2P 兜底） |
| `novaic-agent-runtime` | Agent 运行时 |
| `novaic-runtime-orchestrator` | 运行时编排器 |
| `novaic-tools-server` | 工具服务 |
| `novaic-mcp-vmuse` | MCP VMuse 集成 |
| `novaic-contracts` | 共享协议/类型定义 |
| `novaic-shared-kernel` | 共享核心库 |
| `novaic-shared-runtime-common` | 共享运行时公共库 |
| `novaic-storage-a / b` | 存储服务 |
| `novaic-control-plane` | 控制面板 |
| `thirdparty/openclaw` | 上游 OpenClaw 源码（参考/审计；Skills & Gateway 行为对比） |

```
new-build-novaic/
├── HANDOVER.md / NEW_HANDOVER.md   # 交接文档
├── deploy                          # 统一部署 CLI
├── .gitmodules                     # submodule 清单（含 novaic-* 与 thirdparty/openclaw）
├── docs/                           # 文档（含 `skills-domain-investigation-reports.md`、`SYNC_CONTRACT.md`、`agent-approve-points/`）
├── thirdparty/openclaw/            # OpenClaw 子模块（需 init）
├── scripts/                        # 构建/部署/运维脚本
└── 各 submodule 子目录
```

---

## 四、本地开发

### 4.1 环境准备

```bash
node >= 18, npm >= 9
rustup + cargo (stable)
xcode-select --install  # macOS only
```

### 4.2 启动开发

```bash
cd novaic-app
npm install
npm run dev           # 纯 UI（http://localhost:5173）
npm run tauri:dev     # 含 Rust VmControl
```

> ⚠️ Port 1420 被占：`kill $(lsof -ti:1420)`
> ⚠️ **不要**用 `npm run tauri build --ci`，正确命令：`npm run tauri:build -- --bundles app`

---

## 五、构建与发布

### 5.1 桌面 App

```bash
cd novaic-app
npm run tauri:build -- --bundles app
# 输出: src-tauri/target/release/bundle/macos/NovAIC.app
cp -r src-tauri/target/release/bundle/macos/NovAIC.app /Applications/NovAIC.app
```

### 5.2 iOS 部署流程（完整）

**一键构建安装**：`cd novaic-app && ./scripts/build-and-install-ios.sh`

**手动分步**：
```bash
test -d src-tauri/gen/apple || env -u CI tauri ios init
bash scripts/patch-ios-xcode.sh
npm run tauri:build:ios:debug
IPA_PATH="src-tauri/gen/apple/build/arm64/NovAIC.ipa"
DEVICE=$(xcrun devicectl list devices 2>/dev/null | awk '/connected/ && !/Simulator/ {for(i=1;i<=NF;i++) if($i~/^[0-9A-F]{8}/) {print $i;break}}' | head -1)
xcrun devicectl device install app --device "$DEVICE" "$IPA_PATH"
```

**⚠️ 为何不用 `tauri ios run`**：`-exportOptionsPlist` 传相对路径 bug，xcodebuild 找不到临时文件。

**iOS 关键脚本**：

| 脚本 | 用途 |
|---|---|
| `scripts/patch-ios-xcode.sh` | 移除 FORCE_COLOR（导致 arch 参数错误）；改用 `run-ios-xcode-script.sh` |
| `scripts/run-ios-xcode-script.sh` | Xcode 构建阶段 cd 到项目根执行 npm |
| `scripts/build-and-install-ios.sh` | 完整流程 |

**iOS 黑屏修复**：
1. iOS 构建使用 `--features mobile` 而非 `custom-protocol,mobile`（WKWebView 黑屏）
2. `config/index.ts` 未设置 VITE_GATEWAY_URL 时兜底 `https://api.gradievo.com`
3. `tauri.ios.conf.json` 覆盖桌面配置

**iOS 键盘原生修复（main.mm）**：
- 移除 WKWebView 键盘通知观察者 → 阻止 iOS 自动滚动
- 注册自定义监听 → 精确键盘高度 → 注入 CSS `--keyboard-height`
- `LayoutContainer.tsx` 移动端用 `position: fixed; bottom: var(--keyboard-height, 0px)`
- `ffi::start_app()` 启动 UIKit run loop 且永不返回，所有 `dispatch_after` 必须在它之前调用
- `index.html` viewport **不含** `interactive-widget=`（WebKit 忽略该 token，仅减控制台噪音）；键盘与视口布局以 **main.mm + `LayoutContainer`** 为准，不依赖该 meta。

**iOS Xcode 26.x 兼容性问题（未解决）**：`aws-lc-sys` crate 在 Xcode 26.3 beta 下因 SDKROOT 指向 iPhoneOS 而非 macOS SDK 导致交叉编译失败。推荐降级到正式版 Xcode 或手动注入 CFLAGS。

### 5.3 Android

```bash
npm run tauri:build:android   # 使用 custom-protocol（与 iOS 不同）
```

---

## 六、统一部署 CLI（`./deploy`）

```bash
# ── 客户端 ──
./deploy frontend [ver]    # 构建前端 + rsync 到 relay OTA (默认 v0.3.0)
./deploy ios               # 构建 IPA + 安装到已连接 iPhone
./deploy desktop           # 构建 macOS .app

# ── 后端服务 (api.gradievo.com) ──
./deploy gateway           # rsync + start.sh 全部重启
./deploy runtime / orchestrator / tools / storage-a / storage-b
./deploy services          # rsync 全部 + start.sh 重启（推荐）

# ── 基础设施 ──
./deploy relay             # git pull + cargo build + systemctl restart
./deploy factory           # rsync + systemctl restart llm-factory

# ── 运维 ──
./deploy status / logs [svc] / all [ver]
```

**原理**：`./deploy` **只负责 rsync 同步代码**，进程管理交给服务器端 `/opt/novaic/start.sh`。

> ⚠️ `restart_gw.sh` 已删除。单独重启 Gateway 会导致服务状态不一致。**所有重启必须走 `start.sh`。**

---

## 七、云端部署详细说明

### 7.1 Gateway（api.gradievo.com）

| 项目 | 值 |
|---|---|
| SSH | `ssh root@api.gradievo.com` |
| 代码路径 | `/opt/novaic/services/novaic-gateway` |
| 数据目录 | `/opt/novaic/data/` |
| 数据库 | `/opt/novaic/data/gateway.db` (SQLite) |
| 依赖 | `/opt/novaic/jwt_secret.env` 含 `JWT_SECRET`、`TURN_SECRET`、`FRONTEND_CDN_URL` |
| 日志 | `tail -f /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log`；App WS 排障：`grep -E '\[AppWS\]|Message loop crashed' ...` |

**Gateway 启动参数**：
```
--host 127.0.0.1 --port 19999 --data-dir /opt/novaic/data
--runtime-orchestrator-url http://127.0.0.1:19993
--queue-service-url http://127.0.0.1:19997
--tools-server-url http://127.0.0.1:19998
--file-service-url http://127.0.0.1:19995
--tool-result-service-url http://127.0.0.1:19994
```

**Nginx 配置**（`/etc/nginx/sites-enabled/novaic`）：
- `auth_request → /internal/auth/validate`，注入 `X-User-ID`，剥离客户端伪造头
- CloudBridge WebSocket `/internal/pc/ws` 超时 3600s
- 前端 OTA `/api/config/frontend` 无需 JWT，限流 burst=30

**后端共 16 个 Python 进程**：6 HTTP 服务 + 4 task-worker + 2 saga-worker + watchdog + health + scheduler + STUN。

### 7.2 Relay / STUN（relay.gradievo.com）

| 项目 | 值 |
|---|---|
| SSH | `ssh -p 52222 root@47.243.221.45` |
| 代码路径 | `/opt/novaic/novaic-quic-service` |
| systemd | `novaic-quic-service.service` |
| 端口 | STUN 3478 UDP / Relay 443 QUIC / Nginx 80/443 静态 |

**部署**：`./deploy relay`（或手动 git pull + cargo build + systemctl restart）

**前端热更新部署**：
```bash
# 1. 构建
cd novaic-app && VITE_BASE="/resource/frontend/v0.3.0/" npm run build
# 2. 推送
rsync -avz --delete -e "ssh -p 52222" dist/ root@47.243.221.45:/opt/novaic/static/v0.3.0/
# 3. 更新 Gateway 配置
# jwt_secret.env: FRONTEND_CDN_URL=https://relay.gradievo.com/resource/frontend/v0.3.0/
```

**OTA 三处同步**（新增 CDN 域名时必须同时修改）：

| 位置 | 修改项 |
|------|--------|
| `src/config/index.ts` | `OTA_ORIGINS` 数组 |
| `src-tauri/capabilities/remote-frontend.json` | `remote.urls` |
| `src-tauri/src/setup.rs` | `OTA_ALLOWED_HOSTS` 常量 |

CI 校验：`scripts/check-ota-sync.sh`。

### 7.3 LLM Factory（newapi.gradievo.com）

| 项目 | 值 |
|---|---|
| SSH | `ssh root@newapi.gradievo.com` |
| 代码路径 | `/opt/novaic/llm-factory` |
| 端口 | 19990（systemd: `llm-factory.service`） |
| 部署 | `./deploy factory` |
| 查日志 | `ssh root@newapi.gradievo.com 'curl -s "http://127.0.0.1:19990/v1/logs?limit=5"'` |

**API 端点**：

| 端点 | 用途 |
|------|------|
| `POST /v1/chat/completions` | **唯一 LLM 出口** |
| `GET/POST/DELETE /v1/config/api-keys/*` | 管理 API Key |
| `GET/POST/PUT/DELETE /v1/config/models/*` | 管理模型 |
| `POST /v1/config/api-keys/{id}/test` | 测试 Key |
| `GET /v1/config/api-keys/{id}/fetch-models` | 拉取 provider 模型 |
| `GET /v1/logs` | 调用日志 |

**已删除端点**：~~`/resolve`~~（返回明文 api_key）、~~`/defaults`~~（迁至 Gateway）。

### 7.4 服务器数据维护

| 项目 | 命令 |
|---|---|
| **Orchestrator 已完成 context** | `sqlite3 runtime_orchestrator.db "UPDATE agent_runtimes SET context='[]' WHERE status='completed'; VACUUM;"` |
| **Queue 已完成任务** | `sqlite3 queue.db "DELETE FROM tq_tasks WHERE status IN ('done','failed'); DELETE FROM tq_sagas WHERE status!='active'; VACUUM;"` |
| **日志轮转** | `find /opt/novaic/data/logs/ -name '*.log' -mtime +7 -delete` |
| **日志截断** | `find /opt/novaic/data/logs/ -name '*.log' -size +50M -exec truncate -s 10M {} \;` |

> ⚠️ **禁止运行时执行 `PRAGMA wal_checkpoint(TRUNCATE)`**，会截断未提交事务数据。

**Gateway 卡死恢复**：
```bash
kill -9 $(pgrep -f main_gateway.py) && sleep 2
rm -f /opt/novaic/data/gateway.db-wal /opt/novaic/data/gateway.db-shm
bash /opt/novaic/start.sh
```

---

## 八、认证体系（自定义 JWT）

### 8.1 完整流程

```
用户 → POST /auth/login → Gateway 返回 HS256 JWT + refresh_token
     → 存入 localStorage → App.tsx 调 update_cloud_token(jwt) 推给 Rust
     → Rust gateway_*/CloudBridge 请求携带 Authorization: Bearer <jwt>
     → Nginx auth_request → /internal/auth/validate → 提取 sub → 设置 X-User-ID
     → Gateway Depends(get_current_user) 读取 X-User-ID
     → 所有 DB 操作携带 user_id 过滤
```

### 8.2 Token 参数

| 参数 | 值 |
|---|---|
| 签名算法 | HS256 |
| Access Token TTL | 60 分钟 |
| Refresh Token TTL | 30 天（轮换式） |
| 前端刷新 | 距过期 < 5 分钟自动 `/auth/refresh`；每 55 分钟推送最新 token 给 Rust |
| JWT_SECRET 位置 | `/opt/novaic/jwt_secret.env` |

### 8.3 多用户数据隔离

- 所有业务表均有 `user_id` 字段，Repository 查询强制 `WHERE user_id = ?`
- SSH Key 路径：`{DATA_DIR}/.ssh/id_rsa_{user_hash}`（sha256 前 16 位）
- 客户端伪造的 `X-User-ID` 在 Nginx 层被强制置空

### 8.4 关键文件

| 文件 | 用途 |
|---|---|
| `src/services/auth.ts` | login/register/logout/getAccessToken()，55min 自动 refresh |
| `src/App.tsx` | AuthScreen，pushToken → Rust |
| `src-tauri/src/setup.rs` | Gateway URL、StorageBackend 统一注入 |
| `vmcontrol/src/cloud_bridge.rs` | WebSocket 握手读取 token |
| `gateway/api/auth.py` | login/register/refresh/logout/validate |
| `gateway/infra/deps.py` | `get_current_user`（Bearer JWT 优先；`X-User-ID` 须与 `sub` 一致；`TRUST_GATEWAY_X_USER_ID`）、`verify_internal_tasks`（`/api/internal/tasks*`，见环境变量） |
| `gateway/nginx/novaic-cloud.conf` | auth_request 配置 |

### 8.5 环境变量（与 `gateway/infra/deps.py` 一致）

| 变量 | 含义 |
|---|---|
| `TRUST_GATEWAY_X_USER_ID` | 默认 `true`：无 Bearer 时可信任 nginx 注入的 `X-User-ID`。直连公网且要防伪造时设为 `false`，强制只认 JWT。 |
| `INTERNAL_TASKS_SECRET` | 非空时：`POST/GET /api/internal/tasks*` 须带 `X-Internal-Secret` 与之相同。未设置时仅允许**回环**调用；跨主机必须配置。 |
| `DEV_MODE` | 未授权时的调试日志开关，不改变生产鉴权主逻辑。 |

---

## 九、WebRTC 统一远程桌面管线

### 9.1 统一入口架构

所有设备类型统一走 WebRTC，前端只传 `device_id`：

```
前端 useWebRtc.ts
  → invoke('send_webrtc_offer') via AppBridge WS
  → Gateway _relay_webrtc_offer_to_pc()（注入 TURN ice_servers）
  → CloudBridge WS → VmControl cloud_bridge.rs
  → Router::oneshot("/api/webrtc/start")
  → webrtc_unified.rs: SQLite Device Registry → DeviceKind → 分发
    ├── linux_vm   → webrtc_vm.rs  → VNC socket → H.264
    ├── android    → webrtc_scrcpy.rs → Scrcpy → H.264
    └── host_desktop → webrtc_hd.rs → Screen Capture → H.264
```

> ⚠️ **noVNC 已于 2026-03-19 全栈移除**（前端 14 个文件 + Tauri Rust 6 个文件 + 755 行 vnc_proxy.rs）

### 9.2 WS 全通道信令（方案 B）

**offer / answer / candidates 全走同一条 AppBridge WS**，保证消息有序，天然无竞态。

```
前端 invoke('send_webrtc_offer')
  → AppBridge WS → Gateway app_client.py
  → CloudBridge WS → VmControl → 创建 peer + answer
  → CloudBridge WS → Gateway → AppBridge WS push → 前端 setRemoteDescription

ICE candidates（双向同一条 WS）
```

### 9.3 Device Registry 同步

```
VmControl 连接 Gateway /internal/pc/ws
  → Gateway 推送 sync_devices（三重保障：连接后200ms全量 + DB写完后回推 + CRUD增量）
  → VmControl upsert 到本地 sqlx SQLite（vmcontrol.db）
```

### 9.4 视频编码管线

**编码器优先级**：VideoToolbox GPU（~2ms, CPU≈0%） → FFmpeg → openh264 软编码

**RustDesk 优化已落地**：
- BGRA 直接 GPU 编码（消除 ~5ms CPU 色彩转换）
- DataRateLimits 硬上限（编码器硬件级 CBR，AverageBitRate=80% + DataRateLimits=100%）
- 编码失败自动 Fallback（VT 连续 3 次失败 → 降级 openh264，不黑屏）
- 帧 drain + 动态 Sample.duration（Anti-Slowmo，消除慢放效果）
- 切应用后自动请求 keyframe（visibilitychange + focus 事件）

### 9.5 Scrcpy Broadcaster 多客户端架构

每个 `device_serial` 一个 ScrcpyBroadcaster，持有唯一 scrcpy TCP 连接，通过 `tokio::sync::broadcast` 分发到所有订阅者。

**三个关键 bug 修复**：keyframe 在 ICE 连接前 write（等 Connected 再写）、SPS/PPS 和 IDR 共用缓存（拆分）、broadcaster 双重锁死锁（独立 Arc<Mutex>）。

### 9.6 操控台组件体系

```
Console/
├── DeviceConsole.tsx     — ★ 主组件（fixed 浮层 z-[9999]）
├── ConsoleToolbar.tsx    — 固定底部工具栏
├── VirtualKeyboard.tsx   — ★ 虚拟物理键盘（完整 QWERTY + Fn + 修饰键 toggle）
├── PipMinimap.tsx        — PiP 缩略图（缩放时角落全景）
├── RemoteCursor.tsx      — 远程光标（无 cursor shape 时显示默认白色箭头 SVG）
├── CursorMagnifier.tsx   — 放大镜（precision mode，ref 存储消除闪烁）
└── SoftwareCursor.tsx    — 软件光标

hooks/
├── useViewTransform.ts   — 缩放/平移（pinch + 滚轮 + 拖动）
├── useWebRtc.ts          — WebRTC PeerConnection + DataChannel
└── useRemoteInput.ts     — 鼠标/键盘/触摸 → DataChannel 序列化
```

**Fixed 操控模式**：鼠标/键盘发送到远程，indigo 发光边框。**Adjust 缩放模式**：滚轮缩放+拖动平移。ESC 切换。

**VirtualKeyboard**：修饰键 toggle 模式（点按高亮，按完其他键自动释放）。Apple 风格气泡反馈。

**⚠️ 实现注意**：
1. `containerRef` 需 ref callback + `useState(false)` 强制二次 render，否则 hook 拿不到 DOM
2. 不要在 ref callback 里用 forceUpdate（无限循环）
3. `onPanStart` 依赖只保留 `[viewMode]`，transform 用 `setTransform(prev => ...)` 读最新值

### 9.7 关键文件速查

| 需求 | 文件 |
|---|---|
| 统一 WebRTC 路由 | `vmcontrol/src/api/routes/webrtc_unified.rs` |
| Device Registry | `vmcontrol/src/db/device_repo.rs` |
| HD 捕获+编码 | `vmcontrol/src/api/routes/webrtc_hd.rs` |
| VM VNC 编码 | `vmcontrol/src/api/routes/webrtc_vm.rs` |
| Android scrcpy | `vmcontrol/src/api/routes/webrtc_scrcpy.rs` |
| VT 硬编码 | `vmcontrol/src/webrtc/vt_encoder.rs` |
| Peer 管理 | `vmcontrol/src/webrtc/peer.rs` |
| 键盘注入 | `vmcontrol/src/input/handler.rs`（CGEvent） |
| 剪贴板 | `vmcontrol/src/input/clipboard.rs`（pbcopy/pbpaste） |
| 远程光标 | `vmcontrol/src/webrtc/cursor.rs` |

---

## 十、实时 WS Push 与配置同步

### 10.1 架构

- **前端 SSE 已完全删除**：`GET /api/user/chat/stream` 和 `GET /api/user/logs/stream` 已移除
- **所有前端实时事件走 AppBridge WS**：`push_to_user()` → Rust `gateway_push` Tauri event
- **Worker SSE（`gateway/sse/broadcaster.py`）保留**：Gateway→Worker 进程间通信，不是前端通道
- `gateway/sse_state.py` → **`gateway/push_state.py`**（已重命名全部 import）

### 10.2 WS Push 事件

| event | data | 说明 |
|---|---|---|
| `chat_message` | type, agent_id, content | 聊天消息推送 |
| `logs_updated` | event, agent_id, log_id | 日志通知（前端 GET 拉取） |
| `config_updated` | scope (settings/default_model/agent_model) | 配置变更同步 |

### 10.3 多端配置同步

```
客户端 A 改 audio_model
  → Gateway 写 DB + push_to_user("config_updated", {scope:"settings"})
  → 客户端 B PushManager 收到 → SyncService.debouncedReloadConfig()（500ms 去抖）
  → modelService.loadConfig() → Zustand store 更新 → UI 自动刷新
```

Gateway 3 个触发点：`update_settings`、`set_default_model`、`set_agent_model`。

### 10.4 WS 稳定性修复

1. **Ping/Pong 格式修正**：Rust 改为发 `{"type":"ping"}`（非协议层 Ping 帧），Gateway 正确重置 90s 超时
2. **协议层 WebSocket Ping**：Tauri **`app_bridge`** 对 **`Message::Ping`** 回复 **`Message::Pong`**（与 Uvicorn `ws_ping_interval` / 代理保活对齐）；读循环 **`select!` 偏置**先处理入站，避免心跳饿死读
3. **推送线程静默异常**：`create_task()` 在非 async 上下文抛 RuntimeError 被静默吃掉 → 恢复 `loop.create_task`，升级为 WARNING
4. **USER_MESSAGE 去重**：前端对 `USER_MESSAGE` 调用 `onAgentReply`；`messageRepo.findTempByContent()` 按文本去重，防乐观更新与推回重复
5. **Gateway `subscribe` 崩溃 → 客户端 RST**：若见 **`WebSocket protocol error: Connection reset without closing handshake`**，先查 Gateway 日志 **`[AppWS] Message loop crashed`** 与 Python traceback；已修复一类根因：**`gateway/entity/store.py` `exists_before` / `list_stream` 游标** 对 `sqlite3.Row`→`dict` 的 **`rowid` 键不稳定**（含列名冲突可能）→ **`KeyError: 'rowid'`**。修复：别名 **`_cf` / `_rid`**。
6. **Rust 侧可观测性**：`novaic-app/src-tauri/src/core/app_bridge.rs` 记录 **`conn_seq`**、连接结束原因；`commands/gateway.rs` 中 **`gateway_ws_request`** 拒绝时打 **`target: app_bridge_diag`**（`connected` / `sink_installed`），与前端 **`WS not connected (action=entity)`** 对照时间戳
7. **Entangled React**：`Entangled/packages/react` — `syncListener` / `client` 重连、卸载 **`stopSyncListener`**、generation 与 Strict Mode 双挂载

### 10.5 App→Gateway WS Request/Response

操作型调用（chat_send、interrupt、webrtc_stop）全走 WS，不回退 HTTP：

```json
→ {"type":"request","request_id":"uuid","action":"chat_send","data":{...}}
← {"type":"response","request_id":"uuid","data":{...},"error":null}
```

Gateway `_dispatch_request` 直接调进程内函数，零 HTTP 中转。

### 10.6 App WebSocket（`/api/app/ws`）认证与设备分组

- **身份**：连接必须带 **`Authorization: Bearer <access_token>`**，`user_id` **仅**来自 JWT 的 `sub`。**不再**允许仅凭 `X-User-ID` 连接（防冒充）。若同时带 `X-User-ID`，必须与 `sub` 一致，否则 **4003** 关闭。
- **设备分组**：`GET /api/devices/grouped` 仍可用（浏览器/其他客户端）。**桌面 Tauri 客户端**：**`devices.grouped` 仅通过 Entangled `entangledMethod` / AppBridge WS**，**不设 HTTP 回退**（与「数据面统一走 AppBridge」一致；断连时 UI 应等待重连而非静默换通道）。
- **实现**：`compute_grouped_devices` 使用 `DeviceRegistry.get_user_devices`；与 `grouped_action` 共用逻辑。

### 10.7 Entangled 单 Store 架构与前端引擎统一（2026-03 重构）

**后端改动**：NovAIC `EntityStore` 直接作为 Entangled 的 store，消除了旧的双层结构（bridge closures + 第二个 EntangledStore 空壳）。新增 `EntityStoreProtocol(ABC)` 规范接口。

**`gateway/entity/store.py` 变更**：`EntityDef` 新增字段：
```python
sync_type: property  # 自动推导：STREAM → "stream"，其他 → "list"
sync_limit: int      # stream head_n 窗口（bridge init 时自动设为 50）
op_log_size: int     # 每个 (entity, params) 的 op-log 最大条数（默认 1000）
relations: List      # EntityRelation 级联关系（bridge 从 parent tuples 自动构建）
```
`EntityStore` 新增 `get_all_defs()` 方法（Entangled notifier `set_store()` 需要）。

**`gateway/entity/entangled_bridge.py` 新职责（仅 3 件事）**：
1. `SyncRegistry` 初始化 + 版本从 DB hydrate + 每次 mutation 持久化
2. `_build_relations()`：扫描所有 `EntityDef.parent` 元组 → 自动生成 `EntityRelation` 写入 `parent_def.relations`
3. `set_entangled_store(gw_store)`：将 NovAIC store 注册给 Entangled notifier

**`gateway/api/app_client.py` 接入**：三个 handler 统一使用 `get_entity_store()`；用户 WebSocket 接受后 **首包 schema push** 的 `data` 为 **`{ entities, hash, syncContractVersion }`**（`syncContractVersion` 来自 `gateway.entity.sync_contract`，与 REST `/api/entangled/schema`、Entangled `ws_handler` 对齐，供桌面 `app_bridge` 与 TS 合约版本一致）。
```python
store = get_entity_store()
await handle_subscribe(client, store, ...)    # subscribe（含 cascade）
await handle_load_more(client, store, ...)   # load_more（含 cursor hasMore）
handle_unsubscribe(client_id, msg, store=store)  # unsubscribe
```

**subscription_cascade 服务端化**：客户端仅发 `subscribe A`，`handle_subscribe` 在服务端读 `store.get_def(A).subscription_cascade` 自动展开，Push 所有 cascade 实体的初始 sync。非 React 宿主（Rust / 其他）无需感知级联逻辑。

**前端极其精简的 React Glue**：
- 废弃并彻底删除了 850 行的 `@entangled/react` 历史死代码包。
- 移除前端的复杂请求编排。Rust 层新增 `entangled_method_optimistic` 闭环包揽生成 ID、写入 Pending 缓存、推送事件刷新 UI、多轮 Server 重试及失败拦截。前端组件只剩下简简单单的 `invoke()`。
- `hooks.tsx` 大幅减负并重构成精简的工厂函数（`createListStore` 等）主要为了满足 DRY，其核心已不再是厚重的同步状态机层。

**最后一公里：能力协商与去除中间层**：
- **协议基类**：`entangled/server/store.py` 引入 `EntityStoreProtocol(ABC)` 提取出 `list, get, create, update, delete` 抽象方法，NovAIC Store 直接继承，由 base fallback 到 `_sql_...` 的内部调用，接口边界变得极其清晰。
- **鸭子类型**：`ws_handler` 能够 duck-typing 识别 `store` 的 `exists_before()` / `list_stream()`，免除了手动注入 wrapper。
- **Schema 热推送**：WS 连接打通时服务端计算实体 `capabilities`（`listStream`, `upsert`等）下发，取代之前的硬编码；
- **清理与合并**：消除了 NovAIC 重复的 `_dispatch_entity_crud` (~144行)；抽离公共前端工具 `toSnakeParams` 到 `utils.ts`；省略 `gateway.entity.notifier` 代理层，直接调用 `entangled.server.notifier` 减阻。

---


## 十一、前端架构与关键文件

### 11.1 三层架构

前端采用 **Render / Business / DB 三层架构**（详见 `FRONTEND_ARCHITECTURE.md`）。

**启动流程**：
1. **登录**：`auth.ts` → `pushToken()` → `invoke(update_cloud_token)` → `agentService.initialize()`
2. **恢复 Agent**：`prefsRepo.getSelectedAgent()` 或 localStorage
3. **选择 Agent**：store 写入 + prefs → `switchAgent(agentId)` 并行 load 模型（消息/日志均已改为 Entangled stream 自动回溯订阅）
4. **登出**：`getSyncService().disconnect()` + `resetServices()` 清空单例

**DB 层**（Entangled 为单一事实来源）：
- **所有 IndexedDB (messageRepo/logRepo) 已移除**，改用 Entangled Stream Store（由 Rust SQLite 缓存 + Server Push 同步）。
- 数据流向：Subscribe → Server sync → Rust SQLite cache → `entities_changed` 事件 → React UI 重新渲染。
- **`entities_changed` 载荷**：Rust（`Entangled/packages/client-rust/src/push.rs`）在 `EntityChanged` 中携带 **`params`**（与订阅 key 一致），供 `@entangled/react` 的 `syncListener` 按带参 `queryKey` 失效，避免只按实体名全量 invalidate。
- **订阅 refcount**：`subscriptionSchema.acquireSubscribe` 在首次 `subscribe` 成功后再记 1；AppBridge 重连时用 **wire-only** `subscribe`（`entangledBootstrap`）避免 eager 双计数。
- **聊天主面板**：`ChatPanel` 唯一调用 `useMessages` / `useLogs`，`MessageList`、`ExecutionLog`、`MainAgentLogPreview`、`SubagentList` 等通过 **props** 注入，避免同一 agent **重复订阅** stream。

**Business 层**：
- `messagesStore` / `logsStore` (实体数据)，`syncService`（WS + delta sync）、`agentService`（CRUD + VM setup）、`modelService`（模型配置）
- Zustand 全局状态（`store.ts`）

**AgentToolsTab SWR**：打开 Tab → IndexedDB 瞬间读缓存渲染 → 后台 `Promise.allSettled(6 个配置请求)` → 写 IDB → subscription 无感更新。

### 11.2 关键设计决策

- **`getCachedUser()` 不可放进 useEffect 依赖**：每次返回新对象，必须提取 `userId = getCachedUser()?.user_id`
- **currentAgentId 隔离**：Chats 用 Zustand，Agents 用 local state，Skills 用 local state
- **模型选择**：在 Agent Tools 中配置，`modelService.setModel(agentId, compositeId)`
- **MessageList**：使用 `flex-1 min-h-0`（非 `h-full`），已移除 opacity-0 模式

### 11.3 前端文件速查

| 需求 | 文件 |
|---|---|
| 改远程桌面 | `useWebRtc.ts`、`WebRtcScrcpyView.tsx` |
| 改操控台 | `DeviceConsole.tsx`、`ConsoleToolbar.tsx`、`useRemoteInput.ts` |
| 改浮窗 | `DeviceFloatingPanel.tsx` → FLOATING_PANEL_LAYOUT |
| 改模型选择 | `SettingsModal.tsx` → AgentToolsTab |
| 改消息发送 | `ChatInput.tsx`、Entangled `messagesStore` / `useMessages` |
| 改执行日志 UI | `ExecutionLog.tsx`、`LogCapsule.tsx`、`ChatPanel.tsx`（`MainAgentLogPreview` 叠层布局；与 `MessageList` 共享 `useLogs`） |
| Gateway HTTP 辅助与类型 | `src/services/api.ts`（数据写操作优先 `entangledMethod`，勿在此新增 Agent CRUD） |
| 改主布局 | `LayoutContainer.tsx`、`PrimaryNav.tsx`、`App.tsx` |
| 改 Gateway 配置 | `novaic-gateway/gateway/api/internal/config.py` |
| 改 VM 准备 | `gateway/api/vm.py`、`vmcontrol/src/api/routes/vm_prep.rs` |
| 改技能（UI/同步） | `Settings/SkillsPage.tsx`、`hooks/useSkills.ts`、`application/skillsService.ts`、`data/entities/skills.ts` |
| 改技能进 LLM 上下文 | `novaic-agent-runtime/task_queue/utils/system_prompt.py`（`_build_skills_section`）；匹配逻辑 `novaic-gateway/gateway/db/repositories/skill.py` |

### 11.4 Entangled Headless 架构（Path C，2026-03-30 完成）

**核心理念：React 是纯展示 + 意图分发层。Rust Entangled 引擎自主运转订阅/缓存/同步/重连。**

**三个动词**：
- **读**：`useList/useForm/useStream` → `staleTime=Infinity`，仅由 `entities_changed` 事件驱动刷新
- **写**：`dispatch(intent)` → `entangled_method_optimistic`（CRUD）或 `entangled_method`（自定义 action）
- **路由**：`navChanged(route, params)` → Rust `nav_changed` 命令 → 路由表 → 自主 subscribe/unsubscribe

**路由表（`src-tauri/src/commands/nav.rs`）**：

| 路由 | 订阅实体 |
|------|----------|
| `home` | agents, models, devices |
| `conversation` | agents, models, devices, messages(agentId), execution-logs(agentId), agent-tools(agentId), **agent-binding(agentId)** |
| `settings` | agents, models, devices, api-keys, skills, **agent-binding(agentId), agent-tools(agentId)**（有agentId时） |
| `vm-context` | vm-users(deviceId)（组件级调用） |

**App.tsx 主槽导航（Sync Contract 1.4，当前）**：
- **单一 `useEffect`**：`deriveDesiredMainNav({ isInitialized, settingsOpen, currentAgentId })` → `navChanged(route, params)`，依赖 `[isInitialized, settingsOpen, currentAgentId]`（`nav.ts` 内 `enqueueMainNav` 串行化与 Rust 主槽一致）。
- **启动阶段**：`agentService.initialize()` → `bootstrapEntangledEntities()` 内仍 **`navChanged('home', {})`**（在 `isInitialized` 置 true 之前），用于尽早下发 Rust 订阅；与上述 effect **共用主槽队列**，避免并发 `nav_changed` 互相踩（见 `entangledBootstrap.ts` 注释）。
- **历史**：曾用三个独立 effect 驱动 home / conversation / settings；已收敛为推导函数 + 单 effect，减少竞态。

**关键文件**：
- `src-tauri/src/commands/nav.rs` — 路由表 + `nav_changed` Tauri 命令
- `src/data/entangled/dispatch.ts` — 统一意图总线（取代所有 useMutation）
- `src/data/entangled/nav.ts` — TS 包装，含 `navChanged()` + `useNavChanged()`
- `src/data/entangled/hooks.tsx` — 精简工厂函数，零订阅逻辑
- `src/data/writePipeline.ts` — 已精简至 52 行（仅 `shallowDiff` 工具函数）
- `src/components/hooks/useVmUsers.ts` — 组件级 navChanged('vm-context') 动态订阅

### 11.5 Slot-based NavState v2（2026-03-30）

**问题**：Path C 的 nav_changed 使用全局 `PREV_NAV_SUBS` 静态变量，存在三个缺陷：
1. 多窗口互相覆盖（同一 static 被两个 AppHandle 共享）
2. 无法叠加订阅（conversation 路由覆盖 vm-context 的 vm-users）
3. 多实例组件 refcount 混乱（多个 VmPanel 共用全局状态）

**方案**：`NavState` 是 Tauri `manage()` 注入的 per-AppHandle 状态，内部结构 `HashMap<slot_name, Vec<SubSpec>>`。每个 slot 独立管理自己的订阅集，互不干扰。

**API**：
```typescript
// 默认 slot="main"（兼容现有调用）
navChanged('conversation', { agentId })

// 组件级 slot（useNavChanged 自动 release on unmount）
useNavChanged('vm-context', { deviceId }, [deviceId], { slot: `vm-${deviceId}` })

// 手动释放
navReleaseSlot(`vm-${deviceId}`)
```

**关键文件**：
- `src-tauri/src/commands/nav.rs` — `NavState` managed state + `nav_release_slot` command
- `src/data/entangled/nav.ts` — slot 参数支持 + `navReleaseSlot()` + `useNavChanged` 自动清理 hook

### 11.6 Schema Codegen（2026-03-30）

**问题**：Python `EntityDef`（defs.py）和 TS 接口手动同步，字段改名不感知 → 运行时 crash。

**方案**：`scripts/generate_entity_types.py` 读取 `ALL_ENTITIES`，自动生成 `novaic-app/src/data/entities/__generated__.ts`（20 个实体接口 + checksum）。

```bash
python scripts/generate_entity_types.py          # 生成
python scripts/generate_entity_types.py --check   # CI 校验 drift
```

### 11.7 HTTP→Entangled 通道统一（2026-03-30）

| 操作 | Before | After |
|------|--------|-------|
| addApiKey / updateApiKey / deleteApiKey | `invoke('gateway_post/patch/delete')` | `entangledMethod('api-keys', 'create/update/delete')` |
| updateSettings | `invoke('gateway_patch', '/api/config/settings')` | `entangledMethod('user-preferences', 'upsert')` |
| getBootstrapFiles / saveBootstrapFiles | `invoke('gateway_get/post', '/api/agents/:id/bootstrap-files')` | `entangledMethod('agent-tools', 'get_bootstrap/save_bootstrap')` |
| skills match / fork / getToolCategories | `api.matchSkillsForTask` / `api.forkSkill` / `api.getToolCategories` | `entangledMethod('skills', 'match/fork/get_tool_categories')` |
| skills CRUD (create/update/delete) | `api.createSkill` / `api.updateSkill` / `api.deleteSkill` | `entangledMethod('skills', 'create/update/delete')` |
| modelService.loadConfig | `api.getConfig()` HTTP + `prefsRepo` IDB 三层 fallback | `cacheGetList('models') + cacheGetList('api-keys') + cacheGetItem('user-preferences')` 纯 Entangled 缓存 |
| syncService reconnect | 手动遍历 12 个 entity key `invalidateQueries` | 删除（Rust `resubscribe_all → entities_changed` 自动处理） |

**Python 新增文件**：
- `gateway/api/skill_actions.py` — match/fork/get_tool_categories action 函数
- `defs.py` SKILLS EntityDef — 注册 `match / fork / get_tool_categories` actions（lazy import）
- `defs.py` AGENT_TOOLS EntityDef — 注册 `get_bootstrap / save_bootstrap` actions

**api.ts 保留的真正 HTTP（无法迁移）**：
- 文件上传（binary multipart）
- 健康检查 / 进程管理（WS 未建立时需要）
- Android 设备枚举 / AVD 管理
- 历史日志带 subagent 过滤的复杂查询
- WebRTC 信令

### 11.8 Skills 领域文档（2026-04）

- **调查报告（五子领域）**：`docs/skills-domain-investigation-reports.md` — 存储与发现、Prompt 注入与预算、运行时匹配、市场形态、安全运维；与 **`thirdparty/openclaw`** 对照，供立项 Skill 商店 / 限额 / 导入器时引用。  
- **OpenClaw 代码地图（笔记）**：`docs/agent-approve-points/02-openclaw-architecture.md`（嵌入式 runner、插件 hooks；路径以子模块 `thirdparty/openclaw/src/` 为准）。  
- **待办**：产品级 Skill 商店仍见 **§十六**；调查报告为「现状与差距分析」，非实现交付。


---


### 12.1 后端服务组件

| 进程 | 职责 |
|---|---|
| Gateway | API、DB (chat_messages/subagents/agents)、WS Push |
| Runtime Orchestrator (RO) | Runtime CRUD、agent_runtimes 表 |
| Queue Service | Task/Saga 队列管理 |
| Watchdog | 轮询 sending 消息，创建 MessageProcess Saga |
| Task Worker | 执行 Task（LLM 调用、工具执行、context 读写） |
| Saga Worker | Saga 流程编排（步骤推进、决策、触发子 Saga） |
| Health Worker | 超时任务/Saga 回收 |
| Scheduler Worker | 定时唤醒 sleeping agent |
| Tools Server | 工具执行（shell/browser/file） |

### 12.2 消息 → Runtime 完整链路

```
用户发消息
  → Gateway: chat_messages INSERT (status=sending, read=0)
  → Watchdog: find_sending() → 创建 MessageProcess Saga
  → Saga Step 1 (claim_message): sending → sent
  → Saga Step 2 (route_message): RO get_or_create_runtime()
    → 有 active runtime? → skip
    → 无 active? → 创建 rt-xxx(active) → just_created=true
  → Saga Step 3 (decide): start_runtime
  → Saga Step 4 (trigger): RuntimeStart Saga → ReactThink
```

### 12.3 Agent Loop

```
ReactThink:
  1. context.read:     RO context + Gateway 未读消息 → 合入
  2. context.mark_read: 标记 read=1
  3. llm.call:          调 LLM Factory
  4. context.save:      保存 response
  5. decide:            有 tool_calls → ReactActions / 无 → subagent_rest

ReactActions:
  1. execute_tools:    并行执行所有 tool_calls（Tools Server）
  2. save_results:     保存 tool results
  3. check_continue:   has_new_messages + check_need_rest
  4. decide:           need_rest → RuntimeComplete / else → 下一轮 ReactThink
```

### 12.4 工具执行全链路

```
LLM tool_call (e.g. shell_exec)
  → Tools Server → VM_TOOL_MAPPING → POST /internal/agents/{agent_id}/vm/shell/command
  → Gateway (proxy_vm_tool) → 检查 mounted_tools 权限
  → CloudBridge WS → VmControl → VMUSE (Python, VM 内 port 8080)
  → ShellTools.run_command → asyncio.create_subprocess_shell
```

| 类别 | 工具数 | 路由 |
|---|---|---|
| VM (desktop/shell/file/browser) | 25 | Gateway → PC WS → VmControl → VMUSE |
| Mobile (screen/shell/app/ui) | 22 | Gateway → PC WS → VmControl → adb |
| Memory/Notebook/Chat | ~30 | 直接调 Gateway API |
| QEMU (ssh_exec/status) | 5 | Gateway → PC WS → VmControl |

### 12.5 LLM Factory 集中化

所有 LLM 调用统一走 Factory `POST /v1/chat/completions`。api_key 只在 Factory 内部解密。

```
调用方 → Gateway 查 model_id + user defaults
       → 返回 {model_id, model_name, user_id, factory_url}（不含 api_key）
       → Factory: resolve_model → 解密 → 调 LLM → 记日志 → 返回
```

用户偏好（default_model / audio_model）存 Gateway 本地 `config` 表。Model Name 通过 TTL 缓存（5min，不可达时 30s）。

### 12.6 关键数据库分布

| 数据 | DB | 表 |
|---|---|---|
| 用户消息 | Gateway | chat_messages (sending/sent, read 0/1) |
| SubAgent 状态 | Gateway | subagents (need_rest, wake_at, hrl) |
| Runtime 及 Context | RO | agent_runtimes (status, context JSON) |
| Task/Saga | Queue Service | tasks, sagas |

### 12.7 已知 Bug：消息积压重复 Runtime

SYSTEM_WAKE 风暴导致大量 sending 消息 → Watchdog 为每条创建 Saga → 前一个 Runtime completed 后后续 Saga 又创建新的。

**根治方案 — Watchdog v2 Per-Agent 轮询**：一次拿全部 sending，按 `(agent_id, subagent_id)` 分组，每组只创建 1 个 Saga。

### 12.8 文件速查

| 需求 | 文件 |
|---|---|
| Watchdog | `agent-runtime/task_queue/workers/watchdog_sync.py` |
| MessageProcess Saga | `agent-runtime/task_queue/sagas/message_process.py` |
| ReactThink | `agent-runtime/task_queue/sagas/react_think.py` |
| ReactActions | `agent-runtime/task_queue/sagas/react_actions.py` |
| FactoryLLMClient | `agent-runtime/task_queue/factory_client.py` |
| 工具定义 | `tools-server/common/tools/definitions.py` |
| 工具路由+执行 | `tools-server/tools_server/executor.py` |
| 工具权限+挂载 | `gateway/gateway/agent_binding.py` |
| VM 代理 | `gateway/gateway/api/internal/agent.py` (proxy_vm_tool) |
| VMUSE Shell | `mcp-vmuse/src/novaic_mcp_vmuse/tools/shell.py` |

---

## 十三、文件服务与语音录制

### 13.1 文件服务统一（/api/files/）

历史双系统（`/api/images/` + `/api/files/`）已统一到 `/api/files/`。

```
截图 → ImageStorage.save_image() → POST File Service /api/files/from-base64
聊天附件 → uploadChatFile() → Gateway /api/files/upload → files 表
访问 → GET /api/files/{file_id} → Gateway 验证 user_id → 代理 File Service
```

### 13.2 语音录制（Rust cpal）

Tauri WKWebView 中 `navigator.mediaDevices` 为 undefined，`getUserMedia` 不可用。

```
前端 invoke('start_audio_recording') → Rust cpal 打开麦克风 → PCM 缓存
前端 invoke('stop_audio_recording') → hound 写 WAV → base64 返回 → 上传
```

注意：`cpal::Stream` 用 `unsafe impl Send/Sync` 绕过。WAV ~11MB/分钟，未来可压缩为 Opus。

---

## 十四、环境变量与配置

### 14.1 本地 App 数据目录

macOS：`~/Library/Application Support/com.novaic.app`  
内含：`gateway_url.txt`（默认 `https://api.gradievo.com`）、`api_key.txt`、`app.pid`

**VmControl 路径**：
- QMP Socket：`/tmp/novaic/novaic-qmp-{agent_id}.sock`
- VNC Socket：`/tmp/novaic/novaic-vnc-{id}.sock`

### 14.2 前端配置（config/index.ts）

| 配置 | 关键项 |
|---|---|
| API_CONFIG | GATEWAY_URL, HTTP_TIMEOUT |
| LAYOUT_CONFIG | LAYOUT_THRESHOLD(1024), DRAWER_WIDTH(304) |
| POLL_CONFIG | GATEWAY_HEALTH_INTERVAL |

### 14.3 Gateway 进程环境（鉴权 / 内部 API）

与 **`gateway/infra/deps.py`** 对齐，生产环境在 `jwt_secret.env` 或 systemd `Environment=` 中配置：

- `TRUST_GATEWAY_X_USER_ID`、`INTERNAL_TASKS_SECRET`（见 **§8.5**）。
- 内部任务 API 跨 Docker/局域网调用时：**必须**设置 `INTERNAL_TASKS_SECRET`，客户端带 `X-Internal-Secret`。

**本地自测（无需 pytest）**：

```bash
cd novaic-gateway && PYTHONPATH=. python -m unittest tests.test_deps_internal_tasks -v
```

---

## 十五、常见问题排障大全

| 问题 | 原因 | 解决 |
|---|---|---|
| **AppBridge 秒断 / `WS not connected (action=entity)`** | 多为 Gateway **`/api/app/ws` handler 异常退出**（客户端见 TCP RST）；曾见 **`exists_before` → `KeyError: 'rowid'`** | 已修复：`store.py` 游标查询 **`AS _cf, AS _rid`**；服务器 **`grep Message loop crashed gateway-*.log`**，对齐 **`[AppWS] accepted` / `handler exiting`** |
| macOS SIGTRAP 崩溃 | enigo.key() 必须 main queue | 已修复：全换 CGEvent |
| **Entangled WS 断连 (Message too long)** | head_n 未下发 LIMIT 导致 Gateway 查全量几十MB数据撑爆 WS 帧 | 已修复：在 Gateway 桥接及 Entangled server 透传 `limit` |
| **UI 全面冻结 / Device tab 卡死** | `getCachedUser()` 返新对象 → useEffect 无限循环 | 提取 userId string 做依赖 |
| **宽屏消息不可见** | opacity-0 timer + h-full 解析为 0 | 已修复：flex-1 min-h-0 |
| Gateway 无响应 | WAL/SHM 损坏 | rm -f *.db-wal *.db-shm + 重启 |
| Gateway 500 | JWT_SECRET 未设置 | 确认 jwt_secret.env |
| Gateway 写锁悬挂 | 写操作缺 transaction() | 已修复：with db.transaction("global") |
| Port 1420 占用 | 上次 dev 未退出 | `kill $(lsof -ti:1420)` |
| App 一直 Connecting | pushToken 在 initialize 之后 | 已修复：await pushToken() 先 |
| Rust panic Cannot block | async 里用 blocking_read() | 改为 read().await.clone() |
| iOS 黑屏 | custom-protocol + WKWebView | 构建用 --features mobile |
| `tauri ios run` 失败 | exportOptionsPlist 相对路径 | 用 build + devicectl install |
| iOS arch 参数错 | FORCE_COLOR 被解析为 arch | patch-ios-xcode.sh |
| iOS aws-lc-sys 编译失败 | Xcode 26 beta SDKROOT 不对 | 降级正式版 Xcode |
| LLM 429 / 超时 | API 限流或过载 | 查 task-worker log，建议指数退避 |
| 截图截错屏 | runtime_context 缺 display | 已修复：注入 `:11` 等 |
| scrcpy 无响应 | 控制 TCP 断了不 break | 已修复：write 失败后 break |
| WebRTC 多端互踢 | stop_peers 强杀 + UDP 泄漏 | 已修复：移除强杀 + UDPMux |
| coturn 新连接失败 | 僵尸 session 积累 | 重启 coturn |
| Relay handshake timeout | 服务端用 open_bi | 已修复：改 accept_bi |
| **agent-binding 保存成功 UI 显示成功但重开后消失** | ① 前端用 `update` 而非 `upsert`（首次无记录→0行）；② `nav.rs` 缺 `agent-binding` 订阅→Rust缓存为空→读不到数据 | **已修复**：`agentBinding.ts` `optimistic:false` 走 upsert；nav.rs conversation/settings 加 agent-binding 订阅；App.tsx settings 传 agentId |
| **绑定保存后界面仍显示旧设备 / 无绑定首屏报错** | `entangled_method` 不发 `entities_changed`；RQ `staleTime=Infinity`；无行时 `entity_get` 抛错 | **已修复**：`hooks.tsx` `createFormStore` upsert `onSuccess` → `setQueryData`+invalidate；`allowMissing`；`agentBinding.ts` 泛型含 null |
| **选「无设备」保存后仍绑定** | 保存分支用 `currentBinding`，选无设备时被 `handleDeviceChange` 清空 | **已修复**：`AgentToolsPanel` 用 `bindingData?.device_id` 触发 `clearAgentBinding` |
| **聊天区执行日志预览条偏右、与消息不齐** | Framer Motion `transform` 覆盖 `translate-x` 居中 | **已修复**：`ChatPanel.tsx` flex 居中 + `px-4`，去横向 mask |
| **聊天窗口 device 浮窗不显示** | `useAgentBinding` 读 `agent.binding`（agents实体无此字段），Rust缓存为空返回null | **已修复**：`useAgentBinding.ts` 改用 `agentBindingStore.useForm()` 直接读 Entangled 缓存 |
| **Rust `sync_contract_version` 长期为 0 / v2 缺 idField 无 ERROR 日志** | 连接早期未收到带 `syncContractVersion` 的 schema，或 REST 解析失败未 `invoke` | 确认 **AppWS schema push** 已含 `syncContractVersion`（`app_client.py`）；查 TS `[Entangled]` 与网关返回体是否为 `{ entities, syncContractVersion }` |
| **选 Agent / 新建 Agent 后 needsSetup 或选中态异常** | `useCallback(..., [])` 闭包读到旧 `agents` | **已修复**：`handleSelectAgent` / `handleAgentCreated` 依赖 **`agents`** |
| **登出再登录仍弹出设置浮窗** | `settingsOpen` 未随 session 清空 | **已修复**：`handleLogout` **`settingsOpen: false`** |
| ⚠️ `PRAGMA wal_checkpoint(TRUNCATE)` | 截断未提交事务 | **禁止运行时执行** |

### LLM 调用失败排查

1. 查日志：`grep -E "429|think.*failed" /opt/novaic/data/logs/task-worker-*.log`
2. 取 context：从 `tq_sagas.step_results -> read_context.context`（**不能**用 runtime.context）
3. 重放：`POST /api/queue/tasks/publish` topic=llm.call
4. 脚本：`novaic-agent-runtime/scripts/trace_llm_call.py`

---

## 十六、技术债与待办

**近期已落地（审计收尾，2026-03）**：
- **Entangled 同步引擎重构**：
  - Gateway `store.py` 支持游标 `SELECT EXISTS()` 替换 N+1 翻页 hack；使用 `_cf`/`_rid` 别名避免 `rowid` 键缺失导致 Subscribe 崩溃。
  - `ws_handler` 增加 1000 上限背压队列、30s Server 心跳；`load_more` 纳入独立协议；`cache.rs` 增加 `last_accessed` TTL 垃圾回收。
  - React hook 解除 `JSON.stringify` 带来的依赖开销。
  - **EntityDef 与 EntityStore 大一统（2026-03-29 完成）**：NovAIC `gateway/entity/store.py` 完全继承 `entangled/server/store.py` (新增 ABC Protocol)，移除了大量冗余端点实现。彻底解决了双边 Schema 和 CRUD 实现不一致的问题，将通知流入口收敛到了 BaseStore。
  - `subscription_cascade` 服务端化：`handle_subscribe` 现在在服务端自动展开级联逻辑。
  - `current_version` 持久化：表 `entangled_sync_versions`，`entangled_bridge` 每次 mutation 时 upsert。
  - **前端客户端极致瘦身与 Rust 编排化（2026-03-29 完成）**：彻底删除死代码 `@entangled/react` SDK。废除了前端复杂的编排逻辑，新增 Rust 级命令 `entangled_method_optimistic` 闭环处理 Request ID 生成、并发控制和本地回滚。React `hooks.tsx` 浓缩为 ~250 行精简工厂函数。
  - **Headless 架构 Path C（2026-03-30 完成）**：`nav_changed` Rust 命令完全接管订阅生命周期。路由表覆盖所有实体（home/conversation/settings/vm-context）。`dispatch()` 统一意图总线。`writePipeline.ts` 550行→52行。React 零 subscribe/unsubscribe 调用。详见 §11.4。
  - **Slot-based NavState v2（2026-03-30 完成）**：nav.rs 重构为 per-AppHandle managed state，支持多窗口/多实例 slot-based 隔离。详见 §11.5。
  - **Schema Codegen（2026-03-30 完成）**：`scripts/generate_entity_types.py` 从 Python EntityDef 自动生成 20 个 TS 接口，`--check` CI 模式检测 drift。详见 §11.6。
  - **HTTP→Entangled 通道统一（2026-03-30 完成）**：Gateway 注册 16 个 new action（`get_config`, `test_api_key`, `available_images` 等），四个业务 Service 层彻底迁移至 `entangledMethod`。`api.ts` 净减近 1000 行，清除了全部 57 个 `gateway_*` HTTP 函数，全库已无运行时 HTTP 调用，彻底拥抱 Entangled。详见 §11.7。
- API 稳定与性能：Gateway `list`/`list_all` WS 上限；`agent-binding` notify 使用 `agent_id`。
- [x] **Entangled: invalidate 自愈已移入 Rust**：`app_bridge.rs` 检测到 `invalidated` action 时自动发送 `subscribe(version=null)`，不再依赖 React hook。`cache.rs` 的 invalidate op 同时清空 stale items。
- [x] **Schema Codegen 完成**：Python→TS 实体自动生成，CI 可集成 `--check` 模式
- [x] **HTTP→Entangled 通道迁移完成**：核心 Service 均改用 Entangled actions，api.ts 纯类型化（减负近千行代码）
- [x] **syncService 重连冗余 invalidate 已删除**：Rust `resubscribe_all` 自动处理
- [x] **AppWS schema push 与 Sync Contract 对齐**：`app_client.py` 首包带 `syncContractVersion`；网关 unittest 在无 Entangled 兄弟目录时 skip parity
- [x] **modelService IndexedDB 依赖已移除**：不再读写 prefsRepo selectedModel/AudioModel
- [x] **Skills 领域分调查报告**：`docs/skills-domain-investigation-reports.md`（对照 OpenClaw；落地商店/限额/导入前读）
- [ ] **iOS 键盘输入框适配**：`--keyboard-height` 注入已实现，需真机验证
- [ ] **服务端数据自动清理**：runtime 完成时自动清空 context；queue 定期清理；logrotate
- [ ] **Watchdog v2：Per-Agent 轮询**：按 Agent 分组批量处理，防重复 Runtime
- [ ] WebRTC 多客户端操控冲突处理（当前多端不互斥）
- [ ] Gateway DB 访问改为异步（同步 SQLite 在 async FastAPI 中有阻塞风险）
- [ ] **Skill 商店 / ClawHub 集成**：浏览/搜索/安装 skill
- [ ] **原生视频渲染**：iOS VideoToolbox+Metal / Android MediaCodec+GL / macOS Metal / Web WebCodecs
- [ ] WS 连接断开时前端 toast 提示
- [ ] `prefsRepo` IndexedDB 彻底移除：selectedAgent 改为 Entangled entity，layout 持久化评估
- [ ] **Model 实体规范化重构**（详见下方 §17）

---

## 十七、Model 实体规范化重构方案

### 17.1 现状问题

当前 `candidate_models` 表（EntityDef name=`"models"`）三职合一：

| 职责 | 字段 | 问题 |
|------|------|------|
| 模型元数据 | `model_id`, `name`, `provider` | 同一个 gpt-4o 绑两个 key 就存两行，数据重复 |
| API Key 关联 | `api_key_id` | 用扁平外键代替关系，无法表达 1:N |
| 用户启用状态 | `available=0/1` | 启用状态混在模型记录里，难以独立管理 |

`refresh_models` action 每次需要全量 diff + 手动批量 upsert + 额外 `notify_entity_change`，逻辑复杂。

### 17.2 目标架构（三实体分离）

```
models (Form Entity, 全局模型注册表)
  model_id  PK    "gpt-4o", "claude-3-5-sonnet" …
  name            展示名
  provider        openai / anthropic / google / azure / openai_compatible
  context_window  可选，上下文长度
  is_custom       0/1

api-key-models (List Entity, child of api-keys)
  id        PK
  api_key_id  FK → api_keys.id  ON DELETE CASCADE
  model_id    → models.model_id
  UNIQUE(api_key_id, model_id)

available-models (List Entity, user-scoped)
  id        PK
  user_id   FK
  model_id  → models.model_id
  api_key_id  决定使用哪个 key 来调用该 model
  UNIQUE(user_id, model_id)
```

### 17.3 变更影响

| 层 | 变更内容 |
|------|------|
| Gateway `defs.py` | 新增 `MODELS`（form）、`API_KEY_MODELS`（list）、`AVAILABLE_MODELS`（list）实体；删除旧 `CANDIDATE_MODELS` |
| Gateway `defs.py` | `refresh_models` action 只需 upsert `api-key-models`，models 表单独维护 |
| Gateway DB | migration：数据从 `candidate_models` 拆分填入三张新表 |
| 前端 `data/entities/__generated__.ts` | 重新 codegen |
| 前端 `SettingsModal.tsx` | `modelsStore.useList()` 改为读 `apiKeyModelsStore` + `availableModelsStore` |
| 前端 `useAppStore` | `availableModels` 读 `availableModelsStore` |
| 前端 `modelConfigService.ts` | `toggleModel` → 操作 `available-models` entity；`addCustomModel` → 同时写 `models` + `api-key-models` |

### 17.4 预期收益

- `refresh_models` 极简：拉模型列表 → upsert `api-key-models`，Entangled 自动通知，零手动 notify
- 删 api_key 时 `api-key-models` 级联清理，available-models 也自动失效
- 模型元数据去重：gpt-4o 无论挂几个 key，`models` 表只有一行
- `available-models` 可扩展：加优先级、别名、per-model system prompt 等字段

### 17.5 工作量估算

约 1.5 天：Gateway defs + DB migration（0.5d）+ 前端 UI + hooks（0.5d）+ codegen + 测试（0.5d）

> **当前状态**：`candidate_models` 扁平实现维持可用。待 agent-binding 和 device 功能稳定后再启动本重构。
