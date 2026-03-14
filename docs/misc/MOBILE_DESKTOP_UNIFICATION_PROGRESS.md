# 移动端 + 桌面统一代码进展梳理

> 最后更新：2026-03-10

---

## 一、目标与策略

**目标**：单一代码库，通过 `#[cfg]` 和 target 条件依赖，支持 Mac/Windows 桌面 + Android/iOS 移动端构建。

**策略**：
- **Rust 侧**：`target_os = "android" | "ios"` 条件编译，桌面专属模块（vmcontrol、托盘、http_client）自动排除
- **前端**：共享 React 代码，通过 `@tauri-apps/plugin-os` 的 `type()` 检测平台，切换布局（三栏 vs 底 Tab）
- **依赖**：`[target.'cfg(...)'.dependencies]` 按平台拉入，无需 `--no-default-features`

---

## 二、已完成项

### 2.1 Rust 后端

| 模块 | 状态 | 说明 |
|------|------|------|
| **单 main.rs + cfg 分支** | ✅ | `setup` 内 `#[cfg(any(android, ios))]` → `mobile::setup`，否则桌面 setup |
| **mobile.rs** | ✅ | 移动端精简 setup：无 VmControl、无托盘、无 PID 文件；有 Gateway、Auth、VncProxy |
| **全平台 commands** | ✅ | gateway、auth、config、file、vnc_urls、**secure_storage** 全平台注册 |
| **vnc_proxy 全平台** | ✅ | 桌面：本地 loopback + 远端 P2P；移动端：仅远端 Gateway locate + QUIC P2P |
| **open_file 移动端** | ✅ | tauri-plugin-opener，Android/iOS 用系统默认应用打开 |
| **show_in_folder 移动端** | ⚠️ | stub（静默成功），非关键 |
| **Cargo.toml target 依赖** | ✅ | vmcontrol/blocking 仅桌面；p2p/axum/quinn 桌面+移动端（VncProxy 需 P2P） |
| **feature 互斥** | ✅ | `desktop` 与 `mobile` 互斥，编译断言 |

### 2.2 SecureStorage（2026-03 新增）

| 项目 | 状态 | 说明 |
|------|------|------|
| **secure_storage 命令** | ✅ | `secure_storage_get`、`secure_storage_set`、`secure_storage_delete` |
| **桌面（macOS/Windows/Linux）** | ✅ | AES-256-GCM 加密文件，避免 Keychain 弹窗吓到用户 |
| **iOS** | ✅ | keyring（Keychain），iOS 通常不弹密码窗 |
| **Android** | ✅ | AES-256-GCM 加密文件 `secure_store.dat` |

### 2.3 已删除 / 迁移

| 项目 | 说明 |
|------|------|
| vm/ | 环境检查、镜像、部署迁入 vmcontrol vm_prep，前端走 Gateway |
| cloud_connection.rs | Cloud Bridge 合并进 vmcontrol |
| p2p_commands | Phase 2 本地 mDNS 发现，前端未接入，已删除 |
| config_commands, file_commands | 孤儿模块，已删除 |
| get_api_key | 前端未调用，已删除 |
| get_vmcontrol_url | 前端改用 get_vnc_proxy_url / get_scrcpy_proxy_url，已删除 |
| commands/desktop/, commands/mobile/ | 随 get_vmcontrol_url 删除 |

### 2.4 前端

| 项目 | 状态 |
|------|------|
| useIsMobile | ✅ 使用 `@tauri-apps/plugin-os` 的 `type()`，Web fallback userAgent |
| 布局切换 | ✅ `useIsSidebarLayout` / `LayoutContainer` 根据宽度 + 平台切换三栏 / 底 Tab |
| API 调用 | ✅ 统一 `invoke('gateway_*')`，与平台无关 |
| SSE | ✅ `invoke('gateway_sse_connect')` 共享 |
| 认证 | ✅ `invoke('update_cloud_token')` 共享 |
| **Auth + SecureStorage** | ✅ auth.ts 已接入 secureStorage.ts，JWT 存 Keychain/Keystore |
| **localStorage 迁移** | ✅ secureGet 空时从 localStorage 迁移到 SecureStorage |
| **Gateway URL 同步** | ✅ App 启动时同步 VITE_GATEWAY_URL 到 Rust gateway_url.txt |
| VNC/Scrcpy | ✅ 仅用 get_vnc_proxy_url / get_scrcpy_proxy_url，无 fallback |

### 2.5 构建配置

