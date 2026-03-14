# Commands 拆分全面方案设计

> 目标：将 main.rs 中分散的 Tauri 命令按功能域拆分到 `commands/` 模块，实现可维护、可测试、平台清晰的命令结构。

---

## 一、现状分析

### 1.1 当前命令分布

| 位置 | 命令 | 平台 | 状态 |
|------|------|------|------|
| main.rs | get_gateway_url, set_gateway_url, get_gateway_status | 共享 | 在用 |
| main.rs | update_cloud_token | 共享 | 在用（get_api_key 已删除） |
| main.rs | gateway_get/post/patch/put/delete, gateway_health | 共享 | 在用 |
| main.rs | gateway_sse_connect, gateway_sse_disconnect | 共享 | 在用 |
| main.rs | fetch_authenticated_bytes, download_file_to_cache | 共享 | 在用 |
| main.rs | open_file, show_in_folder | 共享 | 在用 |
| ~~commands/desktop/urls.rs~~ | ~~get_vmcontrol_url~~ | ~~桌面~~ | **已删除**（前端改用 get_vnc_proxy_url / get_scrcpy_proxy_url） |
| commands/vnc_urls.rs | get_vnc_proxy_url, get_scrcpy_proxy_url | 共享 | 在用 |
| ~~vm/setup.rs, vm/deploy.rs~~ | ~~check_environment, check_cloud_image, download_cloud_image, deploy_agent~~ | ~~桌面~~ | **已删除**（迁入 vmcontrol vm_prep，前端走 Gateway） |
| ~~commands/config_commands.rs~~ | ~~get_app_config, add_api_key, ...~~ | ~~桌面~~ | **已删除**（孤儿，前端走 Gateway API） |
| ~~commands/file_commands.rs~~ | ~~upload_file, download_file, list_vm_files~~ | ~~桌面~~ | **已删除**（孤儿，前端未调用） |

### 1.2 状态类型依赖

| 状态类型 | 用途 | 命令依赖 |
|----------|------|----------|
| GatewayUrlState | 运行时 Gateway URL | gateway_*, set_gateway_url, get_gateway_url |
| ApiKeyState | 设备 API Key（vmcontrol 启动时从 env 读取） | 无 Tauri 命令 |
| CloudTokenState | Clerk JWT | gateway_*, update_cloud_token, fetch_authenticated_bytes |
| LoginNotifyState | 登录唤醒 CloudBridge | update_cloud_token |
| VmControlState | 嵌入式 VmControl（内部用） | 无 Tauri 命令（get_vmcontrol_url 已删除） |
| VncProxyState | VNC/Scrcpy 代理 | get_vnc_proxy_url, get_scrcpy_proxy_url |

### 1.3 孤儿模块处理（已完成）

- **config_commands + app_config**：已删除。本地 LLM 配置（API keys、模型）与 Gateway `/api/config` 重复，前端已完全走 gateway_get 访问配置。
- **file_commands**：已删除。通过 split_runtime agent_base_url 与本地 Agent 通信的 VM 文件上传/下载，前端未调用；若未来需要可参考 Gateway 设备 API 或从版本历史恢复。

---

## 二、目标架构

```
commands/
├── mod.rs                 # 模块聚合 + invoke_handler 注册入口
├── gateway.rs             # 共享：Gateway API 代理
├── auth.rs                # 共享：认证与 Token
├── config.rs              # 共享：Gateway URL 配置（非 app_config）
├── file.rs                # 共享：open_file, show_in_folder, download_file_to_cache, fetch_authenticated_bytes
├── secure_storage.rs      # 共享：JWT 等敏感数据
├── vnc_urls.rs            # 共享：get_vnc_proxy_url, get_scrcpy_proxy_url（桌面+移动端）
│
└── ~~desktop/~~           # 已删除：get_vmcontrol_url 已删除，前端改用 vnc_urls
```

