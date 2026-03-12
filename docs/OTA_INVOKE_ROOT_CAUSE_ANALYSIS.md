# OTA 场景下 invoke 不工作：根因分析与可行方案

> 综合调研报告，2026-03-12

---

## 一、完整调用链梳理

### 1.1 用户操作 → invoke → 后端

```
用户打开 OTA 前端（WebView 已 navigate 到 CDN URL）
  → 点击某功能（如 VNC、VM 设置、文件下载等）
  → 前端调用 invoke('xxx', args)
  → @tauri-apps/api/core 的 invoke() 内部使用 window.__TAURI__.core.invoke()
  → Tauri IPC 层（fetch 到 ipc://localhost 或等效通道）
  → Rust 侧 invoke_handler 路由到对应命令（gateway_get、get_vnc_proxy_url 等）
  → 命令执行并返回
```

### 1.2 关键依赖

| 环节 | 依赖 | 说明 |
|------|------|------|
| `invoke()` 可用 | `window.__TAURI__` 已注入 | Tauri 根据 capability 决定是否注入 |
| 命令执行 | capability 中 `allow-app-commands` 或等价权限 | 白名单控制可调用的命令 |
| IPC 通道 | 无 CSP 阻止 `connect-src` | 需允许 `ipc.localhost` 或等效 |

### 1.3 本地 vs OTA 的差异

| 维度 | 本地打包前端 | OTA CDN 前端 |
|------|--------------|--------------|
| **加载方式** | `frontendDist` 打包进应用，`tauri://localhost/` 或 `asset://` | `navigate(https://relay.gradievo.com/...)` |
| **Origin** | `tauri://localhost` / `asset://` | `https://relay.gradievo.com` |
| **Protocol** | 自定义 scheme | HTTPS |
| **Capability 匹配** | `local: true` 的 capability 均适用 | 仅 `remote.urls` 匹配的 capability 适用 |
| **main-cap** | ✅ 适用（local only） | ❌ 不适用（无 remote 配置） |
| **remote-frontend-capability** | ✅ 适用（local: true） | ✅ 仅当 URL 匹配 remote.urls 时 |

---

## 二、项目中 OTA + invoke 相关记录

### 2.1 错误日志 / Issue / 注释

| 来源 | 内容 |
|------|------|
| `permissions/allow-app-commands.toml` | **"Without this, invoke() fails with 'Not allowed to request resource'."** |
| `docs/HOT_UPDATE_EXECUTION_PLAN.md` | "需为加载远程 URL 的窗口配置 remote.urls，否则 window.__TAURI__ 不会注入，invoke 等 API 不可用" |
| `docs/REMOTE_URL_HOT_UPDATE_REPORT.json` | "远程 URL 默认不注入 window.__TAURI__"；"connect-src 需包含 ipc.localhost 以支持 Tauri invoke" |
| `docs/OTA_FLOW_CAPABILITY_SWITCH.md` | "Gateway returns non-relay URL → neither capability applies → Tauri API calls are denied" |

### 2.2 当前 OTA 状态

**OTA 已禁用**（`setup.rs` 第 141–155 行）：

```rust
// OTA 已禁用：桌面和移动端均使用本地打包的前端，不 navigate 到 CDN。
// 如需启用 OTA，可设置 NOVAIC_OTA_ENABLED=1。
pub fn spawn_frontend_ota_task(app: AppHandle, _gw_url: String) {
    // ...
    println!("[Frontend OTA] Disabled, using local assets");
    // 直接 show，不 fetch、不 navigate
}
```

因此，**当前 release 构建下不会出现 OTA + invoke 失败**，因为实际未 navigate 到 CDN。若恢复 OTA 或手动 navigate 到远程 URL，则可能出现 invoke 失败。

---

## 三、根因分析

### 3.1 主因：Capability 不匹配导致 `__TAURI__` 未注入

Tauri 2 的 Remote API Access 机制：

- **默认**：仅 bundled 本地内容可访问 Tauri API
- **远程 URL**：必须在 capability 的 `remote.urls` 中显式放行，否则 `window.__TAURI__` 不注入，`invoke` 不可用

**典型失败场景**：

1. **Gateway 返回的 URL 不在 `remote.urls` 中**
   - 例如：`FRONTEND_CDN_URL=https://cdn.example.com/frontend/`
   - `remote-frontend.json` 仅包含 `https://relay.gradievo.com/*`、`https://api.gradievo.com/*`
   - 结果：无 capability 匹配 → 无 `__TAURI__` → invoke 失败

2. **URL 模式语法问题**
   - Tauri 使用 URLPattern；部分写法（如带端口的正则）可能匹配失败
   - 文档建议使用明确端口，如 `http://localhost:8080` 而非 `http://localhost(:\d+)?`

3. **Capability 未正确加载**
   - 若 `tauri.conf.json` 中 `app.security.capabilities` 显式列出且未包含 `remote-frontend-capability`，则不会生效
   - 当前项目未显式配置，capabilities 目录下文件应自动加载

