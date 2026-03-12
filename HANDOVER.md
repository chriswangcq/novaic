# NovAIC 项目交接文档

> 最后更新：2026-03-11（OTA CI 校验、P2P 打洞移除、setup show 修复、deploy-all 一键部署）

---

## 快速上手

| 需求 | 操作 |
|---|---|
| 本地跑起来 | `cd novaic-app && npm install && npm run tauri:dev` |
| **iOS 构建安装** | `cd novaic-app && ./scripts/build-and-install-ios.sh` |
| 改前端 UI | 改 `novaic-app/src/components/`，热更新生效 |
| 改 Gateway API | 改 `novaic-gateway/`，部署见第五节 |
| 改 Relay 服务 | 改 `novaic-quic-service/`，`git push` 后 `ssh relay 'cd /opt/novaic/novaic-quic-service && git pull && cargo build --release && cp target/release/novaic-quic-service ./ && systemctl restart novaic-quic-service'` |
| **一键部署全部** | `./scripts/deploy-all.sh [version]`（默认 0.3.0）：前端→Relay→iOS→macOS。relay SSH 端口 52222。 |
| **部署前端热更新** | 一、构建并 rsync 到 relay；二、更新 Gateway 环境变量并重启；三、手机端 `./scripts/build-and-install-ios.sh`。relay 用 52222 时需 `-e "ssh -p 52222"`。详见五附「前端热更新」 |
| 改消息/日志逻辑 | `messageService.ts`、`logService.ts`、`syncService.ts` |
| 清空本地缓存 | Settings → Clear Cache → 清空本地 DB 缓存 |
| 查架构 | `novaic-app/FRONTEND_ARCHITECTURE.md`、`docs/DESIGN-P2P-UNIFIED.md`、`docs/COMMANDS_SPLIT_DESIGN.md` |

---

## 一、项目整体架构

```
用户 macOS 桌面
└── NovAIC.app (Tauri)
    ├── 前端 React/Vite          ← novaic-app/src/
    │   ├── IndexedDB 本地缓存   ← 消息、日志、偏好、附件（按 userId 隔离）
    │   └── SSE 连接             ← 当前按 agent 维度，计划改为 user 维度
    └── Rust 后端
        ├── vmcontrol（内嵌）     ← novaic-app/src-tauri/vmcontrol/
        │   ├── 管理 QEMU Linux VM (QMP socket)
        │   ├── 管理 Android 模拟器 (scrcpy 代理)
        │   ├── VM 准备 API：环境检查、镜像检查/下载、部署等待
        │   └── 供 Gateway 经 Cloud Bridge 调用
        ├── vnc_proxy             ← 桌面+移动端：P2P 连接 VNC/Scrcpy（移动端仅远端路径）
        └── CloudBridge WebSocket ──► 云端 Gateway（在 vmcontrol 内）

云端服务器 api.gradievo.com
└── Nginx (HTTPS/443 → 127.0.0.1:19999)
    ├── auth_request → /internal/auth/validate  ← HS256 JWT 验证，注入 X-User-ID
    └── Gateway (Python/FastAPI, port 19999)
        ├── SSE: /api/user/chat/stream, /api/user/logs/stream（User 维度）；兼容 /api/chat/messages?agent_id=xxx
        ├── REST: /api/**, /internal/**
        ├── CloudBridge WebSocket: /internal/pc/ws
        ├── P2P: /api/p2p/heartbeat, locate, relay-request
        └── SQLite: /opt/novaic/data/gateway.db

云端服务器 relay.gradievo.com + stun.gradievo.com（novaic-quic-service 同机）
└── STUN (UDP 3478) + Relay (QUIC 443) + Nginx 静态前端
    ├── STUN: 供 PC 获取外网地址（RFC 5389）
    ├── Relay: P2P 直连不可达时兜底，配对 PC/手机 QUIC 连接并转发 stream（打洞已移除，仅 relay）
    └── relay.gradievo.com/resource/frontend/: App 热更新 CDN，版本化路径 /resource/frontend/v{version}/，见五附「前端热更新」
```

### Gateway URL 配置

- **Tauri HTTP 请求**：通过 `gateway_get` / `gateway_post` 等命令，URL 来自 Rust 的 `gateway_url.txt`（`{data_dir}/gateway_url.txt`，默认 `https://api.gradievo.com`）
- **前端 SSE**：使用 `invoke('get_gateway_url')` 获取运行时 URL，与 HTTP 保持一致，避免本地开发时 SSL 错误

