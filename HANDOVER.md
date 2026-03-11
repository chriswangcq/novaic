# NovAIC 项目交接文档

> 最后更新：2026-03-07（切回自定义 JWT 认证，踩坑记录补充）

---

## 一、项目整体架构

```
用户 macOS 桌面
└── NovAIC.app (Tauri)
    ├── 前端 React/Vite          ← novaic-app/src/
    └── Rust 后端 (VmControl)    ← novaic-app/src-tauri/vmcontrol/
        ├── 管理 QEMU Linux VM (QMP socket)
        ├── 管理 Android 模拟器 (scrcpy 代理)
        └── CloudBridge WebSocket ──► 云端 Gateway

云端服务器 api.gradievo.com
└── Nginx (HTTPS/443 → 127.0.0.1:19999)
    ├── auth_request → /internal/auth/validate  ← HS256 JWT 验证，注入 X-User-ID
    └── Gateway (Python/FastAPI, port 19999)
        ├── SSE: /api/chat/stream, /api/logs/stream
        ├── REST: /api/**, /internal/**
        ├── CloudBridge WebSocket: /internal/pc/ws
        └── SQLite: /opt/novaic/data/gateway.db
```

---

## 二、代码仓库说明

| 仓库目录 | GitHub | 用途 |
|---|---|---|
| `novaic-app` | chriswangcq/novaic-app | Tauri 桌面应用（主仓库） |
| `novaic-gateway` | chriswangcq/novaic-gateway | 云端 Gateway（API + DB） |
| 其余子目录 | 各自独立 repo | agent runtime、工具服务等，部署在云端 |

**注意**：每个子目录都是独立 git repo，不是 monorepo，`.git` 在子目录内。

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

---

## 五、云端部署（novaic-gateway）

### 服务器信息

| 项目 | 值 |
|---|---|
| 域名 | `api.gradievo.com` |
| SSH | `ssh root@api.gradievo.com` |
| 代码路径 | `/opt/novaic/services/novaic-gateway` |
| 数据目录 | `/opt/novaic/data/` |
| 数据库 | `/opt/novaic/data/gateway.db` (SQLite) |

### 部署流程（标准）

```bash
# 1. 本地提交推送
cd novaic-gateway
git add -A && git commit -m "..." && git push

# 2. 服务器拉取
ssh root@api.gradievo.com 'cd /opt/novaic/services/novaic-gateway && git pull'

# 3. 重启 gateway（使用预置脚本）
ssh root@api.gradievo.com 'bash /tmp/restart_gw.sh'

# 4. 验证
ssh root@api.gradievo.com 'ss -tlnp | grep 19999'
```

### 重启脚本 `/opt/novaic/restart_gw.sh`

```bash
#!/bin/bash
set -e
source /opt/novaic/jwt_secret.env
export JWT_SECRET

pkill -f main_gateway.py 2>/dev/null || true
sleep 1
cd /opt/novaic/services/novaic-gateway
nohup .venv/bin/python main_gateway.py \
  --host 127.0.0.1 --port 19999 \
  --data-dir /opt/novaic/data \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --queue-service-url http://127.0.0.1:19997 \
  --tools-server-url http://127.0.0.1:19998 \
  --file-service-url http://127.0.0.1:19995 \
  --tool-result-service-url http://127.0.0.1:19994 \
  >> /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log 2>&1 &
echo $! > /tmp/gw.pid
echo "Started PID $!"
```

> ⚠️ `JWT_SECRET` 存储在 `/opt/novaic/jwt_secret.env`（不进 git）。

### Nginx 配置

- 位置：`/etc/nginx/sites-enabled/novaic`（来源：`novaic-gateway/nginx/novaic-cloud.conf`）
- HTTP(80) → HTTPS(301) 跳转
- HTTPS(443) 代理到 `127.0.0.1:19999`
- **认证方式（2026-03 起）**：Nginx `auth_request` 调用 `/internal/auth/validate`，验证 Clerk RS256 JWT，提取 `sub` 作为 `X-User-ID` 注入下游请求
- 客户端伪造的 `X-User-ID` header 在 Nginx 层被剥离（`proxy_set_header X-User-ID ""`）
- SSE 路由（`/api/chat/messages`、`/api/logs/stream` 等）关闭 proxy buffering、超时 3600s
- CloudBridge WebSocket：`/internal/pc/ws`，超时 3600s，Auth token 通过 `Authorization: Bearer` header 传入

