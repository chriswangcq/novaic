# NovAIC 项目交接文档 (2026 重构版)

> 最后更新时间：2026-03-22。
> 说明：本文档由原先长期维护的 2600+ 行变更日志提炼重写而来。重点描述**当前的稳定架构、开发部署流程以及核心业务链路**，去除了过时的历史演进细节。

---

## 快速上手指南

| 需求 | 操作 / 脚本 |
|---|---|
| 本地完整跑起来 | `cd novaic-app && npm install && npm run tauri:dev` |
| 纯 UI 调试 | `cd novaic-app && npm run dev` (http://localhost:5173) |
| iOS 部署 | `./deploy ios` (需要连接手机) |
| macOS 打包 | `./deploy desktop` |
| 一键发版全后端 | `./deploy services` |
| 一键更新前端 (OTA) | `./deploy frontend [version]` |
| 一键部署全平台 | `./deploy all [version]` |
| 查服务状态与日志 | `./deploy status` / `./deploy logs [service_name]` |
| 清空本地缓存 | 前端界面：Settings → Clear Cache → 清空本地 DB 缓存 |
| 修改前端 UI | 编辑 `novaic-app/src/components/` ( Vite 热更新立即生效) |

---

## 一、 系统架构全景

NovAIC 采用 **OTA-First 薄壳客户端 + 强云端协同** 的多服务分布式架构。

### 1.1 核心拓扑图
```text
[ 前端客户端 (macOS App / iOS / Android / Web) ]
 ├── React/Vite (薄壳UI, 仅24KB内置, OTA热更新)
 ├── IndexedDB (本地持久化: 消息/日志/偏好/Agent配置)
 ├── AppBridge WS (单例长连接: 接收 Gateway 推送的聊天与配置同步)
 └── WebRTC PeerConnection (H.264 零延迟远程桌面收流与触控反馈)

[ 本地 Rust Sidecar (VmControl) ] - 桌面端内置，提供底层操作能力
 ├── WebRTC Engine (macOS VideoToolbox GPU编码 / openh264)
 ├── 本机操控 (CGEvent键鼠模拟) / Android 操控 (scrcpy) / Linux VM (QEMU+VNC)
 └── CloudBridge WebSocket (直连云端，接收并执行云端的虚拟设备控制指令)

[ 云端服务 api.gradievo.com (Python / FastAPI / SQLite) ]
 ├── Nginx反代 (HTTPS/443, /internal/auth/validate JWT认证清洗)
 ├── Gateway (19999) —— 核心大脑，路由转发
 │    ├── API REST / CloudBridge WS / App WS 推送
 │    ├── 局域网/广域网串流协商 (Webrtc 信令中转)
 │    └── SQLite (agents, devices, config 用户设定)
 ├── LLM Factory (19990) —— 所有大模型 API Key 加密存储与请求收口
 ├── Agent Runtime Worker & Watchdog —— 异步处理 LLM 对话和状态图 (Sagas)
 ├── Tools Server —— 隔离执行 Shell、文件、浏览器等工具调用
 └── File Service —— 聊天附件与截图的统一存储
 
[ 兜底网络服务 relay.gradievo.com (Rust) ]
 └── novaic-quic-service (STUN 3478 UDP + QUIC Relay 443 + OTA Web Server)
```

### 1.2 架构演进关键决策 (2026-03 最新状态)
* **Frontend-OTA 热更新**：客户端极简，启动时通过 `GET /api/config/frontend` 拿到最新 CDN 链接跳走。做到前端修 Bug 无需审核、秒级部署（`./deploy frontend`）。
* **全信道 WS Push 化**：彻底废弃前端 HTTP长轮询 和 SSE (Server-Sent Events) ，聊天更新、Agent 状态更迭、配置项同步 (`config_updated`) 采用单例 AppBridge WebSocket 进行实时推送和前端的 Zustand Store 去抖拉取。
* **原生 LLM Factory 收口**：大模型调用被全部抽取到 `llm-factory`。Gateway 与 Agent Runtime 均不可见明文 `api_key`，避免密钥在大仓库里各处明文流通。
* **全景 WebRTC 化**：废弃了 noVNC 与内部 WebSocket 屏幕传输，包括本地 Host Desktop 控制、虚拟机和安卓手机屏幕的传输，全部跑在自适应码率和降级的 H.264/WebRTC 通道上。
* **苹果端注入修正**：全方位修复了 iOS 原生的软键盘高度注入、macOS 原生底层的 `CGEvent` 处理以隔离主线程奔溃等问题。

---

## 二、 代码仓库与结构

采用 `git submodules` 形式组织（共13个子包，存放于 `chriswangcq/novaic/` 下）：

```bash
git clone --recurse-submodules git@github.com:chriswangcq/novaic.git
```

| 模块名 (novaic-*) | 职责与语言 |
|---|---|
| `app` | React 前端 + Tauri (含 VmControl) |
| `gateway` | 后端核心 API，用户设备 / 配置管理 (Python) |
| `llm-factory` | 模型 Proxy，统一管理 API Key (Python) |
| `agent-runtime` | 对话轮询、Saga、Watchdog 任务处理 (Python) |
| `tools-server` | Agent 执行计算机与设备操作指令 (Python)|
| `runtime-orchestrator` | Runtime 生命周期流转编排、单次运行 Context 维护 (Python)|
| `quic-service` | STUN / P2P Relay / OTA 配置下发 (Rust) |
| 其他干系包 | Python 公共合约、组件库、抽象层与类型定义 (kernel, contracts...) |

---

## 三、 开发与部署指南

### 3.1 本地开发
* **环境要求**：Node >= 18, RustUp (Stable), macOS 需要 Xcode Command Line Tools。
* **开发与编译**：
  ```bash
  # 常规启动带 Rust 的整套前端开发
  cd novaic-app && npm run tauri:dev
  # 如果 1420 占线，可以： kill $(lsof -ti:1420)
  ```

### 3.2 统一部署 (deploy CLI)
代码根目录封装了自动化程度极高的 `./deploy` 工具，它只会打包和同步增量代码 (Rsync)，重启等控制操作由目标服务器的 `/opt/novaic/start.sh` 执行，无需手动介入重启顺序。
```bash
./deploy frontend [ver]   # 构建前端、同步到 Relay Nginx 下作热更 CDN
./deploy ios              # 本地编译 IPA 并安装给连接到 USB 的真机
./deploy gateway          # 热更 Gateway 代码并让远程重启所有关联进程
./deploy services         # 更新全部后端微服务代码并全量安全重启
./deploy all [ver]        # 万用一键全发版
```

### 3.3 云端运维常识 (api.gradievo.com)
* 所有的后端服务在生产路径 `/opt/novaic/services/` (Data在 `/data/`)。
* 服务由 `/opt/novaic/start.sh` 和 systemd 协同管控进程组。**请不要使用被废弃的 `restart_gw.sh` 脚本进行单一重启**。
* **环境变量管控**：密钥存放于 `/opt/novaic/jwt_secret.env`。
* **清理日志与DB维护**：为避免服务器磁盘与内存膨胀，可通过以下命令对运行时落盘数据清理：
  ```bash
  # 登入 api.gradievo.com 后
  sqlite3 /opt/novaic/data/queue.db "DELETE FROM tq_tasks WHERE status IN ('done','failed'); VACUUM;"
  sqlite3 /opt/novaic/data/runtime_orchestrator.db "UPDATE agent_runtimes SET context='[]' WHERE status='completed'; VACUUM;"
  find /opt/novaic/data/logs/ -name '*.log' -mtime +7 -delete
  ```

---

## 四、 核心业务域与代码流转

### 4.1 统一认证与数据隔离 (Auth & User Mapping)
* **JWT 流转**：用户走 `/auth/login` → `api.gradievo.com` 返回 HS256 JWT Token。该 Token 缓存在客户端 `localStorage`。前端调用将 Token 放 header `Authorization`；Tauri Rust 通过 `invoke(update_cloud_token)` 知道最新态，所有 Rust 发向网关的请求同理携带 Token。
* **Nginx 解析**：云端所有对内的保护路由均由 Nginx 配置的 `auth_request` 预请求 `/internal/auth/validate`。校验通过后，Nginx 滤掉客户端伪造头，强制塞入真实的 `X-User-ID`。
* **数据库级隔离**：后端所有微服务查询 `agents, config, ssh_keys, devices` 必定带 `WHERE user_id = {request.x_user_id}` 物理隔离。

### 4.2 前端 SWR (Stale-While-Revalidate) 更新体系
* **架构演变**：前端对配置、模型、代理、偏好大量采用 IDB(IndexedDB) 首屏直出 + 后台拉新机制。
* **配置跨端协同**：比如 A 设备修改了 Agent 模型为 o1，Gateway 存库后向 B 设备广播 WS 事件：`gateway_push: config_updated`。B 设备前端的 `SyncService` 收到后利用 500ms 去抖动(Debounce)，随后触发对网关全量 `loadConfig()` 更新 Zustand State。
* **注意陷阱**：在 React Hooks 获取用户信息时，`getCachedUser()` 会返回新的对象引用，不要随意将其塞入 `useEffect([user])` 的 deps 数组中，应当提取其纯字符串类似 `userId = user?.user_id` 作为 deps，否则会导致程序崩溃（无限重新渲染）。

### 4.3 远程桌面协同管线 (WebRTC DataChannel 管线)
现在所有设备类型 (Host Desktop / Linux QEMU / Android Scrcpy) 全面归口向统一 WebRTC：
* WebRTC 信令交互全部基于**唯一长连接**。发送 offer / answer 都在 AppBridge 与 CloudBridge 中转，以此杜绝曾因 HTTP 并发发送导致的网络时序竞态条件（错序崩溃）。
* 视频质量使用了苹果原生 `VideoToolbox CGEvent`、带宽通过 `video_qos` 根据延迟 `[100ms - 300ms]` 自动伸放码率来确保丝滑。
* 设备的触控和键位被前端抽取在 `RemoteConsole / VirtualKeyboard` (虚拟苹果风键盘，完美对应各种功能键)，透过 `DataChannel` 发往后端。

### 4.4 Agent 工作引擎全链路
用户发出消息后：
1. **持久化并发送**：网关写库 `chat_messages`。
2. **Watchdog 轮询捕获**：Runtime 项目中的 Watchdog 检测到未处理的 Sending 消息，分配对应 Saga 触发 Agent 工作流 (`Runtime Orchestrator`) 构建独立的运行沙箱（Runtime_X）。
3. **ReactThink**：通过调用 `LLM Factory` 思考。
4. **ReactActions**：通过挂载于这台设备的 `Tools Server` 解析该 Agent 有权使用的工具并发出真实的请求执行；并把结果填回。
5. **结束判断与清理**：一旦不包含 `tool_call` 或者达到轮询边界，打入 completed 并触发完成。

---

## 五、 问题避坑与技术债

### 已知待办 (TODO)
* [ ] **原生视频渲染层 (WebRTC Native Render)**：计划将 iOS/macOS 移动端的 WebRTC `video` 标签直接替换为 `CAMetalLayer` 原生贴片透明渲染层，降低手机硬件发热及解码功耗。
* [ ] **技能集联通商店 (ClawHub)**：待补齐 `skill` 和中央市场 ClawHub 之间的双向浏览与安装功能。
* [ ] **Gateway DB Async 化**：网关中 SQLite 仍然有很多同步直达调用，在异步极高的 FastAPI 中长时间阻塞会有性能瓶颈需要后续换 Async Drivers。
* [ ] **Watchdog 聚合创建优化**：当离线定时任务被过期触发时（比如 System Wake 风暴），Watchdog 可能瞬间创建大量的 Message Process 导致处理重复运行，需要合并为一个 Subagent Saga 处理锁。
* [ ] **iOS 真机键盘高度偏移**：已使用 `main.mm` 对键盘做高度注入以避让安全区，但由于 React `LayoutContainer` 渲染时序，可能在非常用输入法切换时框体会短暂遮挡或偏下。

### 疑难解答与排坑
| 异常表征 | 可能原因与解决方案 |
|---|---|
| `./deploy ios` 失败 (aws-lc-sys 报错) | Xcode 26.x BETA 版更改了 `macOS SDK` 的签名，这破坏了 rust 依赖 `aws-lc-sys` 的交叉编译预期，降级到正式版 Xcode 15 即可，或尝试配置 CFLAGS 为真机目录。 |
| LLM 一直想事情但是总是超时，也不回复 | 检查 API 限流（特别是 429 报错），可通过查阅 `task-worker-*.log` 获取到具体的 `tool_call` 被中断的原因；不要过度依赖 Context 全表。|
| Gateway 完全无响应或者启动不了 | 有强可能为前一次强杀的时候没有关闭 `SQLite` 连接。恢复需清除脏写入（`rm -f /opt/novaic/data/gateway.db-wal` 然后完全重启进程组）。|
| P2P WebRTC 链接不上但是日志显示正常 | Relay (Turn Server) 长时间不断跑会引发僵尸会话池满了，如果重启两端程序不能解决连接问题，需要在 `47.xxx` 的机器上 `systemctl restart novaic-quic-service` 刷新一下打孔端口池。|

---
**本文档由最新演进状态重构而来。**