---

## 二、代码仓库说明

| 仓库目录 | GitHub | 用途 |
|---|---|---|
| `novaic-app` | chriswangcq/novaic-app | Tauri 桌面应用（主仓库） |
| `novaic-gateway` | chriswangcq/novaic-gateway | 云端 Gateway（API + DB） |
| `novaic-quic-service` | chriswangcq/novaic-quic-service | STUN + Relay（P2P 兜底） |
| 其余子目录 | 各自独立 repo | agent runtime、工具服务等，部署在云端 |

**注意**：每个子目录都是独立 git repo，不是 monorepo，`.git` 在子目录内。父仓库 `new-build-novaic` 无 remote 时仅作本地聚合。

### 分支与合并（2026-03）

| 仓库 | 主分支 | 说明 |
|---|---|---|
| novaic-app | main | fix/ios-black-screen-saturated 已合并 |
| novaic-gateway | main | multi-user 已合并 |
| novaic-tools-server | main | multi-user 已合并 |
| novaic-mcp-vmuse | main | multi-user 已合并 |
| novaic-quic-service | main | 独立 repo，已推送到 GitHub |

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

#### iOS 缩放与键盘行为

- **防缩放**：`index.html` viewport 含 `maximum-scale=1, minimum-scale=1, user-scalable=no`；`index.css` 含 `touch-action: manipulation`
- **键盘弹出**：`interactive-widget=resizes-content` + `visualViewport` polyfill，使内容区缩小而非整页上推

#### 调试用 Hello World 项目

独立最小项目 `tauri-ios-hello/` 用于验证 Tauri iOS 构建流程，与主应用解耦：

```bash
cd tauri-ios-hello
./scripts/build-and-install-ios.sh
```

配置与 novaic-app 相同（Team、bundle `com.novaic.app.hello`），便于单独调试。

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
# 方式 A：使用部署脚本（推荐，rsync 同步代码，避免 git pull 冲突）
cd novaic-gateway
git add -A && git commit -m "..." && git push
./scripts/deploy-gateway.sh root@api.gradievo.com

# 方式 B：手动 git pull（若服务器有本地修改可能冲突）
cd novaic-gateway
git add -A && git commit -m "..." && git push
ssh root@api.gradievo.com 'cd /opt/novaic/services/novaic-gateway && git pull'
ssh root@api.gradievo.com 'cp /opt/novaic/services/novaic-gateway/scripts/restart_gw.sh /opt/novaic/ && bash /opt/novaic/restart_gw.sh'