### 查看 gateway 日志

```bash
# 实时追踪今天的日志
ssh root@api.gradievo.com 'tail -f /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log'
```

---

## 六、认证体系（2026-03 重构：自定义 JWT）

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
| `novaic-app/src-tauri/src/main.rs` | `CloudTokenState`（`Arc<RwLock<String>>`），`update_cloud_token` 命令 |
| `novaic-app/src-tauri/src/cloud_connection.rs` | WebSocket 握手时读取最新 token，设置 `Authorization: Bearer` |
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

## 七、关键架构决策与注意点

### VmControl — VM 状态检测（Scheme A）

**决策**：判断 Linux VM 是否运行，只检查 QMP socket 文件是否存在，不尝试连接。

**原因**：QMP 是单客户端协议，连接会失败且破坏现有连接。

**文件**：`novaic-app/src-tauri/vmcontrol/src/api/routes/vm.rs` — `is_vm_running()`

### SSH Key 路径约定

路径格式：`{DATA_DIR}/.ssh/id_rsa_{user_hash}`（`user_hash` 为 `user_id` 的前 16 位 sha256 hex）

- Gateway 写入：`novaic-gateway/gateway/vm/ssh.py` — `get_private_key_path(user_id)`
- VmControl 读取：`vm.rs` — 只查这一个路径（`user_id` 经 CloudBridge 从 X-User-ID 传入）

### scrcpy 控制流断线恢复

**问题**：scrcpy TCP 控制连接断开（Broken Pipe）时，VmControl 旧代码只 log 不 break，导致 WebSocket 永远不关闭无法重连。

**修复**：`scrcpy/mod.rs` 控制任务 Text 分支加 `break`，WebSocket 关闭触发前端 2s 后自动重连。

### Gateway 设备启停状态门控

`start_device` 允许状态：`READY` / `STOPPED` / `ERROR`（ERROR 状态可以重试启动）

`stop_device` 无状态门控：无论 DB 状态如何，都尝试停止（防止 DB 状态过期导致无法停机）。

**文件**：`novaic-gateway/gateway/api/devices.py`

### CloudBridge — 本地与云端通信

Tauri App 与云端 Gateway 通过 WebSocket (`/internal/pc/ws`) 保持长连接，所有 VM 操作从 Gateway 发出，经 CloudBridge 转发给本地 VmControl，再由 VmControl 操作 QEMU/ADB。

- **认证**：WebSocket 握手时在 `Authorization: Bearer <clerk_jwt>` header 里携带 token
- **token 动态刷新**：`cloud_connection.rs` 每次重连前从 `Arc<RwLock<String>>` 读取最新 token
- **Tauri HTTP 客户端必须加 `.no_proxy()`**，否则会走系统代理失败
- **所有 gateway_* Tauri 命令**（`gateway_get/post/patch/put/delete`）使用 `cloud_token.read().await.clone()` 获取 Clerk JWT，注意必须用 `.await`（不能用 `blocking_read()`，否则在 Tokio async 上下文中 panic）

---

## 八、前端关键文件

> 前端采用 **Render / Business / DB 三层架构**（详见 `novaic-app/FRONTEND_ARCHITECTURE.md`）。

### DB 层 `src/db/`

| 文件 | 用途 |
|---|---|
| `src/db/index.ts` | IndexedDB 初始化 / schema / `getDb(userId)` 工厂 |
| `src/db/messageRepo.ts` | 消息 CRUD |
| `src/db/logRepo.ts` | 日志 CRUD |
| `src/db/prefsRepo.ts` | 偏好 k/v 持久化 |

### Gateway 子层 `src/gateway/`

| 文件 | 用途 |
|---|---|
| `src/gateway/client.ts` | re-export `api` 单例（所有 HTTP REST 入口），供 Services 层调用 |
| `src/gateway/sse.ts` | `SSEManager`：Chat SSE + Logs SSE 连接生命周期管理 |
| `src/gateway/auth.ts` | Token 获取 / URL 注入 |

### Business 层 `src/application/`