### 2.1 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| **gateway** | Gateway HTTP 代理、SSE 连接 | core::gateway_client, core::sse_stream, GatewayUrlState, CloudTokenState |
| **auth** | JWT 更新（update_cloud_token） | CloudTokenState, LoginNotifyState |
| **config** | Gateway URL 读写、健康检查 | GatewayUrlState, AppHandle |
| **file** | 打开文件、显示目录、下载到缓存、认证字节获取 | platform::FileOps（可选）, CloudTokenState |
| **vnc_urls** | VNC、Scrcpy 代理 URL | VncProxyState（桌面+移动端） |
| ~~desktop/urls~~ | ~~VmControl base URL~~ | **已删除**（get_vmcontrol_url 已删除） |
| ~~desktop/app_config~~ | ~~本地 LLM 配置~~ | **已删除** |
| ~~desktop/vm_file~~ | ~~VM 文件上传下载~~ | **已删除** |

---

## 三、状态管理方案

### 3.1 状态类型归属

状态类型定义保留在 **main.rs** 或新建 **state.rs**，由 setup 注入，commands 通过 `tauri::State<'_, T>` 使用。

```
# 方案 A：保留在 main.rs
main.rs 中定义 ApiKeyState, GatewayUrlState, CloudTokenState, ...
commands 通过参数注入使用

# 方案 B：抽取 state 模块（推荐）
state/
  mod.rs       # pub type ApiKeyState = ...; 等
main.rs 与 commands 均 use crate::state::*;
```

### 3.2 推荐：state 模块

```rust
// state/mod.rs
use std::sync::Arc;

pub type ApiKeyState = Arc<String>;
pub type GatewayUrlState = Arc<std::sync::Mutex<String>>;
pub type CloudTokenState = Arc<tokio::sync::RwLock<String>>;
pub type LoginNotifyState = Arc<tokio::sync::Notify>;

#[cfg(not(any(target_os = "android", target_os = "ios")))]
pub type VmControlState = Arc<tokio::sync::Mutex<VmControlEmbedded>>;

#[cfg(not(any(target_os = "android", target_os = "ios")))]
pub type VncProxyState = ...;  // 来自 vnc_proxy
```

---

## 四、各模块详细设计

### 4.1 commands/gateway.rs（共享）

| 命令 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| gateway_get | path | Value | 已抽 gateway_get_impl |
| gateway_post | path, body? | Value | |
| gateway_patch | path, body? | Value | |
| gateway_put | path, body? | Value | |
| gateway_delete | path | Value | |
| gateway_health | - | bool | |
| gateway_sse_connect | path | () | |
| gateway_sse_disconnect | - | () | |
| fetch_authenticated_bytes | url | Vec<u8> | |

**依赖**：core::gateway_client, core::sse_stream, GatewayUrlState, CloudTokenState

### 4.2 commands/auth.rs（共享）

| 命令 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| update_cloud_token | token | () | 更新 CloudTokenState，触发 LoginNotifyState |

**依赖**：CloudTokenState, LoginNotifyState（get_api_key 已删除，设备 api_key 仅 vmcontrol 使用）

### 4.3 commands/config.rs（共享）

| 命令 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| get_gateway_url | - | String | |
| set_gateway_url | url | () | 持久化到 gateway_url.txt |
| get_gateway_status | - | bool | 健康检查 |

**依赖**：GatewayUrlState, AppHandle（用于 data_dir）

### 4.4 commands/file.rs（共享）

| 命令 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| open_file | path | () | 平台分支：桌面 shell，移动端 stub |
| show_in_folder | path | () | 同上 |
| download_file_to_cache | url, filename? | { path } | 下载到 $APPCACHE |
| fetch_authenticated_bytes | url | Vec<u8> | 带 JWT 的 HTTP GET |

**依赖**：CloudTokenState, platform::FileOps（可选，当前未接入）

### 4.5 commands/desktop/vm.rs（桌面）