# 验证
ssh root@api.gradievo.com 'ss -tlnp | grep 19999'
```

### 重启脚本（repo 内维护）

- **源文件**：`novaic-gateway/scripts/restart_gw.sh`（进 git）
- **部署位置**：`/opt/novaic/restart_gw.sh`（deploy-gateway.sh 会 rsync 同步）
- **deploy-gateway.sh**：rsync 部署代码（避免 git pull 冲突）、同步 restart_gw.sh、若 jwt_secret.env 缺 FRONTEND_CDN_URL 则自动追加
- **依赖**：`/opt/novaic/jwt_secret.env` 含 `JWT_SECRET`、可选 `RELAY_URL`、可选 `FRONTEND_CDN_URL`（前端 OTA）
- **模板**：`scripts/jwt_secret.env.example`，首次部署时复制并填写

### Nginx 配置

- 位置：`/etc/nginx/sites-enabled/novaic`（来源：`novaic-gateway/nginx/novaic-cloud.conf`）
- **生产部署**：`novaic-cloud.conf` 含占位符，需替换后部署。运行 `nginx/deploy-nginx.sh` 生成配置，再 scp 到服务器并 reload。若修改了 novaic-cloud.conf（如新增公开路由），需重新部署 nginx 配置
- HTTP(80) → HTTPS(301) 跳转
- HTTPS(443) 代理到 `127.0.0.1:19999`
- **认证方式（2026-03 起）**：Nginx `auth_request` 调用 `/internal/auth/validate`，验证 Clerk RS256 JWT，提取 `sub` 作为 `X-User-ID` 注入下游请求
- 客户端伪造的 `X-User-ID` header 在 Nginx 层被剥离（`proxy_set_header X-User-ID ""`）
- SSE 路由（`/api/chat/messages`、`/api/logs/stream`、`/api/user/chat/stream`、`/api/user/logs/stream` 等）关闭 proxy buffering、超时 3600s
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

## 五附、novaic-quic-service（STUN + Relay）

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

**OTA 开关**：默认关闭。需在 App 启动环境设置 `NOVAIC_OTA_ENABLED=1`（或 `true`/`yes`/`on`）才启用 OTA。未设置时始终使用本地打包前端。

**OTA 三处同步**：新增或变更 CDN 域名时，需同时修改以下三处，否则会 navigate 失败或 invoke 不可用：

| 位置 | 修改项 |
|------|--------|
| `novaic-app/src/config/index.ts` | `OTA_ORIGINS` 数组 |
| `novaic-app/src-tauri/capabilities/remote-frontend.json` | `remote.urls` |
| `novaic-app/src-tauri/src/setup.rs` | `OTA_ALLOWED_HOSTS` 常量 |

当前允许的 host：`relay.gradievo.com`、`api.gradievo.com`。

**CI 校验**：`scripts/check-ota-sync.sh` 校验三处一致性，已在 `.github/workflows/tauri-ci.yml` 中执行。本地运行：`bash scripts/check-ota-sync.sh`。

**OTA 调试**：浏览器打开 CDN URL 时，`sessionStorage.setItem('novaic_ota_debug', '1')` 后刷新，控制台输出 `[OTA] Debug` 信息。

#### 一键部署（推荐）

```bash
./scripts/deploy-all.sh [version]   # version 默认 0.3.0
```

依次执行：1) 前端构建并 rsync 到 relay；2) novaic-quic-service 推送并重启；3) iOS 构建安装；4) macOS 桌面 App 构建。完成后需手动更新 Gateway 的 `FRONTEND_CDN_URL` 并重启。

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

重启 Gateway：`ssh root@api.gradievo.com 'bash /opt/novaic/restart_gw.sh'`

**三、手机端构建**

iOS 一键构建并安装：`cd novaic-app && ./scripts/build-and-install-ios.sh`

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

详见 `docs/HOT_UPDATE_DEPLOY_STEPS.md`。

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

- `docs/PHASE5-DEPLOYMENT.md` — 部署详细流程
- `docs/HOT_UPDATE_DEPLOY_STEPS.md` — 前端热更新部署（frontend.gradievo.com）
- `docs/DESIGN-novaic-quic-service.md` — 服务设计
- `docs/DESIGN-P2P-UNIFIED.md` — P2P 架构总览

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
| `novaic-app/src-tauri/src/main.rs` | 单一入口，setup 内 `#[cfg]` 分支；桌面：Tray、VmControl、VncProxy；`update_cloud_token` 命令 |
| `novaic-app/src-tauri/src/mobile.rs` | 移动端 setup：调用 setup::setup_shared，默认云端 Gateway |
| `novaic-app/src-tauri/src/setup.rs` | 共享 setup：Gateway URL、StorageBackend、VncProxy 统一注入（桌面+移动端） |
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

## 七、关键架构决策与注意点

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

### Gateway 设备启停状态门控

`start_device` 允许状态：`READY` / `STOPPED` / `ERROR`（ERROR 状态可以重试启动）

`stop_device` 无状态门控：无论 DB 状态如何，都尝试停止（防止 DB 状态过期导致无法停机）。

**文件**：`novaic-gateway/gateway/api/devices.py`

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

### VncProxy（桌面+移动端）

- **桌面**：本地路径（QUIC loopback）+ 远端路径（Gateway locate + P2P）
- **移动端**：仅远端路径（无本地 VmControl，`local_vmcontrol` 恒为 None）
- **P2P 流程**：打洞已移除，远端 VNC/Scrcpy 仅走 relay（relay-request → connect_via_relay）
- **命令**：`get_vnc_proxy_url`、`get_scrcpy_proxy_url` 在 `commands/vnc_urls.rs`（全平台）

---

## 八、前端关键文件

> 前端采用 **Render / Business / DB 三层架构**（详见 `novaic-app/FRONTEND_ARCHITECTURE.md`）。

### 应用启动与 Agent 选择流程

