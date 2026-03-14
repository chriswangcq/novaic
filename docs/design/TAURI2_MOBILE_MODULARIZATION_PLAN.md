# Tauri 2 移动端模块化计划

> 目标：在现有 Tauri 2 桌面应用基础上，支持 Android + iOS，通过 feature flags 和条件编译实现单一代码库、多平台构建。  
> 排除：VMControl、P2P、VNC 等桌面专属模块。

**版本策略**：仅兼容 2020 年及之后的移动操作系统版本（iOS 14+、Android 11 / API 30+），可放弃对更早系统的支持以简化实现。

---

## 架构评审摘要（2025-03）

五位架构师从模块结构、安全、DevOps、平台兼容、可维护性角度审阅后，已采纳以下关键意见并融入本文档：

| 来源 | 采纳意见 |
|------|----------|
| 模块结构 | 推荐 target 条件依赖；补齐 split_runtime、cloud_connection、http_client 归属；修正 FileOps 条件编译写法 |
| 安全 | 新增「凭证与认证」小节；移动端需 SecureStorage；get_api_key 已删除（设备 api_key 仅 vmcontrol 使用） |
| DevOps | 构建命令需 `--` 传递 Cargo 参数；移动端 resources 须显式列出保留项；补充 npm 脚本与 CI 策略 |
| 平台 | 使用 @tauri-apps/plugin-os 做平台检测；open_file 移动端需 Kotlin/Swift 插件，shell.open() 不可靠 |
| 可维护 | 推荐单 main.rs + #[cfg]；增加 core::bootstrap::init()；补充测试策略与 feature 互斥编译断言 |

---

## 一、总体架构

```
novaic-app/
├── src/                          # 前端（共享，需平台检测）
├── src-tauri/
│   ├── src/
│   │   ├── main.rs              # 单一入口，setup 内 #[cfg] 分支 desktop/mobile
│   │   ├── mobile.rs            # 移动端 setup：调用 setup::setup_shared，默认云端 Gateway
│   │   ├── setup.rs             # 共享 setup：Gateway URL、StorageBackend、VncProxy 统一注入
│   │   │
│   │   ├── core/                # 跨平台共享（无 Tauri 依赖）
│   │   │   ├── mod.rs
│   │   │   ├── bootstrap.rs     # init: rustls, panic hook, tracing
│   │   │   ├── gateway_client.rs
│   │   │   ├── sse_stream.rs
│   │   │   ├── config.rs        # 仅常量/结构体；VM 常量 → desktop
│   │   │   └── error.rs
│   │   │
│   │   ├── commands/            # Tauri 命令（共享，无 desktop 子模块）
│   │   │   ├── mod.rs
│   │   │   ├── gateway.rs       # gateway_*, fetch_authenticated_bytes
│   │   │   ├── auth.rs          # update_cloud_token
│   │   │   ├── config.rs        # get/set gateway_url
│   │   │   ├── file.rs          # open_file, show_in_folder, download_file_to_cache
│   │   │   ├── secure_storage.rs
│   │   │   └── vnc_urls.rs      # get_vnc_proxy_url, get_scrcpy_proxy_url（get_vmcontrol_url 已删除）
│   │   │
│   │   ├── platform/            # 平台抽象
│   │   │   ├── mod.rs
│   │   │   ├── storage.rs       # trait StorageBackend
│   │   │   └── file_ops.rs     # trait FileOps
│   │   │
│   │   └── vnc_proxy.rs         # 桌面+移动端：P2P 连接 VNC/Scrcpy（顶层 mod）
│   │
│   ├── vmcontrol/               # 仅桌面 target
│   ├── p2p/                     # 桌面+移动端（VncProxy 需 P2P）
│   ├── Cargo.toml
│   ├── tauri.conf.json          # 基础配置
│   ├── tauri.ios.conf.json      # iOS 覆盖
│   └── tauri.android.conf.json  # Android 覆盖
```

---

## 二、Cargo.toml 模块化

### 2.1 Feature Flags