| 文件 | 状态 |
|------|------|
| tauri.conf.json | ✅ 基础配置 |
| tauri.ios.conf.json | ✅ iOS 覆盖（resources、minVersion） |
| tauri.android.conf.json | ✅ Android 覆盖（resources、minSdk 30） |

---

## 三、待完成 / 待完善

### 3.1 中优先级

| 项目 | 说明 |
|------|------|
| **lib.rs 抽取** | 不需要：单 main.rs + mobile.rs 已足够，core/commands 已模块化 |

### 3.2 低优先级 / 可选

| 项目 | 说明 |
|------|------|
| **core::bootstrap::init()** | 计划抽到 core，当前 init 逻辑仍在 main |
| **platform::FileOps trait** | 文档建议的抽象，当前 file.rs 内联 cfg 分支 |
| **IPlatformBridge 前端抽象** | CROSS_PLATFORM_ARCHITECTURE 建议，当前直接 invoke |

---

## 四、命令矩阵（当前）

| 命令 | 桌面 | 移动 |
|------|------|------|
| gateway_* | ✅ | ✅ |
| update_cloud_token | ✅ | ✅ |
| get/set_gateway_url, get_gateway_status | ✅ | ✅ |
| **secure_storage_get/set/delete** | ✅ | ✅ |
| fetch_authenticated_bytes, download_file_to_cache | ✅ | ✅ |
| open_file | ✅ | ✅（opener） |
| show_in_folder | ✅ | ✅（opener 打开父目录） |
| get_vnc_proxy_url, get_scrcpy_proxy_url | ✅ | ✅ |

---

## 五、模块归属一览

| 模块 | 桌面 | 移动 |
|------|------|------|
| core/ | ✅ | ✅ |
| commands/ | ✅ | ✅ |
| commands/secure_storage | ✅ | ✅ |
| state/ | ✅ | ✅ |
| platform/ | ✅ | ✅ |
| vnc_proxy | ✅ | ✅（仅远端路径） |
| vmcontrol | ✅ | ❌ |
| http_client | ✅ | ❌ |
| mobile | ❌ | ✅ |
| p2p | ✅ | ✅（VncProxy 用） |
| axum, quinn | ✅ | ✅（VncProxy 用） |

---

## 六、数据流与存储

| 数据类型 | 存储位置 | 平台 |
|----------|----------|------|
| JWT access/refresh | SecureStorage | 桌面 AES 加密文件；Android 加密文件；iOS Keychain |
| 用户信息缓存 | 内存 _cachedUser | 全平台 |
| gateway_url | gateway_url.txt | 桌面；移动端默认 api.gradievo.com |
| api_key | api_key.txt | 桌面 |
| IndexedDB | messages/logs/prefs/files | 全平台 WebView |

---

## 七、构建与验证

| 平台 | 命令 | 备注 |
|------|------|------|
| 桌面 | `npm run tauri:dev` | 开发模式 |
| 桌面 | `npm run tauri:build -- --bundles app` | 打包 .app |
| Android | `npm run tauri:dev:android` | 需 NDK |
| Android | `npm run tauri:build:android` | 需 NDK |
| iOS | `npm run tauri:dev:ios` | 需 Xcode、真机/模拟器 |
| iOS | `npm run tauri:build:ios` | 需 Xcode |

---

## 八、相关文档

| 文档 | 用途 |
|------|------|
| `TAURI2_MOBILE_MODULARIZATION_PLAN.md` | 模块化计划、命令矩阵、实施阶段、检查清单 |
| `COMMANDS_ANALYSIS.md` | 命令清单、状态依赖、前端映射 |
| `CROSS_PLATFORM_ARCHITECTURE.md` | 跨平台抽象建议（IPlatformBridge、Storage、Layout） |
| `COMMANDS_SPLIT_DESIGN.md` | 命令拆分与目标架构 |
| `SECURE_STORAGE_DESIGN.md` | 敏感数据存储设计 |

---

## 九、近期变更摘要（2026-03）

1. **SecureStorage 实现**：Rust 命令 + 前端 secureStorage.ts + auth 接入
2. **keyring 平台特性**：显式启用 apple-native、windows-native、sync-secret-service，避免 mock 存储
3. **localStorage 迁移**：secureGet 空时从 localStorage 迁移到 SecureStorage
4. **Gateway URL 同步**：App 启动时同步 VITE_GATEWAY_URL 到 Rust，解决桌面默认 localhost 导致登录失败
5. **show_in_folder 移动端**：用 opener 打开父目录，失败时静默（替代 stub）
6. **桌面 SecureStorage 改用加密文件**：避免 macOS Keychain 弹窗吓到用户，仅 iOS 保留 Keychain