1. **登录**：`auth.ts` 存 token → `App.tsx` 调用 `update_cloud_token` 推给 Rust → `initialize()` 启动 VmControl
2. **恢复 Agent**：从 `prefsRepo.getSelectedAgent()` 或 localStorage 恢复上次选中的 agentId
3. **选择 Agent**：`AgentService.selectAgent(agentId)` → `SyncService.switchAgent(agentId)` → 断开旧 SSE → load 消息/日志 → 建立新 SSE
4. **登出**：`getSyncService().disconnect()` 断开 SSE，`resetServices()` 清空 Service 单例

### DB 层 `src/db/`（DB 驱动渲染）

**原则**：IndexedDB 为单一事实来源，消息/日志全部来自 DB，UI 通过订阅响应变更。

| 文件 | 用途 |
|---|---|
| `src/db/index.ts` | IndexedDB 初始化 / schema / `getDb(userId)` 工厂 / `clearLocalDb()` |
| `src/db/messageRepo.ts` | 消息 CRUD，写后 `notifyMessageChange` |
| `src/db/messageSubscription.ts` | 消息变更订阅 `subscribe(userId, agentId, cb)` |
| `src/db/logRepo.ts` | 日志 CRUD |
| `src/db/logSubscription.ts` | 日志变更订阅 |
| `src/db/prefsRepo.ts` | 偏好 k/v 持久化 |
| `src/db/fileRepo.ts` | 附件缓存（图片 Blob、文件 local_path） |

**数据流**：`messageRepo.putMessages()` → `notifyMessageChange()` → `useMessagesFromDB` 的 callback → `refetch()` 从 DB 读 → 渲染。日志同理。

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
| `src/application/syncService.ts` | SSE 生命周期 + delta sync 协调；`switchAgent(agentId)` 时 disconnect → load → connectChat + connectLogs |
| `src/application/agentService.ts` | Agent CRUD + 初始化 + VM setup 流程 |
| `src/application/modelService.ts` | 模型配置管理 |
| `src/application/layoutService.ts` | 布局持久化 |
| `src/application/converters.ts` | RawMessage ↔ VM ↔ ServerRow 纯函数转换 |
| `src/application/messagePaginationStore.ts` | 消息分页状态（hasMore、isLoading，按 agentId） |
| `src/application/logPaginationStore.ts` | 日志分页状态（hasMore、isLoading、lastLogId，按 agentId + logSubagentId） |
| `src/application/logFilterStore.ts` | 日志过滤（logSubagentId、logSubagents） |
| `src/application/logInputCacheStore.ts` | 日志 input 按需加载缓存 |

### Render 层 `src/components/` 与 `src/hooks/`

| 文件 | 用途 |
|---|---|
| `src/hooks/useMessagesFromDB.ts` | DB 驱动消息列表，订阅 `messageSubscription`，变更时 refetch |
| `src/hooks/useLogsFromDB.ts` | DB 驱动日志列表，订阅 `logSubscription` |
| `src/components/hooks/useMessages.ts` | 消息 hook（组合 useMessagesFromDB + messagePaginationStore + messageService） |
| `src/components/hooks/useLogs.ts` | 日志 hook（组合 useLogsFromDB + logPaginationStore + logService） |
| `src/components/hooks/useAgent.ts` | Agent hook（含 VM setup 流程） |
| `src/components/hooks/useModels.ts` | 模型 hook |
| `src/components/hooks/useLayout.ts` | 布局 hook |
| `src/components/hooks/useSettings.ts` | 设置 hook（API keys、models、skills、agent tools） |

### VM Setup 服务

| 文件 | 用途 |
|---|---|
| `src/services/setup.ts` | 环境检查、镜像检查/下载、VM 创建、部署等待（均通过 gateway_get/post 调用 Gateway） |
| `src/components/Setup/EnvironmentCheck.tsx` | 环境检查 UI（调用 `gateway_get('/api/vm/environment')`） |

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
| `src/components/Visual/MainAgentLogPreview.tsx` | 主 Agent 执行日志预览（独立组件） |
| `src/components/Visual/SubagentList.tsx` | Subagent 列表（独立组件，与 MainAgentLogPreview 无联动） |
| `src/components/Visual/LogCapsule.tsx` | 单个 subagent 的日志胶囊组件 |

### 前端布局与交互（2026-03 更新）

#### ChatPanel 布局结构