| 命令 | 来源 | 说明 |
|------|------|------|
| check_environment | vm::setup | |
| check_cloud_image | vm::setup | |
| download_cloud_image | vm::setup | |
| deploy_agent | vm::deploy | |

### 4.6 ~~commands/desktop/urls.rs~~（已删除）

get_vmcontrol_url 已删除，前端改用 get_vnc_proxy_url / get_scrcpy_proxy_url（在 vnc_urls.rs）。

### 4.7 ~~commands/desktop/p2p.rs~~（已删除）

p2p_commands（start_discovery, stop_discovery, list_discovered_devices）已删除：前端从未调用，Phase 2 本地发现未接入。

### 4.8 commands/desktop/app_config.rs（桌面，可选）

config_commands 迁入。若前端已完全走 Gateway API，可标记为 deprecated 或移除。

### 4.9 commands/desktop/vm_file.rs（桌面，可选）

file_commands 迁入。依赖 split_runtime、http_client，与 Gateway 设备 API 不同（本地 Agent 文件服务）。

---

## 五、invoke_handler 注册策略

### 5.1 注册入口

```rust
// commands/mod.rs
pub fn invoke_handlers() -> impl FnOnce(&mut InvokeHandler) {
    |handler| {
        handler
            .invoke_handler(tauri::generate_handler![
                // 共享
                gateway::gateway_get,
                gateway::gateway_post,
                // ...
                auth::update_cloud_token,
                config::get_gateway_url,
                config::set_gateway_url,
                config::get_gateway_status,
                file::open_file,
                file::show_in_folder,
                file::download_file_to_cache,
                file::fetch_authenticated_bytes,
                vnc_urls::get_vnc_proxy_url,
                vnc_urls::get_scrcpy_proxy_url,
                // VM 命令（桌面）保留在 vm::setup/deploy
            ]);
    }
}
```

或保持 main.rs 中 `generate_handler![]` 列表，从各模块 `use` 命令函数。

### 5.2 推荐：集中注册

在 `commands/mod.rs` 中聚合所有命令，main.rs 调用 `commands::all_handlers()` 或类似接口，避免 main 膨胀。

---

## 六、迁移步骤（分阶段）

### Phase 1：基础设施

1. 新建 `state/mod.rs`，迁移状态类型定义
2. main.rs 中 setup 使用 `state::*`，invoke 仍保留在 main

### Phase 2：共享命令迁移

1. 创建 `commands/gateway.rs`，迁移 gateway_*、fetch_authenticated_bytes
2. 创建 `commands/auth.rs`，迁移 update_cloud_token（get_api_key 已删除）
3. 创建 `commands/config.rs`，迁移 get_gateway_url、set_gateway_url、get_gateway_status
4. 创建 `commands/file.rs`，迁移 open_file、show_in_folder、download_file_to_cache
5. 更新 commands/mod.rs 导出
6. main.rs 中 `use commands::{gateway, auth, config, file}`，invoke_handler 引用新路径

### Phase 3：桌面命令迁移

1. ~~创建 commands/desktop/~~（已删除：get_vmcontrol_url 已删除，vnc_urls 已共享）
2. commands/desktop/vm.rs：VM 命令保留在 vm::setup、vm::deploy，invoke 直接引用
3. ~~commands/desktop/urls.rs~~（get_vmcontrol_url 已删除）
4. ~~commands/desktop/p2p.rs~~（p2p_commands 已删除）

### Phase 4：孤儿模块处理（已完成）

1. ~~config_commands + app_config~~：已删除，前端走 Gateway API
2. ~~file_commands~~：已删除，前端未调用

---

## 七、可测试性

### 7.1 *_impl 抽取

| 命令 | 可抽 impl | 说明 |
|------|-----------|------|
| gateway_get | ✅ 已有 | gateway_get_impl |
| set_gateway_url | set_gateway_url_impl(url, data_dir) | 纯逻辑，可单测 |
| download_file_to_cache | download_to_cache_impl(url, token, cache_dir) | 可 mock reqwest |

