# Tauri Commands 分析

> 基于当前 invoke_handler 注册与模块结构（2026-03 更新）

---

## 一、命令清单（按平台）

### 1.1 共享命令（桌面+移动端）

| 模块 | 命令 | 用途 |
|------|------|------|
| **config** | `get_gateway_url` | 获取运行时 Gateway URL |
| **config** | `set_gateway_url` | 设置 Gateway URL |
| **config** | `get_gateway_status` | 检查 Gateway 健康 |
| **auth** | `update_cloud_token` | 更新 JWT（推送给 Cloud Bridge） |
| **secure_storage** | `secure_storage_get` | 安全存储读取 |
| **secure_storage** | `secure_storage_set` | 安全存储写入 |
| **secure_storage** | `secure_storage_delete` | 安全存储删除 |
| **gateway** | `gateway_get` | GET 请求代理 |
| **gateway** | `gateway_post` | POST 请求代理 |
| **gateway** | `gateway_patch` | PATCH 请求代理 |
| **gateway** | `gateway_put` | PUT 请求代理 |
| **gateway** | `gateway_delete` | DELETE 请求代理 |
| **gateway** | `gateway_health` | Gateway 健康检查 |
| **gateway** | `gateway_sse_connect` | 建立 SSE 连接 |
| **gateway** | `gateway_sse_disconnect` | 断开 SSE 连接 |
| **gateway** | `fetch_authenticated_bytes` | 带认证的字节获取 |
| **file** | `download_file_to_cache` | 下载文件到缓存 |
| **file** | `open_file` | 打开文件（桌面用系统默认；移动端 stub） |
| **file** | `show_in_folder` | 在文件夹中显示（桌面用；移动端 stub） |
| **vnc_urls** | `get_vnc_proxy_url` | VNC 代理 WebSocket URL |
| **vnc_urls** | `get_scrcpy_proxy_url` | Scrcpy 代理 WebSocket URL |

---

## 二、模块结构

```
commands/
├── mod.rs           # 模块聚合
├── auth.rs          # 共享：认证
├── config.rs       # 共享：Gateway URL 配置
├── file.rs         # 共享：文件操作
├── gateway.rs      # 共享：Gateway API 代理 + SSE
├── secure_storage.rs # 共享：JWT 等敏感数据（委托 platform::StorageBackend）
├── vnc_urls.rs     # 共享：VNC/Scrcpy 代理 URL（无 desktop 子模块）
```

---

## 三、状态依赖

| 状态类型 | 注入位置 | 命令依赖 |
|----------|----------|----------|
| GatewayUrlState | main/mobile setup | config::*, gateway::* |
| ApiKeyState | main/mobile setup | （内部 NOVAIC_API_KEY，无 invoke） |
| CloudTokenState | main/mobile setup | auth::*, gateway::*, fetch_authenticated_bytes |
| LoginNotifyState | main/mobile setup | （Cloud Bridge 内部） |
| VncProxyState | main/mobile setup | vnc_urls::* |
| VmControlState | main setup（仅桌面） | （内部使用，无 invoke） |

---

## 四、已移除命令（历史）

| 命令 | 原位置 | 现状 |
|------|--------|------|
| ~~start_discovery, stop_discovery, list_discovered_devices~~ | ~~p2p_commands~~ | **已删除**（Phase 2 本地 mDNS 发现，前端未接入） |
| ~~get_api_key~~ | auth | **已删除**（前端未调用） |
| ~~get_vmcontrol_url~~ | desktop/urls | **已删除**（前端改用 get_vnc_proxy_url / get_scrcpy_proxy_url） |
| check_environment | vm/setup | 迁入 vmcontrol vm_prep，前端 gateway_get |
| check_cloud_image | vm/setup | 同上 |
| download_cloud_image | vm/setup | 同上 |
| deploy_agent | vm/deploy | 同上 |
| get_app_config, add_api_key, ... | config_commands | 已删除，前端走 Gateway |
| upload_file, download_file, list_vm_files | file_commands | 已删除，前端未调用 |

---

## 五、前端调用映射

| 前端调用 | 命令/API |
|----------|----------|
| `invoke('get_gateway_url')` | config::get_gateway_url |
| `invoke('gateway_get', {path})` | gateway::gateway_get |
| `invoke('gateway_post', {path, body})` | gateway::gateway_post |
| `invoke('update_cloud_token', {token})` | auth::update_cloud_token |
| `invoke('get_vnc_proxy_url', {deviceId})` | vnc_urls::get_vnc_proxy_url |
| `invoke('get_scrcpy_proxy_url', {deviceSerial, deviceId?})` | vnc_urls::get_scrcpy_proxy_url |

---

## 六、潜在改进

| 项目 | 说明 |
|------|------|
| open_file 移动端 | 已用 tauri-plugin-opener 实现 |