```
ChatPanel
├── DeviceFloatingPanel (compact)     ← 右上角浮层，不占布局
├── 主内容区 (flex-1)
│   ├── MessageList
│   └── Execution Log（展开时，可拖拽调整高度）
└── 底部 (shrink-0)
    ├── CollapsibleExecutionLog（收起时，在输入框上方）
    └── ChatInput
```

#### MainAgentLogPreview 与 SubagentList

- **独立组件**：主 Agent 执行日志与 Subagent 列表上下分离，无联动
- **MainAgentLogPreview**：主 Agent 日志预览（最多 4 条），sleeping 时不显示
- **SubagentList**：Subagent 胶囊列表，点击打开该 agent 的完整日志弹窗
- **位置**：输入框正上方（与展开态 Execution Log 一致）

#### DeviceFloatingPanel 浮窗配置

**所有参数集中**：`DeviceFloatingPanel.tsx` 顶部 `FLOATING_PANEL_LAYOUT`

```typescript
FLOATING_PANEL_LAYOUT = {
  right: 20,           // 距视口右边 (px)
  gap: 10,             // 卡片间距
  previewMaxH: 200,    // 预览最大高度
  previewBaseW: 154,   // 高度计算基准宽度
  deviceRatio: { linux: 16/10, android: 9/19.5 },
  stackTop: 100,       // 顶部浮窗距顶
  stackBottom: 96,     // 底部浮窗距底
  overlayHPad, overlayTopPad, overlayBottomPad, headerH,
  chipH: 40,
  spacerExtra: 8,
}
```

- **尺寸计算唯一入口**：`getPreviewSize(type)`，高度受 `previewMaxH` 限制，宽度按宽高比自适应
- **compact 模式**：右上角浮层，不占布局空间；点击展开逻辑不变

#### 模型选择

- **配置入口**：Settings → Agent Tools → 选择 Agent → Model 下拉
- **ChatInput**：已移除模型选择器，模型在 Agent Tools 中配置
- **存储**：`getModelService().setModel(agentId, compositeId)`，composite 格式 `api_key_id:model_id`

#### Header 与导航

- **左右切换**：使用 `agents` 数组顺序，循环切换
- **标题居中**：`grid grid-cols-[auto_1fr_auto]`
- **右上角**：`...` 按钮（MoreVertical），替代原 Settings 图标

#### Settings 模态与 Tab

- **Tab 类型**：`models | agents | skills | agent-tools | cache | user`
- **User tab**：邮箱、显示名称、退出登录
- **Agent Tools**：选择 Agent → 配置 Skills、Device Binding、Model、Bootstrap 文件等

#### 主布局结构（LayoutContainer）

```
PC 式（宽度 ≥ LAYOUT_THRESHOLD）：
  PrimaryNav | AgentDrawer | Main(Header + ChatPanel/DeviceManagerPage/SettingsModal)

手机式（宽度 < 阈值）：
  - 第二栏（narrowPage=sidebar）：NarrowHeader + AgentDrawer（含 agents/devices/setting 列表）
  - 第三栏（narrowPage=chat/devices/settings）：Header + 对应内容，底 tab 隐藏，可返回
```

- **narrowPage**：`sidebar | chat | devices | settings`，控制手机式下当前显示哪一栏
- **PrimaryTab**：`agents | devices | setting`，主导航三个 tab
- **activeView**：`chat | devices`，决定 Main 区渲染 ChatPanel 还是 DeviceManagerPage

#### Tauri 窗口拖拽区

`data-tauri-drag-region` 用于无边框窗口拖动，已加在：

| 组件 | 位置 |
|---|---|
| PrimaryNav | 红绿灯区、Logo 区、空白区 |
| AgentDrawer | Agents/Devices 标题栏 |
| Header | 左右占位 div |
| DeviceManagerPage | 标题栏 |
| SettingsModal | 标题栏 |
| NarrowHeader | 整行 |

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

### noVNC 版本锁定

```json
"@novnc/novnc": "^1.5.0"
```

> ⚠️ 不要升级到 1.6+。新版本使用 top-level await，与 Vite 开发模式不兼容，会报 `top-level await` 错误。

---

## 九、模型与 Agent 配置

### 模型选择流程

