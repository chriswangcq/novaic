# OTA 薄壳与生产拓扑

> 对应根目录 `**HANDOVER.md` §2.1–§2.3**。细节与排障仍以 HANDOVER 为准。

## OTA-First 薄壳（Thin Client）

1. **体积小**：Release 仅内嵌约 24KB 静态 Loading（`novaic-app/src-tauri/loading/index.html`）。
2. **按需加载**：启动后从 Relay CDN 拉取前端包；修 Bug 通过 `./deploy frontend` 发版。
3. **本地数据**：Rust 侧 `sqlx` + Entangled；OTA 前端可操作本地 SQLite。

## 桌面端结构（概念）

- **用户 macOS 桌面** → `NovAIC.app`（Tauri）
  - React/Vite（`novaic-app/src/`）
  - **偏好**：`localStorage`（`prefsRepo`）；**消息 / 日志 / 实体**：Entangled + Rust SQLite（`entangled_cache`），业务主存非 Dexie/IndexedDB。
  - **AppBridge WS**：用户维度推送（如 `chat_message`、`config_updated`）。
  - **WebRTC**：远程桌面（VM / Android / HD / Subuser）。
  - **Rust**：Tauri Commands（`gateway_`* HTTP 代理为 IPC 主通道）、**vmcontrol**（`novaic-app/src-tauri/vmcontrol/`：WebRTC、QEMU、Android scrcpy、CloudBridge WS → 云端 Gateway）。

## 云端（概念）

- **api.gradievo.com**：Nginx 443 → Gateway `127.0.0.1:19999`；`auth_request` → `/internal/auth/validate` 注入 `X-User-ID`。
- Gateway：REST、WS Push（`pc_client`）、CloudBridge `/internal/pc/ws`、P2P 相关 API、`gateway.db`（运维向；业务实体见 [data-ownership.md](data-ownership.md)）。
- **relay + STUN**：`novaic-quic-service`；STUN 3478、Relay QUIC 443、静态前端 CDN（`frontend` OTA 路径）。

## macOS 键盘与 SIGTRAP（摘要）

- **根因**：`enigo.key()` / `enigo.text()` 须在 main queue；在 tokio worker 调用可触发 **SIGTRAP**。
- **修复**：macOS 上键盘路径改为 **CGEvent**（`core_graphics`）。关键文件：`vmcontrol/src/input/handler.rs`、`vmcontrol/src/api/routes/hd_tools.rs`。

## TURN 凭证（摘要）

- **coturn**：常见配置 `/etc/turnserver.conf`，3478 UDP/TCP；长期运行可能需重启以清理僵尸 session。
- **流转**：Gateway 注入 TURN 到 `webrtc_offer`；客户端经 `/api/turn/credentials`；VmControl 解析 `ice_servers`（见 `gateway/api/turn.py`、`peer.rs`）。

## 相关文档

- [authentication.md](authentication.md) — JWT  
- [webrtc.md](webrtc.md) — 远端桌面管线  
- [../runbooks/cloud-production.md](../runbooks/cloud-production.md) — 主机路径与 Nginx