```toml
[features]
default = ["desktop"]
# 桌面专属：VM、P2P、VNC、托盘、进程管理
desktop = [
    "vmcontrol",
    "p2p",
    "axum",
    "quinn",
    "tokio-tungstenite",
    "tauri/tray-icon",
    "tauri/devtools",
    "tauri-plugin-process",
]
# 移动端：无 VM、无托盘
mobile = []
# 自定义协议（桌面打包用）
custom-protocol = ["tauri/custom-protocol"]
```

### 2.2 条件依赖

```toml
[dependencies]
# Tauri：基础能力全平台，tray-icon/devtools 仅桌面
tauri = { version = "2", default-features = false, features = ["shell", "dialog", "fs"] }
# 在 [features] 中通过 desktop 启用 tray-icon, devtools

vmcontrol = { path = "vmcontrol", optional = true }
p2p = { path = "p2p", optional = true }
axum = { version = "0.7", optional = true, features = ["ws"] }
quinn = { version = "0.11", optional = true, features = ["rustls"] }
tokio-tungstenite = { version = "0.24", optional = true }
tauri-plugin-process = { version = "2", optional = true }

# 共享依赖（所有平台）
reqwest = { version = "0.11", default-features = false, features = ["json", "multipart", "stream", "rustls-tls"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.35", features = ["full"] }
# ...
```

### 2.3 推荐：target 条件依赖

**优先采用 target 条件依赖**，在编译 Android/iOS 时自动排除桌面库，无需传 `--no-default-features`，减少人为错误：

```toml
[target.'cfg(not(any(target_os = "android", target_os = "ios")))'.dependencies]
vmcontrol = { path = "vmcontrol" }
p2p = { path = "p2p" }
axum = { version = "0.7", features = ["ws"] }
quinn = { version = "0.11", features = ["rustls"] }
tokio-tungstenite = { version = "0.24", default-features = false, features = ["rustls-tls-native-roots"] }
```

feature flags 保留用于可选能力（如 `custom-protocol`、`devtools`），`desktop` 与 `mobile` 互斥，建议在 `main.rs` 顶部增加编译断言：

```rust
#[cfg(all(feature = "desktop", feature = "mobile"))]
compile_error!("Cannot enable both 'desktop' and 'mobile' features");
```

### 2.4 移动端依赖差异

| 依赖 | 桌面 | 移动 |
|------|------|------|
| `tauri/tray-icon` | ✅ | ❌ |
| `tauri/devtools` | ✅ | ❌（可保留用于调试） |
| `tauri-plugin-process` | ✅ | ❌ |
| `tauri-plugin-shell` | ✅ | ✅（部分能力） |
| `tauri-plugin-dialog` | ✅ | ✅ |
| `tauri-plugin-fs` | ✅ | ✅ |
| `reqwest/blocking` | ✅（VM 停止用） | ❌ |
| `dirs` | ✅ | ⚠️ 移动端用 `tauri::path` |
| `vmcontrol` | ✅ | ❌ |
| `p2p` | ✅ | ✅（VncProxy P2P 连接远端） |
| `axum` | ✅ | ✅（VncProxy WebSocket 服务） |
| `quinn` | ✅ | ✅（VncProxy QUIC 隧道） |

### 2.5 现有模块归属清单

**未来扩展**：若增加 Web 等第三平台，可新增 `web` feature，在 main 中加 `#[cfg(feature = "web")] web::run()` 分支；命令注册与平台抽象可扩展对应实现。

**vmcontrol 生态**：环境检查、镜像下载、部署（check_environment、check_cloud_image、download_cloud_image、deploy_agent）属于 vmcontrol 能力范畴；Tauri 侧 `vm/` 是 vmcontrol 的客户端桥接层，通过 Gateway 与 vmcontrol 交互。

| 模块 | 用途 | 归属 |
|------|------|------|
| `vm/` | 已删除 | 环境检查/镜像/部署已迁入 vmcontrol vm_prep，前端走 Gateway |
| `gateway_base_url` | 已迁入 core::config | core |
| `cloud_connection.rs` | 已删除 | Cloud Bridge 已合并进 vmcontrol |
| `vnc_proxy.rs` | P2P 连接 VNC/Scrcpy | 桌面+移动端（移动端仅远端路径） |
| `http_client.rs` | `local_client()` 用于 VM 通信 | desktop |
| `app_config.rs` | 已删除 | - |
| `commands/file_commands.rs` | 已删除 | - |