```
用户选择模型 (composite: api_key_id:model_id)
  → getModelService().setModel(agentId, composite)
  → 更新 store.selectedModel + prefsRepo
  → gateway.setAgentModel(agentId, modelId)  // modelId = composite 中冒号后的部分
```

### Gateway 模型 API

| 接口 | 说明 |
|---|---|
| `GET /api/agents/{id}/model` | 获取 agent 当前模型配置 |
| `PUT /api/agents/{id}/model` | 设置 agent 模型，body: `{ model_id: string }` |

### candidate_models 表

- `id` + `api_key_id` 联合主键
- `agents.model_id` 存 model id，与 `candidate_models.id` 匹配

### 切换 Agent 时模型加载

```
AgentService.selectAgent(agentId)
  → ModelService.loadForAgent(agentId)
  → gateway.getAgentModel(agentId)
  → store.patchState({ selectedModel: composite })
  → prefsRepo.setSelectedModel(userId, composite)
```

---

## 十、数据库 Schema 关键表

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

## 十一、SSE 事件与连接管理

### 当前逻辑（Agent 维度）

- **Chat SSE**：`GET /api/user/chat/stream`（User 维度，无 agent_id）
- **Logs SSE**：`GET /api/user/logs/stream`（User 维度，无 agent_id）
- **前端**：登录后 `connectUserStream()` 建立一次连接；`switchAgent(agentId)` 仅 load，不断连
- **SSE URL**：前端通过 `invoke('get_gateway_url')` 获取，与 Tauri HTTP 请求一致

### Chat SSE 事件

| 事件 | 说明 |
|---|---|
| `AGENT_REPLY` | Agent 文字回复 |
| `AGENT_ASK` | Agent 提问 |
| `AGENT_NOTIFY` | Agent 通知 |
| `STATUS_UPDATE` | 消息已读状态更新 |

### Log SSE 事件

| 事件 | 说明 |
|---|---|
| `log_entry` | 单条新日志 |
| `log_batch` | 连接时推送历史日志批次 |
| `logs_updated` | 有新日志（轻量通知，前端需再 GET /api/logs/entries 拉取） |
| `subagent_update` | SubAgent 生命周期变更（spawned/sleeping/awake/running/completed/failed/cancelled） |

### SSE 改造计划（User 维度）

目标：一个用户一条长连接，切换 agent 不断连，事件持续写入 DB。详见 **docs/SSE_USER_LEVEL_MIGRATION.md**。

---

## 十二、常见问题

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
| SSE SSL 错误 | 前端 SSE 曾用 VITE_GATEWAY_URL，与 Tauri 的 gateway_url.txt 不一致 | 已修复：SSE 使用 `invoke('get_gateway_url')` 与 HTTP 一致 |
| 本地 DB 缓存异常 | IndexedDB 数据损坏或需强制刷新 | Settings → Clear Cache → 清空本地 DB 缓存，然后刷新页面 |
| LLM think 失败（429 / engine_overloaded） | Moonshot 等 API 限流或过载 | 间歇性，非 context 问题；建议对 429 做指数退避重试 |
| 截图无法截到指定 subuser 的屏幕（shell 可以） | `runtime_context` 缺少 `display` 字段 | 已修复：`build_runtime_context` 为 vm_user 注入 `display: ":11"` 等 |
| iOS 安装后黑屏 | custom-protocol 在 WKWebView 有已知问题；或 VITE_GATEWAY_URL 缺失导致启动抛错 | 已修复：iOS 用 `--features mobile` 不含 custom-protocol；config 兜底默认 Gateway URL |
| `tauri ios run` 报 exportOptionsPlist 找不到 | Tauri CLI 传相对路径，xcodebuild 工作目录不对 | 用 `tauri ios build` + `devicectl device install app`，见 `scripts/build-and-install-ios.sh` |
| iOS 构建报 "Arch specified by Xcode was invalid" | project.yml 含 `${FORCE_COLOR}` 被解析为 arch 参数 | 运行 `bash scripts/patch-ios-xcode.sh` 修复 |
| iOS 构建报 `no method named 'show' found for WebviewWindow` | `WebviewWindow::show` 仅 `#[cfg(desktop)]` 存在，移动端无此方法 | 已修复：`setup.rs` 中 `show_main_window` 用 `#[cfg(desktop)]` 包裹，移动端窗口默认可见 |
| VNC WebSocket 连接 127.0.0.1 失败 | ATS 默认阻止 ws:// | patch-ios-xcode.sh 已注入 `NSAllowsLocalNetworking` |
| VNC 连接被对方重置 (code 1006) | 移动端用 agent UUID 做 P2P locate，而 locate 需要 VmControl Ed25519 device_id | 已修复：`get_vnc_proxy_url` 在无 local_vmcontrol 时调用 `GET /api/p2p/my-devices` 取第一个 online 的 device_id |
| VNC 间歇性失败（连接被对方重置） | Relay 竞态、CloudBridge JWT 过期、VncProxy 未发 Close 帧 | 2026-03-11 修复：relay 初始延迟 2s→6s；connect_relay 用最新 token；vnc_proxy 错误时发送 Close 帧 |
| 排查 P2P 请求是否到达 Gateway | 需确认 locate 是否被调用 | `GET /api/p2p/debug`（需 JWT）返回最近 50 条 P2P 事件；`novaic-gateway/scripts/check-p2p-debug.sh` |
| VNC locate 返回 online 但连接失败 | PC 端 STUN 失败，ext_addr=0.0.0.0 不可连接 | Gateway 已修复：ext_addr 为 0.0.0.0 时返回 online=False；PC 端每 5 分钟重试 STUN。需确保 PC 允许 UDP 出站（stun.l.google.com:19302） |
| 调试 STUN 是否可用 | 验证本机能否获取外网地址 | `python3 novaic-app/scripts/test-stun.py [port]`（port 默认 19998，若被占用用其他如 45678） |
| 自建 STUN 服务器 | 默认 stun.gradievo.com:3478（novaic-quic-service） | 覆盖用 `NOVAIC_STUN_SERVER=stun.l.google.com:19302` |
| SSE 连接失败（User chat/logs） | 可能 TLS、401 或网络 | 需 Xcode 控制台查看 Rust 错误；后续可改进 Rust 向 JS 传递错误详情 |
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