### 7.2 测试策略

- 有 impl 的命令：对 impl 写 `#[test]`
- 无 impl 的薄包装：依赖 Tauri mock 或集成测试

---

## 八、依赖关系图

```
                    main.rs (setup, run)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
     state/          commands/        core/
  (类型定义)         (命令实现)      (gateway_client, sse_stream, config)
         │               │
         │     ┌─────────┼─────────────────────┐
         │     ▼         ▼         ▼          ▼
         │  gateway   auth    config   file  vnc_urls  secure_storage
         │     │         │         │     │      │
         └─────┴─────────┴─────────┴─────┴──────┘
                         │
              #[cfg(desktop)]（vm 命令在 vm::setup/deploy）
                         ▼
                    vnc_proxy（全平台）
```

---

## 九、风险与注意事项

1. **状态注入顺序**：setup 中 `app.manage()` 顺序需与命令依赖一致
2. **循环依赖**：commands 不引用 main，仅通过 State 获取依赖
3. **cfg 条件**：desktop 子模块需 `#[cfg(not(any(target_os = "android", target_os = "ios")))]`，避免移动端编译拉入 vmcontrol 等
4. **孤儿模块**：config_commands、file_commands、app_config 已删除

---

## 十、检查清单（实施对照）

### 10.1 Phase 1：基础设施

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 新建 state/mod.rs | ☑ | 定义 ApiKeyState, GatewayUrlState, CloudTokenState, LoginNotifyState |
| VmControlState, VncProxyState 条件编译 | ☑ | state/vmcontrol.rs #[cfg(not(android, ios))]，VncProxyState 保留在 vnc_proxy |
| main.rs setup 使用 state::* | ☑ | app.manage 注入状态 |

### 10.2 Phase 2：共享命令

| 检查项 | 状态 | 说明 |
|--------|------|------|
| commands/gateway.rs 创建 | ☑ | gateway_get/post/patch/put/delete, gateway_health, gateway_sse_*, fetch_authenticated_bytes |
| commands/auth.rs 创建 | ☑ | update_cloud_token（get_api_key 已删除） |
| commands/config.rs 创建 | ☑ | get_gateway_url, set_gateway_url, get_gateway_status |
| commands/file.rs 创建 | ☑ | open_file, show_in_folder, download_file_to_cache |
| commands/mod.rs 导出 | ☑ | pub mod gateway, auth, config, file |
| main.rs invoke_handler 引用 | ☑ | 使用 commands::gateway::*, commands::auth::*, 等 |

### 10.3 Phase 3：桌面命令

| 检查项 | 状态 | 说明 |
|--------|------|------|
| commands/desktop/ | ☑ 已删除 | get_vmcontrol_url 已删除，vnc_urls 已共享 |
| commands/desktop/vm.rs | ☐ | VM 命令保留在 vm::setup、vm::deploy，invoke 直接引用 |
| commands/desktop/p2p.rs | ☑ 已删除 | p2p_commands 已删除（前端未接入） |

### 10.4 Phase 4：main.rs 精简

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 命令函数从 main.rs 移除 | ☑ | 共享命令已迁入 commands/，桌面 URLs 迁入 commands/desktop/urls |
| gateway_get_impl 归属 | ☑ | 已迁入 commands/gateway |
| local_url, read_gateway_url 等 | ☑ | read_gateway_url 在 state，local_url 在 commands/config |

### 10.5 验证

| 检查项 | 状态 | 说明 |
|--------|------|------|
| cargo check 通过 | ☑ | desktop 构建通过 |
| cargo test 通过 | ☑ | test_local_url, test_gateway_get_impl 通过 |
| 前端 invoke 无回归 | ☑ | 命令名不变 |
| 桌面命令移动端不编译 | ☑ | cfg(not(android, ios)) 正确 |