---

## 三、主入口与 mobile.rs

### 3.1 当前实现：单一 main.rs + mobile.rs

采用**单一 `main.rs`**，在 `setup` 闭包内用 `#[cfg]` 分支选择桌面或移动端逻辑。**无需 lib.rs**：core/、platform/、commands/ 已充分模块化，可测逻辑在 `*_impl` 中，无需 lib 抽取。

```rust
// src/main.rs
fn main() {
    core::bootstrap::init();  // rustls + panic hook + tracing + NO_PROXY

    tauri::Builder::default()
        .setup(|app| {
            #[cfg(any(target_os = "android", target_os = "ios"))]
            return mobile::setup(app);

            #[cfg(not(any(target_os = "android", target_os = "ios")))]
            { /* 桌面：Tray、VmControl、VncProxy、PID 等 */ }
        })
        .invoke_handler(tauri::generate_handler![...])
        .run(...);
}
```

### 3.2 mobile.rs 职责

`mobile.rs` 是**移动端 (Android/iOS) 的 setup 逻辑**，当 `target_os` 为 android 或 ios 时，`main.rs` 的 setup 直接 `return mobile::setup(app)`，跳过桌面逻辑。

| 项目 | 桌面 setup | mobile::setup |
|------|------------|---------------|
| Gateway URL | 统一云端默认 `setup::DEFAULT_GATEWAY_URL` | 同上 |
| Tray 托盘 | ✓ | ✗ |
| PID 文件 | ✓ | ✗ |
| VmControl | ✓ 嵌入式 | ✗ |
| VncProxy | ✓ 统一 `setup::setup_shared` 注入 | ✓ |
| StorageBackend | ✓ 统一 `setup::setup_shared` | ✓ |
| 共享状态 | gw_url, cloud_token, login_notify, vnc_proxy, ... | 同上（精简版） |

移动端无本地 VM，VncProxy 仅用于连接远端设备的 VNC/Scrcpy（通过 Gateway locate + QUIC P2P）。

### 3.3 setup.rs 统一共享状态

Gateway URL、StorageBackend、VncProxy 等**统一由 `setup::setup_shared` 注入**：

- **DEFAULT_GATEWAY_URL**：`https://api.gradievo.com`，桌面+移动端统一用云端
- **load_gateway_url(data_dir)**：从 gateway_url.txt 读取，空则用 DEFAULT_GATEWAY_URL
- **setup_shared(app, data_dir)**：创建并 manage gw_url、api_key、cloud_token、login_notify、storage_backend、vnc_proxy_state

VncProxy 打洞逻辑统一：本地用 connect_to_peer，远端用 punch_and_connect，均走 p2p::tunnel。

### 3.4 lib.rs 不需要

原计划的 lib.rs + main_desktop/main_mobile 拆分**已放弃**，原因：