---

## 十三、环境变量与配置

### 本地 Tauri App

**App 数据目录**（`app.path().app_data_dir()`）：
- macOS：`~/Library/Application Support/com.novaic.app`
- 内含：`gateway_url.txt`（Gateway URL，默认 `https://api.gradievo.com`）、`api_key.txt`、`app.pid` 等

**VmControl 读取的路径约定**：
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
| LAYOUT_CONFIG | LAYOUT_THRESHOLD(1024), DRAWER_WIDTH(288), LOG_HEIGHT_RATIO(0.5) |
| SSE_CONFIG | RECONNECT_DELAY, MAX_RECONNECT_ATTEMPTS |
| POLL_CONFIG | GATEWAY_HEALTH_INTERVAL |
| STORAGE_KEYS | selectedAgent, selectedModel 等 prefs 键名 |

---

## 十四、待办 / 技术债

- [x] 将 `/tmp/restart_gw.sh` 移到 `/opt/novaic/restart_gw.sh` 防止重启丢失 ✓
- [x] SSE 广播按 `user_id + agent_id` 隔离 ✓
- [x] `UserRepository` 写操作加 `transaction()` 防止锁悬挂 ✓
- [x] SSE 使用 Tauri `get_gateway_url` 与 HTTP 一致 ✓
- [x] **SSE 改为 User 维度**：一个用户一条长连接，切换 agent 不断连 ✓（见 docs/SSE_USER_LEVEL_MIGRATION.md）
- [x] **VM 准备 API 迁入 vmcontrol**：环境检查、镜像检查/下载、部署等待统一走 Gateway → Cloud Bridge → vmcontrol ✓
- [ ] `execution_logs` 的 `subagent_id = 'main'` legacy 数据迁移为 `'main-{agent_id[:8]}'`（消除前端兼容逻辑）
- [ ] VM 停机后 socket 文件清理（当前 VNC socket 在 VM 停后仍残留）
- [ ] scrcpy 重连后 `retryCount` 上限（当前 3 次后停止，用户需手动点"连接设备"）
- [ ] 设备状态轮询与 DB 状态同步（现在可能出现 DB 状态落后于实际运行状态的情况）
- [ ] Gateway DB 访问改为异步（当前同步 SQLite 在 async FastAPI 中，高并发下仍有阻塞风险；长期方案：`aiosqlite` 或 `run_in_executor`）

### 前端修改注意事项

