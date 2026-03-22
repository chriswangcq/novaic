# NovAIC 项目交接文档 (2026 全面重构版)

> 最后更新时间：2026-03-22
> **文档说明**：本文档由原先近 3000 行变更日志进行结构化重构而来。以模块和功能为维度，完整提取了历史技术方案、避坑指南、调试指令以及排查记录等核心信息，旨在为接手者提供全链路的上下文。

---

## 目录
1. [快速上手](#一-快速上手)
2. [项目整体架构纲要](#二-项目整体架构纲要)
3. [仓库结构与代码管理](#三-仓库结构与代码管理)
4. [本地开发与客户端构建指南](#四-本地开发与客户端构建指南)
5. [云端微服务部署与服务器运维](#五-云端微服务部署与服务器运维)
6. [六大核心架构细节](#六-六大核心架构细节)
    - 6.1 [认证体系与多租户权限隔离](#61-认证体系与多租户权限隔离)
    - 6.2 [WebRTC 统一远程桌面防卡顿管线](#62-webrtc-统一远程桌面防卡顿管线)
    - 6.3 [实时 WebSocket Push 与配置同步](#63-实时-websocket-push-与配置同步)
    - 6.4 [前端业务流转与 SWR 更新架构](#64-前端业务流转与-swr-更新架构)
    - 6.5 [Agent Runtime 后端回路与工具代理](#65-agent-runtime-后端回路与工具代理)
    - 6.6 [大语言模型 Gateway - LLM Factory](#66-大语言模型-gateway---llm-factory)
7. [历史暗坑与排障速查大全 (Troubleshooting)](#七-历史暗坑与排障速查大全-troubleshooting)
8. [技术债与待办重点](#八-技术债与待办重点)

---

## 一、 快速上手

| 需求场景 | 执行指令 |
|---|---|
| **本地 UI 开发** | `cd novaic-app && npm install && npm run dev` |
| **本地 Rust 调试** | `cd novaic-app && npm run tauri:dev` |
| **构建桌面发行版** | `./deploy desktop` (等价 `npm run tauri:build -- --bundles app`)|
| **构建安装 iOS** | `./deploy ios` (需要 USB 连接授信 iPhone 真机)|
| **应用前端 OTA 发布** | `./deploy frontend [version]` (编译 + 同步到 Relay CDN)|
| **热更并重启 Gateway** | `./deploy gateway` |
| **一键全量服务发版** | `./deploy services` |
| **P2P Relay 部署** | `./deploy relay` |
| **查在线服务状态** | `./deploy status` |
| **看指定服务日志** | `./deploy logs [gateway\|orchestrator\|tools\|runtime\|worker\|relay]`|
| **清空手机/电脑缓存** | Frontend Settings → Clear Cache → 刷新页面 |

---

## 二、 项目整体架构纲要

NovAIC 目前采用 **OTA-First 薄壳客户端 + 边缘中继协同** 的体系：

1. **OTA 极简直出版 (24KB)**：客户端安装包已移除巨量资源，App 启动后访问 Relay CDN 获取最新包直接跳传 (Navigate)，修 Bug 可做到秒级发版覆盖 iOS/Android/macOS。内置的 Tauri 功能则通过 Rust 暴露 Native 接口（如原生键鼠操控、底层 IndexedDB SQLite 同级操作）。
2. **纯 WebRTC 穿透链路**：废弃了所有过往基于 H5 Canvas / NoVNC 的画面投射，统一切换至基于 H.264 的 VideoToolbox 硬编与 WebRTC DataChannel 并发传输，彻底解决网络重传慢、编码占 CPU 发热大以及坐标投射失真问题。
3. **消除 SSE 与 HTTP 极简流操作**：移除了所有的 RESTful SSE 推送通道，所有前端实时事件走 `AppBridge WS` 全量信令与 payload 推送通道。

```text
[ 用户端设备 ] 
 ├── Web Frontend (React/Vite)
 │   ├── UI/交互 (Tailwind + Zustand)
 │   ├── IndexedDB 实体缓存 (通过 Tauri SqlDB)
 │   ├── Push Manager (监听 Gateway 下发的 gateway_push，触发重新拉取)
 │   └── DeviceConsole / Webrtc View (负责H264视频解码与输入劫持反馈)
 │
 └── Rust Tauri 后台 (VmControl)
     ├── WebRTC Engine (macOS VideoToolbox GPU硬编 / FFmpeg 软编)
     ├── 键盘鼠标注入器 (全平台兼容：macOS CGEvent API 规避主线程崩溃)
     └── Android Scrcpy Bridge / QEMU vnc_proxy
      
[ 云端总线 api.gradievo.com ]
 └── Nginx
     └── FastAPI Gateway (19999)    ←  维护全局数据库、路由权限过滤(`X-User-ID`)
         ├── WebSocket CloudBridge  ←  连接到客户端的 VmControl 获取画面通道、推设备列表
         └── SQLite                 ←  保存 Config，Devices, agents

[ 云端 AI 控制回路 ]
 ├── LLM Factory (19990)            ←  唯一的对外网络，收纳所有 API_KEY 解密调用
 ├── Runtime Orchestrator           ←  存储执行的完整状态 JSON Context
 ├── Queue Service                  ←  分发 Message Processing Saga
 └── Tools Server                   ←  Docker 环境或连入的手机 / VM 内下发系统 Shell 操作指令

[ 穿透与 OTA 节点 relay.gradievo.com ]
 └── Rust STUN (3478 UDP) + HTTPS Relay (443 QUIC) + OTA 前端分发 Nginx
```

---

## 三、 仓库结构与代码管理

根仓库为 `chriswangcq/novaic` (默认 `main` 分支)，内部由 13 个 Git **Submodule** 组合运转：
`git clone --recurse-submodules git@github.com:chriswangcq/novaic.git`

| Submodule | 用途描述 |
|---|---|
| `novaic-app` | Tauri 桌面+移动端薄壳应用前端代码及本地 Rust 伴随进程 |
| `novaic-gateway` | 云端统一前端网关入口，提供 Auth、推送、代理桥接 |
| `novaic-llm-factory` | 后置 LLM 的管理收口微服务 |
| `novaic-quic-service` | STUN/Relay 服务实现以及静态文件的存储节点 |
| `novaic-agent-runtime` | Task Saga、Watchdog 的任务编排后端 |
| `novaic-runtime-orchestrator` | 上下文与生命周期追踪编排器 |
| `novaic-tools-server` | Agent 可以使用的指令执行节点 |
| `novaic-mcp-vmuse` | 提供 VM 使用相关 MCP Server |
| `novaic-storage-*` | 文件 / 附件图库存储集群 |
| `基础协议库` | `kernel` / `contracts` / `shared-runtime-common` 公共类库 |

---

## 四、 本地开发与客户端构建指南

### 4.1 桌面端编译规范
执行 `npm run tauri:build -- --bundles app`（**切勿**在使用 `--ci`，脚本会自动 `env -u CI`以防在工作流意外）。
`macOS` 发行版中若涉及 QEMU 内置镜像自动下载等功能，构建产物将被输出至 `src-tauri/target/release/bundle/macos/NovAIC.app`。

### 4.2 iOS 移动端编译与签下坑点
**完整构建命令：**
```bash
cd novaic-app && ./scripts/build-and-install-ios.sh
```
这个脚本自动化了如下手动流程：
1. 若 `gen/apple` 不存在，使用 `tauri ios init` 创建模板 （需要配置 `tauri.ios.conf.json` 开发 Team）。
2. 调用 `scripts/patch-ios-xcode.sh` 修复原工程存在的一系列变数环境（特别是移除 FORCE_COLOR 防止被识别成错误的体系结构 Arch 配置！）。
3. 调用 Xcode 工具链进行 Debug 签名。
4. 调用 `devicectl device install app` 走局域网或者真实 USB 部署到手机。

**iOS 历史大坑必须知晓：**
1. **不要用 `tauri ios run` ！！！**：它的 `-exportOptionsPlist` 使用存在硬伤传递相对路径，会导致 `Couldn't load The file ".tmpXXXX" couldn't be opened` 的长历史 Bug。使用 `build-and-install-ios` 规避。
2. iOS Xcode 26.3 SDK (iOS15.7 底包) 针对 `aws-lc-sys` 的编译可能会因缺少特定 macOS 头而报错 `using sysroot for 'iPhoneOS' but targeting 'MacOSX'`。需要在 `run-ios-xcode-script.sh` 手动注入 `CFLAGS_aarch64_apple_darwin="-isysroot $(xcrun --sdk macosx --show-sdk-path)"` 作为预补救。
3. **黑屏问题（ WKWebView 限制）**：iOS 决不能使用 `custom-protocol`。构建 Features 必须用 `--no-default-features --features mobile`。由于屏蔽了 `custom-protocol`，一旦 `VITE_GATEWAY_URL` 缺失会导致闪退，故已设置硬编码保底。

### 4.3 其它端
* Android 端需具有完好 NDK 的 Android Studio 前置。通过 `tauri:build:android` 打包，支持 `custom-protocol`。

---

## 五、 云端微服务部署与服务器运维

所有发版完全依托基于 rsync 实现的代码增量 `./deploy` 工具。它只更新文件，由服务器远端的 `start.sh` 执行启停工作。
> 🚨 **绝对禁止执行 `restart_gw.sh` 对网关单独重启，这会造成 WebRTC 及进程内推送队列丢失并长期宕机挂死。无论改什么后端文件，一律以 `/opt/novaic/start.sh --stop && start.sh` 完整重启生态组为标准。**

### 5.1 Relay / STUN / OTA 节点运维 (relay.gradievo.com)
Relay 目前独立承载跨设备不能直连时的 `QUIC兜底`，以及前端动态切换的 CDN源，运维端口 `SSH: 52222`。
* 前端打包命令 `VITE_BASE="/resource/frontend/v0.3.0/" npm run build`。
* 前端会随 `./deploy frontend` 进入该服务器 `/opt/novaic/static/v0.3.0/` 中。
* 要更换全局版本号，修改 Gateway 配置 `/opt/novaic/jwt_secret.env` 中的 `FRONTEND_CDN_URL` 的路径即可。
* **长时间黑屏/UDP枯竭**：若 `coturn` 服务器运行超 6 天可能积累过多无意义丢包 zombie session，`./deploy relay` 会拉代码并触发 systemctl 释放所有连接复原服务。

### 5.2 数据库维护与清理操作 (api.gradievo.com)
长时间运行之后 SQLite 的事务 WAL 会导致磁盘剧增（Orchestrator和 Queue），必须定期用如下命令减负（支持无锁情况热执行）：
```bash
# 1. 回收队列脏任务
sqlite3 /opt/novaic/data/queue.db "DELETE FROM tq_tasks WHERE status IN ('done','failed'); DELETE FROM tq_sagas WHERE status!='active'; VACUUM;"
# 2. 清理 Orchestrator 中的巨大的上下文存储
sqlite3 /opt/novaic/data/runtime_orchestrator.db "UPDATE agent_runtimes SET context='[]' WHERE status='completed'; VACUUM;"
# 3. 删除堆积 Log 文本
find /opt/novaic/data/logs/ -name '*.log' -mtime +7 -delete 
find /opt/novaic/data/logs/ -name '*.log' -size +50M -exec truncate -s 10M {} \;
```
*(操作完建议通过 deploy orchestrator 释放一轮内存即可。)*

> 🚨 **安全警告：运行时执行 PRAGMA wal_checkpoint(TRUNCATE)**
绝对不允许在 Gateway 活动时用 `sqlite3 ... "PRAGMA wal_checkpoint(TRUNCATE)"` 强断数据库 WAL 后缀，可能会斩断进程中还未 Flush 的完整聊天写入事件，造成永久掉表！！若要移动 DB 请标准走 `BEGIN...COMMIT` 软拷贝。

---

## 六、 六大核心架构细节

### 6.1 认证体系与多租户权限隔离
* **令牌颁放**：用户获取的是有效时间 60 分钟且轮替可刷新的自定义域 `HS256 JWT`。前端自行倒计在临期小于 5 分钟请求 `/auth/refresh`。
* **Rust Context 交互**：Tauri Rust 层因需和 Gateway 建立长连接，前端会在登录态变化时调用 `invoke(update_cloud_token)` 推送令牌，存储进入 `Arc<RwLock>` 中给所有出向 WebSocket 的 `Authorization Header` 携带上。
* **Nginx 无信任接管**：Nginx 配置了对于 `/api/**` 全域开启 `auth_request -> /internal/auth/validate`。一旦解析正确，将会获得 uuid 并设置请求头 `proxy_set_header X-User-ID "$sub"`；如果是用户刻意构造的 `X-User-ID` 进包头，Nginx 会把它强制置空。
*  Gateway 下所有的 Router 读取用户身份全从请求依赖 `Dependency(get_current_user)` 读取这个头，杜绝了后端对复杂 Token的逆运算，所有的 Repository CRUD 无论什么情况，默认携带 `WHERE user_id = ?`。

### 6.2 WebRTC 统一远程桌面防卡顿管线
> 该架构已被完整重写，之前用于连接 Linux 的 vnc_proxy/QEMU、控制安卓的 scrcpy IPC 被统一合并。前端一律不需要感知背后是啥物理连接，只要发起 `useWebRtc (device.id)`。云端的 `CloudBridge` 会通过在设备列表中的注册判定派发向谁进行渲染。
1. WebRTC **信令与ICE 全部从 HTTP 迁移到 WS** 内部通信（也就是现在的 WS Push 同道），前后序完美保证了 Answer 的投递百分之百在 Candidates 之前，杜绝连接中途中断重连异常。
2. **TURN 密码凭证由 Gateway 下发代理**：过去一直困扰的广域网无法分配 Turn Credential 的问题被修复为由 Gateway 内核统一使用 HMAC 生成 `webrtc_offer` 中的 `ice_servers` 进行注入。前端直接解析即可打洞。
3. **帧传输的彻底优化**：
    * 剥离了过去的固定时间流逝和重构积压引发的“视频出现超级慢放问题”（Anti-slowmo）。`Subscriber_pump` 使用真实物理流失时钟，遇阻主动 `drain` 抛弃多余非 I 帧追赶直播时间戳。
    * VNC / 手机切屏后解码器冰冻，已经加入了屏幕可见度的 React 监听恢复，切屏自动 `POST key_frame`。
4. **macOS 极低CPU发热硬编码改造**：通过接入 VideoToolbox 的 `DataRateLimits` 接口进行 CBR 强制预估分配。在源端使用 `CGEvent` 取代 `enigo`（后者会在 tokio 异步中触发 macOS 主线程校验保护机制然后使得原生系统 `SIGTRAP` 奔溃退出桌面 App）。

### 6.3 实时 WebSocket Push 与配置同步
本系统原本含有多个依赖于 `HTTP SSE (Server-Sent Event)` 流来检测新消息和更新配置的长连接节点。在最新版本重构中所有被命名为 SSE 的类名与业务已全量废标，统称为 **PushManager**。
1. Frontend 发起的唯一长链接将接管来自后备的各类型投递，包括事件 `chat_message`，`logs_updated`。
2. **多端互斥配置**：若端 A 修改配置，会在后端触发向全域在线且同 ID 用户终端推送 `config_updated` 事件，客户端通过去抖计时器延迟重新加载 `reLoadConfig` 达到无刷新修改。（由于大模型选取存在这种场景，此法有效修复了不同步导致保存了配置读取仍为空的问题）。
3. 当客户端与终端主动需要断连重置，只发停止心跳与移除监听而不断开通道复用。

### 6.4 前端业务流转与 SWR 更新架构
* 系统分为三级设计：`视图 (Components)` ← `业务层 (useXYZ hook / Zustands)` ← `本地数据库 DB (IndexedDB)`。
* 当打开或者选取 Agent Tab 或者加载某页，立刻呈现 `IndexedDB` 给入的数据。在此之下发送异步网关请求核对是否有改动，若有改动重新覆盖 IndexedDB 并利用注册的 Observer 通知 UI 隐匿重刷。（Stale-While-Revalidate）。
* **UI组件排布约束**：不采用 `window_resize` 做绝对值判断，全部采用 Flex。历史的 `opacity-0` 逻辑与 `visibilitychange` 多端冲突引发的窗口看不到文字但可以选择复制的历史 Bug，已被替换为用父级 `min-h-0` + Flex 的约束完美兼容全设备。

### 6.5 Agent Runtime 后端回路与工具代理
核心运行流通过事件图 `Sagas` 状态机接管：
1. Agent Message 压入 -> Watchdog 检测。
2. *(历史大坑)*：Watchdog 会因为调度死锁堆满从而在一秒内开启百个线程为同意 Agent 创建不同 Runtime 互斥覆盖。现已改进为批量拿消息且在分组层面 `Per-Agent` 限流重试机制。
3. 唤醒 `ReactThink` (向大模型交涉) 发现要执行工具，切换 `ReactActions` 抛向下属。
4. 对于比如涉及到操作桌面的本地请求，ToolsServer 会直接发起 `/internal/agents/{agent_id}/vm/shell/command` 给 Gateway，网关找到该代理绑定的设备归属设备，并往 `CloudBridge WebSocket` 直接向桌面端 Rust 后台内的 `VMuse` 微型 Python 虚拟环境打过去真实的运行反馈。

### 6.6 大语言模型 Gateway - LLM Factory
已完成集中化架构迁移：
* 把任何向外部供应商（OpeAI, Kimi）发起的调用封装到 `newapi.gradievo.com` 的 LLM-Factory。
* 所有服务的原始 LLM 配置数据在 DB 被切断成 `composite_id (api_key_id:model_id)`。调取链路从提取密码变为主程只要告诉 Factory `user_id` 和请求参数，Factory 再从独立 SQLite 里解出对称密钥发出请求，大幅提高了系统对 Key 的安全度以及日志集中排查体验。

---

## 七、 历史暗坑与排障速查大全 (Troubleshooting)

若运行开发或线上排查遇到各类莫名失效，请首选参考此处前人走通的死胡同记录：

| 故障现象表征 | 深度根因解禁与快速恢复办法 |
|---|---|
| **macOS 上报 "Tokio runtime SIGTRAP 崩溃"** | Rust 库包 `enigo::key()` 和 `arboard` 去操作系统的原生态度必须严格使用苹果主队列（Dispatch Mian Queue），跨出事件会遭遇系统直接捕杀进程。全链路已经替换为具有纯无锁队列事件转发能力的苹果原声 `CGEvent` 组件。不要动那个地方了。 |
| **设备列表页在操作时 UI 直接完全死锁卡住** | `auth.ts` 暴露给出的 `getCachedUser()` 函数如果被带在 `useEffect` 的 Deps 中，因为它的对象实现是每次新建一份不同的 Object 变量！这将致使 React Diff 爆炸死锁！解法：依赖项改为具体的单纯标量 (如 `getCachedUser()?.user_id`)。 |
| **LLM 想一想抛 429 和超时 Failed** | 绝大多数非本地出错，都是外部模型商动态过载或单机 Rate Limit 被干爆。排查方式是拿到 `task-worker-*.log` 找 task_id，取 JSON 数据直接在 factory 反向验证一下。通常直接给请求层再包一层被动回退重试策略即可。 |
| **截图服务失效：命令好使，截完是黑屏或错的** | 由于新加入的多账号系统 `subusers`，截屏需要挂载独立的桌面指针 `DISPLAY`。目前的解法是在 `build_runtime_context` 时区分 `main_user(:10)` 外为不同 user 注入 `:{display_num}` 并带进 VMuse 内让 Scort 等截图程序指向正确对象即可。目前系统已全自动下推。 |
| **`npm run tauri:dev` 提示 1420 冲突** | Vite 进程没关干净。暴力清理：`kill $(lsof -ti:1420)`。|
| **找不到 Gateway 连接（各种 500 / CORS 满天飞）** | Rust 中的 HTTP/WS 均默认不走用户态的代理。有时候本地有工具拦截或者强制走了 Global Proxy 会把请求直接丢错，注意看是否有无正确带上 `no_proxy`。以及 JWT_SECRET 在重启时是否因为未在 env 而未读到。|
| **iOS / Mac 使用过程中软键盘虚拟键按下没有作用** | 防止出现和真机系统抢劫行为，`VirtualKeyboard` 使用的是 Toggle Mode 处理组合。比如点击一下了 `Shift` 如果高亮会驻留一次输入动作并在敲回退或其他下个按键释放，千万别一直按着长按。 |

---

## 八、 技术债与待办重点

下面是遗留待处理的任务积压池（近期被提出未进行清理或闭环的任务）：

1. **[基础能力] iOS 键盘输入框上顶错位**：原生端针对高度 `--keyboard-height` 的计算回调由于生命周期的变动极易出现失效导致消息框底被盖着，亟待真机联调深度重算 React Hook 同步时机。
2. **[生命管理] 服务端海量 Context 僵尸存储定时清零**：目前的 DB 清理依靠手动进入 Gateway 的 SQLite 删除或者 `./deploy cleanup`。需要加入系统原生 `complete_runtime` 函数内对不涉及以后学习的长时 Context 做截肢。
3. **[重要管控] Watchdog v2 的正式版上线**：已经做好的文档规划（使用 Per-Agent 的排队而不是消息循环 Saga）未最终闭环。防高并发崩溃需要落实。
4. **[原生体验] 视频的原生 Layer**：前端渲染视频的延时终极瓶颈为 Web 渲染和解码消耗。把 Tauri 窗口贴附并叠加底层的原生播放器 `CAMetalLayer/VideoCodec GL`，做到硬解析硬出屏这块要尽快排期以彻底榨干多端兼容红利。
5. **[用户侧体验] 联机能力与 ClawHub 双切**：需联通主服 API 将商店内置能力与用户选择模块激活能力打通，支持按需使用插件扩充能力。
6. **[性能隐患] Gateway FastAPI 内部的同步 Block 函数消除**：一些读字典或者简单直达表还在直接依赖未经过 Async 封皮的读取，在高负荷高轮询很容易使主线程 IO 卡死变慢。

---
📝 *文档致敬所有前人熬夜填过的暗坑！祝下一个接手系统的协作者武运昌隆。*