- 可测逻辑已在 core/、commands/*_impl 中，不依赖 Tauri 运行时
- 单 main.rs + mobile.rs + setup.rs 已清晰分离
- 抽取 lib 需改 Cargo 构建（[[bin]]、[lib]），收益有限

---

## 四、命令注册矩阵

| 命令 | 桌面 | 移动 |
|------|------|------|
| **Gateway** | | |
| `gateway_get/post/patch/put/delete` | ✅ | ✅ |
| `gateway_health` | ✅ | ✅ |
| `gateway_sse_connect/disconnect` | ✅ | ✅ |
| **Auth** | | |
| `update_cloud_token` | ✅ | ✅ |
| ~~get_api_key~~ | 已删除 | 设备 api_key 仅 vmcontrol 从 env 读取 |
| **Config** | | |
| `get_gateway_url` | ✅ | ✅ |
| `set_gateway_url` | ✅ | ✅ |
| `get_gateway_status` | ✅ | ✅ |
| **File** | | |
| `fetch_authenticated_bytes` | ✅ | ✅ |
| `download_file_to_cache` | ✅ | ✅ |
| `open_file` | ✅ | ✅（需平台实现） |
| `show_in_folder` | ✅ | ⚠️ 移动端可弱化 |
| **VM（仅桌面）** | | |
| `check_environment` | ✅ | ❌ |
| `check_cloud_image` | ✅ | ❌ |
| `download_cloud_image` | ✅ | ❌ |
| `deploy_agent` | ✅ | ❌ |
| ~~get_vmcontrol_url~~ | 已删除 | 前端改用 get_vnc_proxy_url / get_scrcpy_proxy_url |
| `get_vnc_proxy_url` | ✅ | ✅ |
| `get_scrcpy_proxy_url` | ✅ | ✅ |
| **P2P（已删除）** | | |
| ~~`start_discovery`~~ | — | — |
| ~~`stop_discovery`~~ | — | — |
| ~~`list_discovered_devices`~~ | — | — |

### 命令注册示例

`tauri::generate_handler!` 需要静态列表，使用 `#[cfg]` 条件编译：

```rust
tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![
        gateway_get,
        gateway_post,
        gateway_patch,
        gateway_put,
        gateway_delete,
        gateway_health,
        gateway_sse_connect,
        gateway_sse_disconnect,
        update_cloud_token,
        get_gateway_url,
        set_gateway_url,
        get_gateway_status,
        fetch_authenticated_bytes,
        download_file_to_cache,
        open_file,
        show_in_folder,
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        check_environment,
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        check_cloud_image,
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        download_cloud_image,
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        deploy_agent,
        // get_vmcontrol_url 已删除
        get_vnc_proxy_url,
        get_scrcpy_proxy_url,
        // p2p_commands 已删除（start_discovery, stop_discovery, list_discovered_devices）
    ])
```

---

## 五、平台存储与路径

### 5.1 桌面 data_dir

```rust
// 当前：app.path().app_data_dir()
// 用于：api_key.txt, gateway_url.txt, app.pid, logs/
```

### 5.2 移动端

- **iOS**：`NSDocumentDirectory` 或 `NSCachesDirectory`，通过 `tauri::path::app_data_dir()` 获取
- **Android**：`getFilesDir()` / `getCacheDir()`，Tauri 提供对应 API

```rust
#[cfg(any(target_os = "android", target_os = "ios"))]
fn get_config_dir(app: &AppHandle) -> PathBuf {
    app.path().app_data_dir().unwrap_or_else(|_| PathBuf::from("."))
}
```

### 5.3 凭证与认证（安全）

| 凭证类型 | 桌面 | 移动端 | 说明 |
|----------|------|--------|------|
| **设备 api_key** | `data_dir/api_key.txt` 明文 | stub 返回空（纯云端）或 SecureStorage | 仅连本地 Gateway 时需设备级认证 |
| **用户 JWT** | localStorage + CloudTokenState | **Keychain/Keystore** + CloudTokenState | `tauri-plugin-store` 基于 SQLite，**不适合**存敏感数据 |
| **LLM API keys** | `appConfig.json` | SecureStorage 或应用沙盒 | 移动端需评估 appConfig 权限 |

**get_api_key**：已删除。设备 api_key 在启动时加载到 env，仅 vmcontrol 使用，前端无需调用。

**建议**：在 Phase 3 前完成 `platform::SecureStorage` trait 与平台实现（iOS Keychain、Android EncryptedSharedPreferences/Keystore），将 JWT、api_key 等敏感数据统一通过该抽象读写。

---

## 六、文件操作平台实现

### 6.1 open_file

| 平台 | 实现 |
|------|------|
| macOS | `open {path}` |
| Windows | `cmd /C start "" {path}` |
| Linux | `xdg-open {path}` |
| Android | `Intent.ACTION_VIEW` + FileProvider URI |
| iOS | `UIDocumentInteractionController` 或 `QLPreviewController` |

### 6.2 show_in_folder

| 平台 | 实现 |
|------|------|
| macOS | `open -R {path}` |
| Windows | `explorer /select,{path}` |
| Linux | `xdg-open {parent_dir}` |
| Android | `Intent.ACTION_VIEW` + 目录 URI |
| iOS | 可省略或使用 Share Sheet |

### 6.3 抽象与实现

`#[cfg_attr]` 不支持 `path`，应使用 `#[cfg]` 条件模块：

```rust
// platform/mod.rs
#[cfg(any(target_os = "android", target_os = "ios"))]
mod mobile;
#[cfg(not(any(target_os = "android", target_os = "ios")))]
mod desktop;

pub trait FileOps {
    fn open_file(path: &str) -> Result<(), String>;
    fn show_in_folder(path: &str) -> Result<(), String>;
}
// 各平台实现 impl FileOps for DesktopFileOps / MobileFileOps
```

**重要**：`tauri-plugin-shell` 的 `open()` 在移动端对 `file://` 支持不足，Android 上易出现 "Not allowed to open url"。**移动端 open_file 需通过 Kotlin/Swift 自定义插件**（Intent.ACTION_VIEW + FileProvider / UIDocumentInteractionController）实现。

---

## 七、Tauri 配置

### 7.1 tauri.conf.json（基础）

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "NovAIC",
  "version": "0.3.0",
  "identifier": "com.novaic.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:1420",
    "frontendDist": "../dist"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": [...]
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [...],
    "resources": {}
  }
}
```

### 7.2 tauri.ios.conf.json

```json
{
  "bundle": {
    "resources": {
      "resources/config": "config",
      "resources/backends": "backends",
      "resources/novaic-mcp-vmuse": "novaic-mcp-vmuse"
    },
    "iOS": {
      "developmentTeam": "YOUR_TEAM_ID",
      "minimumSystemVersion": "15.0"   // 2021+，满足「2020 年后」策略
    }
  },
  "app": {
    "windows": []
  }
}
```

**注意**：JSON Merge Patch 中 `"resources": {}` 会清空所有资源。必须**显式列出需保留**的项，才能排除 `qemu`、`android-sdk`、`scrcpy-server` 等 VM 相关资源。

### 7.3 tauri.android.conf.json

```json
{
  "bundle": {
    "resources": {
      "resources/config": "config",
      "resources/backends": "backends",
      "resources/novaic-mcp-vmuse": "novaic-mcp-vmuse"
    },
    "android": {
      "minSdkVersion": 30,   // API 30 = Android 11 (2020)，满足「2020 年后」策略
      "targetSdkVersion": 34
    }
  }
}
```

---

## 八、插件兼容性

| 插件 | 桌面 | Android | iOS |
|------|------|---------|-----|
| tauri-plugin-shell | ✅ | ⚠️ 部分 | ⚠️ 部分 |
| tauri-plugin-dialog | ✅ | ✅ | ✅ |
| tauri-plugin-fs | ✅ | ✅ | ✅ |
| tauri-plugin-process | ✅ | ❌ | ❌ |

移动端需确认 `shell.open()` 等是否可用；若不可用，`open_file` 需用原生实现。

---

## 九、实施阶段

### Phase 1：Cargo 模块化（1–2 天）

1. 在 `Cargo.toml` 增加 `desktop` / `mobile` features
2. 将 `vmcontrol`、`p2p`、`axum`、`quinn` 等改为 `optional`
3. 用 `#[cfg(feature = "desktop")]` 包裹 VM、P2P、VNC 相关代码
4. 验证 `cargo build --no-default-features --features desktop` 通过

### Phase 2：核心拆分（2–3 天）

1. 新建 `core/`，迁移 `gateway_client`、`sse_stream`、`config`、`error`
2. 新建 `core::bootstrap::init()`，统一 rustls、panic hook、tracing、NO_PROXY 初始化
3. 新建 `commands/`，按功能拆分命令；将命令逻辑抽成可测函数（如 `gateway_get_impl`），便于单元测试
4. 共享逻辑已在 `core/`、`commands/` 中，无需 lib.rs
5. 在 `main.rs` setup 内用 `#[cfg]` 分支：`mobile::setup(app)`（移动端）或桌面逻辑
6. **模块归属**：`split_runtime` 的 gateway 常量 → core；`agent_base_url` → desktop；`cloud_connection`、`http_client`、`vm_file_commands` → desktop

### Phase 3：移动端 setup（1–2 天）

1. 实现 `mobile::setup(app)`，在 setup 内 `#[cfg(android, ios)]` 时返回
2. 共享命令全平台注册；VM 命令 `#[cfg(desktop)]` 排除
3. 配置存储：使用 `tauri::path`，移动端默认 gateway_url 为云端
4. 无 Tray、无 PID、无 VmControl 启动

### Phase 4：文件操作（1 天）

1. 抽象 `FileOps` trait
2. **Android**：实现 Kotlin 插件，使用 `Intent.ACTION_VIEW` + FileProvider，将 `content://` 或 app 内部路径转为可分享 URI（`tauri-plugin-shell` 的 `open()` 对 `file://` 支持不足）
3. **iOS**：实现 Swift 插件，使用 `UIDocumentInteractionController` 或 `QLPreviewController`
4. `show_in_folder` 移动端可先 stub

### Phase 5：配置与构建（1 天）

1. 添加 `tauri.ios.conf.json`、`tauri.android.conf.json`
2. 移除移动端 bundle 中的 VM 资源
3. 配置 `tauri ios init`、`tauri android init`
4. 验证 `tauri ios dev`、`tauri android dev`

### Phase 6：前端适配（1–2 天）

1. **平台检测**：添加 `@tauri-apps/plugin-os`，使用 `platform()` 或 `type()` 做分支（非 `getCurrent().platform`）：
   ```ts
   import { type } from '@tauri-apps/plugin-os';
   const isMobile = () => ['ios', 'android'].includes(type());
   ```
2. 隐藏 VM/Device 相关 UI（AgentDrawer、DeviceSidebar 等）
3. 布局：移动端使用底部 Tab 或单栏
4. 安全区：`env(safe-area-inset-*)` 或 padding

---

## 十、构建命令

**重要**：Tauri CLI 不会把 `--no-default-features` 传给 Cargo，必须通过 `--` 显式传递：

```bash
# 桌面（默认）
tauri build

# 移动端（通过 -- 将参数传给 Cargo）
tauri android build -- --no-default-features --features mobile
tauri ios build -- --no-default-features --features mobile

# 开发
tauri android dev -- --no-default-features --features mobile
tauri ios dev -- --no-default-features --features mobile
```

**npm 脚本封装**（推荐，避免 CI/文档中写错）：

```json
{
  "scripts": {
    "tauri:build:desktop": "tauri build",
    "tauri:build:android": "tauri android build -- --no-default-features --features mobile",
    "tauri:build:ios": "tauri ios build -- --no-default-features --features mobile",
    "tauri:dev:android": "tauri android dev -- --no-default-features --features mobile",
    "tauri:dev:ios": "tauri ios dev -- --no-default-features --features mobile"
  }
}
```

**注意**：移动端构建前需执行 `tauri ios init` 或 `tauri android init` 初始化原生工程。若采用 target 条件依赖（2.3 节），则无需 `--no-default-features`，`tauri android build` 会自动排除桌面库。

---

## 十一、风险与注意事项

| 风险 | 缓解 |
|------|------|
| Tauri 插件在移动端行为不同 | 优先用官方文档，对 shell/fs 做兼容测试；shell.open() 对 file:// 不可靠，需自定义插件 |
| 移动端 data_dir 路径 | 统一用 `app.path()` 系列 API；注意 [Issue #12276](https://github.com/tauri-apps/tauri/issues/12276) 移动端 path 解析 |
| `reqwest/blocking` 在移动端 | 移动端不启用 blocking |
| 前端 VM 相关逻辑 | 用 `@tauri-apps/plugin-os` 的 `type()` 检测，非 getCurrent().platform |
| 证书 / 签名 | iOS 需 Apple Developer，Android 需 keystore |
| tauri-plugin-fs scope | 移动端需在 capabilities 中配置 scope（如 `$APPCACHE/downloads/**`），Android 需声明存储权限 |
| Token 相关日志 | Release 构建中移除或脱敏 `update_cloud_token` 等处的 Token 相关 println |

---

## 十二、CI 策略

| 场景 | 建议 |
|------|------|
| **gen/ 是否提交** | 推荐提交 `gen/android`、`gen/ios`，便于复现构建、减少 CI 时间 |
| **init 时机** | 若已提交 gen/，CI 中不执行 init；若未提交，每次构建前执行 `tauri android init --ci` / `tauri ios init --ci` |
| **feature 校验** | 增加 `cargo check -p novaic --features desktop` 与 `cargo check --no-default-features --features mobile --target aarch64-linux-android` 提前发现配置问题 |

---

## 十三、测试策略

- **共享命令**：将业务逻辑抽成 `*_impl` 函数，在 `#[test]` 中直接测试，无需 Tauri 运行时
- **桌面集成**：使用 `tauri::test::mock_builder()` 构建应用，`invoke` 调用命令验证
- **移动端**：需模拟器或真机；可在文档中补充 Android 模拟器 CI 示例

---

## 十四、检查清单（对照实现）

> 本清单根据五位架构师（模块结构、安全、DevOps、平台兼容、可维护性）审计结果整理，按文档章节与当前实现逐项对照。  
> `✓` 已实现 | `✗` 未完成 | `简化` 采用简化方案 | `待验证` 需人工/环境验证

### 14.1 Cargo 与构建

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| target 条件依赖（vmcontrol、p2p、axum、quinn、tokio-tungstenite） | 2.3 | ✓ | `Cargo.toml` 已配置 |
| feature flags（desktop、mobile、custom-protocol） | 2.1 | ✓ | 已定义 |
| tauri default-features = false，tray-icon/devtools 仅 desktop | 2.2 | ✓ | 已配置 |
| tauri-plugin-process optional | 2.4 | ✓ | 已 optional，仅在 desktop 注册 |
| reqwest blocking 仅桌面 | 2.4 | ✓ | target 条件依赖中 |
| desktop+mobile 互斥 compile_error! | 2.3 | ✓ | `main.rs` 顶部已加 |
| npm 脚本：tauri:build:android/ios、tauri:dev:android/ios | 十 | ✓ | 已定义，带 `--` 传参 |
| tauri:build:desktop 脚本 | 十 | ✓ | 已添加别名 |

### 14.2 主入口与移动端

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| 单一 main.rs + #[cfg] 分支 | 3.4 | ✓ | setup 闭包内 desktop/mobile 分支 |
| mobile::setup() 精简启动 | 3.2 | ✓ | 调用 setup::setup_shared，默认云端 Gateway |
| setup::setup_shared 统一注入 | 3.3 | ✓ | Gateway URL、StorageBackend、VncProxy 桌面+移动端统一 |
| 移动端默认 gateway_url 云端 | 4.1 | ✓ | `https://api.gradievo.com` |
| 移动端无 Tray、无 PID、无 VmControl | 3.3 | ✓ | mobile.rs 无相关逻辑 |
| 共享命令在移动端注册 | 4 | ✓ | vnc_urls、gateway 等全平台注册 |
| 桌面专属命令在移动端不注册 | 4 | ✓ | VM 命令已 #[cfg] 排除；无 desktop 子模块 |

### 14.3 架构与模块拆分

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| core/ 目录（bootstrap、gateway_client、sse_stream、config、error） | 一、Phase 2 | ✓ | 已全部迁入 core/ |
| core::bootstrap::init() | 3.4、Phase 2 | ✓ | init() 统一调用 rustls、panic hook、tracing、NO_PROXY |
| commands/ 按功能拆分（gateway、auth、config、file、vnc_urls、secure_storage） | 一、Phase 2 | ✓ | 已迁入 commands/，无 desktop 子模块（get_vmcontrol_url 已删除） |
| platform/ 目录（StorageBackend、FileOps） | 一、Phase 4 | ✓ | platform/ 已建，FileOps、StorageBackend trait 已定义；secure_storage 命令委托 StorageBackend |
| desktop/ 目录 | 一、Phase 2 | ✓ 已删除 | get_vmcontrol_url 已删除，vnc_urls 已共享 |
| lib.rs 共享库入口 | 3.4 | 不需要 | 单 main.rs + mobile.rs + setup.rs 已足够 |
| 2.5 模块归属（split_runtime→core、cloud_connection→desktop 等） | 2.5 | 部分 | split_runtime gateway_base_url 已迁入 core::config |

### 14.4 凭证与安全

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| secure_storage 命令 | 5.3 | ✓ | 桌面/Android 加密文件，iOS Keychain |
| JWT 使用 SecureStorage | 5.3 | ✓ | auth.ts 接入 secureStorage |
| get_api_key | 5.3 | ✓ 已删除 | 设备 api_key 仅 vmcontrol 从 env 读取，前端无需调用 |
| Token println 脱敏（Release） | 十一 | ✓ | 已用 #[cfg(debug_assertions)] 包裹 |
| app_config / LLM keys 移动端处理 | 5.3 | 简化 | config_commands 仅桌面注册，移动端无 app_config |

### 14.5 文件操作

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| platform::FileOps trait | 6.3 | ✓ | 已定义，待 open_file 移动端插件接入 |
| open_file 移动端 | 6.1、6.3 | ✓ | tauri-plugin-opener，系统默认应用打开 |
| show_in_folder 移动端 | 6.2 | ✓ | 用 opener 打开父目录，失败时静默 |
| tauri-plugin-fs scope（$APPCACHE） | 十一 | ✓ | 已添加 fs:allow-appcache-*-recursive |

### 14.6 平台配置与版本

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| tauri.ios.conf.json 存在且 resources 正确 | 7.2 | ✓ | 已排除 qemu/android-sdk |
| tauri.android.conf.json 同上 | 7.3 | ✓ | 同上 |
| 版本策略：2020+（iOS 15、Android 11/API 30） | 新增 | ✓ | 文档已说明，tauri.android 已改为 minSdk 30 |
| app.windows: [] 移动端覆盖 | 7.2 | ✓ | tauri.ios.conf / tauri.android.conf 已添加 |

### 14.7 前端适配

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| @tauri-apps/plugin-os | Phase 6 | ✓ | 已加入依赖并注册 |
| isMobile() 使用 type() | Phase 6 | ✓ | useIsMobile hook 使用 plugin-os type() |
| VM/Device UI 在移动端隐藏 | Phase 6 | 不适用 | Device 为 app 逻辑，Rust 通过 P2P 与 vmcontrol 通信，移动端保留 |

### 14.8 测试与 CI

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| 命令逻辑抽成 *_impl 可测函数 | Phase 2、十三 | ✓ | gateway_get_impl 已抽取 |
| 共享命令 #[test] | 十三 | ✓ | test_local_url、test_gateway_get_impl |
| CI cargo check desktop/mobile | 十二 | ✓ | .github/workflows/tauri-ci.yml |

### 14.9 构建验证

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| 桌面 build 无回归 | 十四 | ✓ | 需人工验证 |
| 移动端 build 通过（至少 Android） | 十四 | 待验证 | 需 NDK 环境 |
| tauri android init / ios init 文档 | 十、Phase 5 | ✓ | HANDOVER、README 已补充 |
| cargo check --target aarch64-linux-android | 十二 | ✗ | 需配置 NDK，CI 中可跳过 |

### 14.10 文档与说明

| 检查项 | 文档章节 | 实现状态 | 说明 |
|--------|----------|----------|------|
| init 流程在 README/HANDOVER 中说明 | 十 | ✓ | 已补充 tauri android/ios init 步骤 |
| 移动端构建前置条件（NDK、Xcode） | 十 | ✓ | HANDOVER 已说明 |

---

### 汇总

| 类别 | 已完成 | 未完成 |
|------|--------|--------|
| Cargo 与构建 | 8/8 | 0 |
| 主入口与移动端 | 6/6 | 0 |
| 架构与模块 | 7/7 | 0 |
| 凭证与安全 | 5/5 | 0 |
| 文件操作 | 4/4 | 0 |
| 平台配置 | 4/4 | 0 |
| 前端适配 | 3/3 | 0 |
| 测试与 CI | 3/3 | 0 |
| 构建验证 | 3/4 | 1 |
| 文档与说明 | 2/2 | 0 |