| 文件 | 用途 |
|---|---|
| `src/application/store.ts` | Zustand 全局状态（纯状态容器 + 同步 setter） |
| `src/application/index.ts` | Service 单例工厂（`userId`-scoped 懒惰初始化） |
| `src/application/messageService.ts` | 消息完整生命周期（发送、delta sync、SSE 处理） |
| `src/application/logService.ts` | 日志业务逻辑 |
| `src/application/syncService.ts` | SSE 生命周期 + delta sync 协调 |
| `src/application/agentService.ts` | Agent CRUD + 初始化 + VM setup 流程 |
| `src/application/modelService.ts` | 模型配置管理 |
| `src/application/layoutService.ts` | 布局持久化 |
| `src/application/converters.ts` | RawMessage ↔ VM ↔ ServerRow 纯函数转换 |

### Render 层 `src/components/`

| 文件 | 用途 |
|---|---|
| `src/components/hooks/useMessages.ts` | 消息 hook（读 store + 调 messageService） |
| `src/components/hooks/useLogs.ts` | 日志 hook |
| `src/components/hooks/useAgent.ts` | Agent hook（含 VM setup 流程） |
| `src/components/hooks/useModels.ts` | 模型 hook |
| `src/components/hooks/useLayout.ts` | 布局 hook |
| `src/components/hooks/useSettings.ts` | 设置 hook（API keys、models、skills、agent tools） |

### 媒体流服务（Tauri 专属）

| 文件 | 用途 |
|---|---|
| `src/services/vncStream.ts` | noVNC 共享连接管理（单例，多组件共享） |
| `src/services/scrcpyStream.ts` | scrcpy 视频流共享管理（WebSocket + WebCodecs） |

### 关键 UI 组件

| 文件 | 用途 |
|---|---|
| `src/components/Layout/DeviceFloatingPanel.tsx` | VM/AVD 悬浮窗（preview/expanded/operating 三态） |
| `src/components/Visual/ExecutionLog.tsx` | Execution Log 完整视图（树形 subagent 分组） |
| `src/components/Visual/CollapsibleExecutionLog.tsx` | Execution Log 悬浮小条（摘要 + 展开） |
| `src/components/Visual/LogCapsule.tsx` | 单个 subagent 的日志胶囊组件 |

### noVNC 版本锁定

```json
"@novnc/novnc": "^1.5.0"
```

> ⚠️ 不要升级到 1.6+。新版本使用 top-level await，与 Vite 开发模式不兼容，会报 `top-level await` 错误。

---

## 九、数据库 Schema 关键表

> 数据库：`/opt/novaic/data/gateway.db` (SQLite, schema v45)

| 表 | 用途 |
|---|---|
| `agents` | Agent 实体（每个用户对话对象） |
| `subagents` | SubAgent（main + sub，有 `parent_subagent_id` 树结构） |
| `subagent_context` | SubAgent 的 LLM context 消息（append-only） |
| `execution_logs` | 工具调用日志（`subagent_id` 归属，支持 upsert） |
| `sessions` | 会话 |
| `chat_messages` | 用户/Agent 消息 |
| `devices` | VM/Android 设备（`status` 字段可能落后于实际状态） |
| `tasks` | 异步后台任务（shell/browser/tool 等） |
| `users` | 用户表（为内部 JWT auth 预留，Clerk 模式下不用此表做登录） |
| `refresh_tokens` | 内部 JWT refresh token（Clerk 模式下不用） |

### 多用户相关表字段

所有业务数据表均含 `user_id TEXT NOT NULL DEFAULT ''` 字段（schema v44+ 迁移后不再有空值）。

### execution_logs 的 subagent_id 历史遗留

旧日志的 `subagent_id = 'main'`（DB default），新日志为 `'main-{agent_id[:8]}'`。  
前端 `groupLogsBySubagent` 会把两者分到不同 key，`sortedCapsuleIds` 逻辑会跳过 legacy `'main'` 避免重复显示。

---

## 十、SSE 事件类型

### Chat SSE — `GET /api/chat/stream`

| 事件 | 说明 |
|---|---|
| `AGENT_REPLY` | Agent 文字回复 |
| `AGENT_ASK` | Agent 提问 |
| `AGENT_NOTIFY` | Agent 通知 |
| `STATUS_UPDATE` | 消息已读状态更新 |

### Log SSE — `GET /api/logs/stream`

| 事件 | 说明 |
|---|---|
| `log_entry` | 连接时推送历史日志（含完整内容） |
| `logs_updated` | 有新日志（轻量通知，前端需再 GET /api/logs/entries 拉取） |
| `subagent_update` | SubAgent 生命周期变更（spawned/running/completed/failed/cancelled） |

---