- **DeviceFloatingPanel**：改布局参数只改 `FLOATING_PANEL_LAYOUT` 和 `getPreviewSize`
- **CollapsibleExecutionLog**：inline 时 Tab 在底部；非 inline 时已废弃（不再使用顶部浮动）
- **模型相关**：`useModels` 读 store；`getModelService().setModel` 写 store + prefs + gateway

### AgentToolsTab 加载数据

`loadData` 并行拉取：`getToolCategories`、`getAgentToolsConfig`、`getSkills`、`getAgentSkills`、`api.devices.listForUser`、`api.getAgentBinding`、`api.getAgentModel`，以及 `getPromptsPreview`、`getBootstrapFiles`。选择 Agent 后自动触发。

### ExecutionLog 与 CollapsibleExecutionLog

- **ExecutionLog**：完整日志视图，`showHeader` 时显示 subagent tabs（全部/各 subagent 切换）
- **MainAgentLogPreview**：主 Agent 日志预览，独立组件
- **SubagentList**：Subagent 列表，独立组件，点击打开 AgentLogModal

### 关键文件速查

| 需求 | 文件 |
|---|---|
| 改浮窗尺寸/位置 | `DeviceFloatingPanel.tsx` → FLOATING_PANEL_LAYOUT |
| 改 Execution Log 布局 | `MainAgentLogPreview.tsx`、`SubagentList.tsx`、`ChatPanel.tsx` |
| 改模型选择 UI | `SettingsModal.tsx` → AgentToolsTab |
| 改消息发送 | `ChatInput.tsx`、`messageService.ts` |
| 改 Agent 列表 | `AgentDrawer.tsx`、`useAgent.ts` |
| 改主布局/导航 | `LayoutContainer.tsx`、`PrimaryNav.tsx`、`App.tsx` |
| 改 Gateway 配置 API | `novaic-gateway/gateway/api/internal/config.py` |
| 改 VM 准备（环境/镜像/部署） | `novaic-gateway/gateway/api/vm.py`、`vmcontrol/src/api/routes/vm_prep.rs` |
| 改 Relay 服务 | `novaic-quic-service/src/relay.rs`、`protocol.rs`、`auth.rs` |
| 一键部署全部 | `scripts/deploy-all.sh` |
| OTA 三处一致性校验 | `scripts/check-ota-sync.sh`（CI 已集成） |

### Gateway 内部配置（LLM 调用用）

`/internal/config` 返回 agent 的 model 配置：优先用 `agents.model_id`，否则用 `config.default_model`；从 `candidate_models` 解析 `api_key`、`api_base` 供 runtime 调用 LLM。

### 相关文档

| 文档 | 说明 |
|---|---|
| `novaic-app/FRONTEND_ARCHITECTURE.md` | Render/Business/DB 三层、hooks 约束、数据流 |
| `novaic-app/docs/ARCHITECTURE_OVERVIEW.md` | 架构总览、数据流图 |
| `novaic-app/docs/DB_DRIVEN_ARCHITECTURE_CHECK.md` | DB 驱动架构检查清单 |
| `docs/SSE_USER_LEVEL_MIGRATION.md` | SSE 改为 User 维度改造方案 |
| `docs/COMMANDS_SPLIT_DESIGN.md` | Tauri 命令拆分、vm/vmcontrol 关系 |
| `docs/DESIGN-P2P-UNIFIED.md` | P2P 架构、Relay 兜底、Registry/Discovery |
| `docs/PHASE5-DEPLOYMENT.md` | novaic-quic-service 部署指南 |
| `docs/HOT_UPDATE_DEPLOY_STEPS.md` | 前端热更新部署（relay.gradievo.com/resource/frontend/） |
| `docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md` | OTA 重新启用实施方案 |
| `docs/RELAY_MIGRATION_8_TO_47.md` | Relay 迁移 8.146.233.64→47.243.221.45 |
| `SYSTEM_DESIGN.md` | 系统设计 |
| `novaic-app/VNC_SCRCPY_WS_CONNECTIONS.md` | VNC/scrcpy WebSocket 连接说明 |
| 本文档「四、构建与发布 → iOS 部署流程」 | iOS 完整部署流程、黑屏修复、脚本说明 |
| `docs/IOS_BLACK_SCREEN_ISSUE_REPORT.md` | iOS 黑屏问题分析与修复记录 |

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