### 3.2 与「混合内容」结论的对比

| 假设 | 结论 | 说明 |
|------|------|------|
| **混合内容（HTTP in HTTPS）** | ❌ 非主因 | OTA 前端来自 `https://relay.gradievo.com`，为 HTTPS；invoke 使用 Tauri 的 ipc 通道，非普通 HTTP 请求 |
| **CSP 阻止** | ⚠️ 可能次要 | 当前 `csp: null`，无 CSP；若启用 CSP，需在 `connect-src` 中放行 `ipc.localhost` |
| **Capability / remote.urls** | ✅ **主因** | 远程 URL 未匹配 capability 时，`__TAURI__` 不注入，invoke 不可用 |
| **Origin 校验** | ✅ 与 capability 一致 | Tauri 通过 `remote.urls` 做 origin 校验，本质是 capability 匹配 |
| **命令白名单** | ✅ 已配置 | `allow-app-commands.toml` 已列出所需命令，问题在 capability 是否应用到当前 URL |

**结论**：主因是 **Capability 的 `remote.urls` 未覆盖实际 OTA URL**，导致 `__TAURI__` 未注入；混合内容不是主要因素。

---

## 四、其他可能因素

| 因素 | 可能性 | 说明 |
|------|--------|------|
| **CSP** | 中 | 若启用 CSP，`connect-src` 需包含 `ipc.localhost`；当前 `csp: null` 无影响 |
| **main-cap 无 invoke 权限** | 已明确 | `main-cap` 仅含 event/window/shell/opener，不含 `allow-app-commands`；invoke 依赖 `remote-frontend-capability` |
| **iOS/Android 差异** | 待验证 | 移动端 capability 加载可能与桌面不同；`remote-frontend.json` 使用 `desktop-schema`，需确认移动端是否生效 |
| **Tauri 已知 bug** | 低 | GitHub #11934 针对「浏览器访问」非 WebView；WebView 内 navigate 到远程 URL 的理论支持已文档化 |

---

## 五、可行修复 / 验证方案

### 方案 1：验证并修正 remote.urls 与 Gateway 配置（推荐）

**步骤**：

1. 确认 Gateway 返回的 `frontend_url` 与 `remote-frontend.json` 的 `remote.urls` 一致：
   - 默认：`https://relay.gradievo.com/resource/frontend/v0.3.0/` ✅ 匹配 `https://relay.gradievo.com/*`
   - 若使用 `api.gradievo.com/static/`，需在 `remote.urls` 中已有 `https://api.gradievo.com/*` ✅

2. 若使用其他 CDN 域名，在 `remote-frontend.json` 中补充：

```json
"remote": {
  "urls": [
    "https://relay.gradievo.com/*",
    "https://api.gradievo.com/*",
    "https://your-cdn.example.com/*"
  ]
}
```

3. 在 `jwt_secret.env.example` 和部署文档中明确：`FRONTEND_CDN_URL` 必须落在 `remote.urls` 的域名范围内。

**验证**：启用 OTA 后，在 OTA 页面控制台执行 `'__TAURI__' in window`，应为 `true`。

---

### 方案 2：恢复 OTA 逻辑并增加诊断日志

**步骤**：

1. 在 `spawn_frontend_ota_task` 中恢复 fetch + navigate 逻辑（可通过 `NOVAIC_OTA_ENABLED=1` 控制）。

2. 在 navigate 前后打日志：
   - 打印 `frontend_url` 与 `remote.urls` 的匹配结果
   - 在 WebView 的 `page_load` 或等效事件中，检查当前 URL 与 capability 的匹配情况

3. 在前端增加 fallback：若 `!window.__TAURI__`，显示「当前环境不支持部分功能，请使用本地版本」并可选重载到本地。

**验证**：通过日志确认 navigate 的 URL、capability 匹配结果，以及 `__TAURI__` 是否注入。

---

### 方案 3：最小化 OTA 验证（快速排查）

**步骤**：

1. 在 `setup` 中临时写死 `navigate("https://relay.gradievo.com/resource/frontend/v0.3.0/")`，跳过 Gateway 请求。

2. 启动 release 构建，确认 OTA 页面是否可正常 `invoke`。

3. 若可工作：问题在 Gateway 返回的 URL 或环境配置；若仍失败：问题在 capability 配置或 Tauri 行为。

**验证**：直接验证「固定 URL + 已知匹配 remote.urls」场景下的 invoke 是否可用。

---

## 六、总结

| 项目 | 结论 |
|------|------|
| **根因** | Capability 的 `remote.urls` 未覆盖实际 OTA URL，导致 `__TAURI__` 不注入，invoke 不可用 |
| **混合内容** | 非主因；OTA 为 HTTPS，invoke 走 Tauri IPC |
| **优先修复** | 确保 Gateway 的 `FRONTEND_CDN_URL` 与 `remote-frontend.json` 的 `remote.urls` 一致 |
| **验证手段** | 在 OTA 页面执行 `'__TAURI__' in window`，并恢复 OTA 逻辑做端到端测试 |