## 十一、常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| LVM 启动失败（设备状态 `error`） | DB 状态为 `error` 被 `start_device` 拒绝 | 已修复：`error` 状态允许重试启动 |
| VNC 连接不上（重启 App 后自动好） | QMP 单客户端限制 / 内存状态丢失 | Scheme A：只检查 socket 文件存在性 |
| scrcpy 操作模式无响应（Broken Pipe 刷屏） | 控制 TCP 连接断了但 task 不退出 | 已修复：write 失败后 break，触发重连 |
| AVD 停机失败 | DB `device_serial` 为空 | 已修复：从 live 设备列表动态解析 serial |
| Port 1420 已占用 | 上次 tauri:dev 未退出 | `kill $(lsof -ti:1420)` |
| `npm run tauri build --ci` 报错 | `--ci` 只接受 true/false | 改用 `npm run tauri:build -- --bundles app` |
| noVNC top-level await 报错 | 版本 >= 1.6 | 保持 `@novnc/novnc: ^1.5.0` |
| CloudBridge 500 / auth validate 500 | gateway 进程没有 `JWT_SECRET` 环境变量 | 用 `bash /opt/novaic/restart_gw.sh` 而非直接 nohup 启动 |
| App 一直显示 "Connecting..." | Rust `initialize()` 在 JWT 推送前执行 | `App.tsx` 已修复：`await pushToken()` 后再调 `initialize()` |
| Rust panic "Cannot block current thread" | 在 async fn 里用了 `blocking_read()` | 改为 `token.read().await.clone()` |
| Gateway 无响应 / 注册登录 500 | `UserRepository` 写操作未用 `transaction()` 包裹，导致事务悬挂、写锁永不释放 | 已修复（`user.py`）：所有 INSERT/UPDATE/DELETE 改为 `with db.transaction("global")` |
| Gateway 无响应（重启后恢复） | 强制 kill gateway 后 WAL/SHM 文件损坏，新进程被旧锁卡住 | `rm -f /opt/novaic/data/gateway.db-wal /opt/novaic/data/gateway.db-shm` 后再 `bash /opt/novaic/restart_gw.sh` |
| Gateway 注册/登录 500（写锁悬挂） | `UserRepository` 写操作缺少 `db.transaction()` 包裹，INSERT 后事务未提交，写锁永不释放 | 已修复（`user.py`）：所有写操作改为 `with db.transaction("global")` |
| 数据迁移后数据丢失 | 在 gateway 有未提交事务时执行了 `PRAGMA wal_checkpoint(TRUNCATE)`，把未提交数据截断 | **禁止**在 gateway 运行时执行 `wal_checkpoint(TRUNCATE)`；正常迁移直接用 `BEGIN/COMMIT` 即可 |

---

## 十二、环境变量与配置

### 本地 Tauri App

VmControl 读取的路径约定：
- SSH Key：`~/.novaic/.ssh/id_rsa`（`DATA_DIR` 由 App 启动时确定）
- QMP Socket：`/tmp/novaic/novaic-qmp-{agent_id}.sock`
- VNC Socket：`/tmp/novaic/novaic-vnc-{id}.sock`

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

### 本地 App 环境变量

```bash
# novaic-app/.env
VITE_GATEWAY_URL=https://api.gradievo.com
```

---

## 十三、待办 / 技术债

- [x] 将 `/tmp/restart_gw.sh` 移到 `/opt/novaic/restart_gw.sh` 防止重启丢失 ✓
- [x] SSE 广播按 `user_id + agent_id` 隔离 ✓
- [x] `UserRepository` 写操作加 `transaction()` 防止锁悬挂 ✓
- [ ] `execution_logs` 的 `subagent_id = 'main'` legacy 数据迁移为 `'main-{agent_id[:8]}'`（消除前端兼容逻辑）
- [ ] VM 停机后 socket 文件清理（当前 VNC socket 在 VM 停后仍残留）
- [ ] scrcpy 重连后 `retryCount` 上限（当前 3 次后停止，用户需手动点"连接设备"）
- [ ] 设备状态轮询与 DB 状态同步（现在可能出现 DB 状态落后于实际运行状态的情况）
- [ ] Gateway DB 访问改为异步（当前同步 SQLite 在 async FastAPI 中，高并发下仍有阻塞风险；长期方案：`aiosqlite` 或 `run_in_executor`）

---

## 十四、数据库操作安全规范

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
