# OTA 与 invoke 兼容性：4 名 Subagent 调研报告

> 2026-03-12，针对「OTA 不支持 invoke」结论的深度复核

---

## 一、核心结论：之前的判断不准确

| 原结论 | 调研结论 |
|--------|----------|
| OTA 不支持 invoke | **不准确**：Tauri 2 官方支持 OTA + invoke，需正确配置 capability |
| 混合内容（HTTPS → ipc://）导致失败 | **部分成立**：仅 macOS/iOS WKWebView 有此限制，Tauri 有 postMessage 回退（但有 JSON 响应 bug） |
| 必须禁用 OTA | **非必须**：配置正确时 OTA 可与 invoke 共存 |

---

## 二、Tauri 2 官方立场

**Remote API Access**（[文档](https://v2.tauri.app/security/capabilities/#remote-api-access)）：

> By default the API is only accessible to bundled code shipped with the Tauri App.  
> **To allow remote sources access to certain Tauri Commands** it is possible to define this in the capability configuration file.

即：**远程 URL 可通过 capability 的 `remote.urls` 获得 invoke 权限**。

---

## 三、invoke 底层实现（澄清）

- **不是**：HTTPS 页面直接请求 `ipc://` 被浏览器拦截
- **实际**：Tauri 使用 WebView 自定义 URI scheme（如 `tauri://localhost`），由 Tauri Runtime 注册
- **校验**：Runtime Authority 根据 **当前 document 的 origin** 判断是否允许调用命令，与 capability 的 `remote.urls` 匹配

---

## 四、本项目配置检查

| 配置项 | 状态 | 说明 |
|--------|------|------|
| `capabilities/remote-frontend.json` | ✅ 已配置 | `remote.urls`: `https://relay.gradievo.com/*`, `https://api.gradievo.com/*` |
| `permissions/allow-app-commands.toml` | ✅ 已配置 | 24 个命令白名单 |
| `security.csp` | `null` | 无 CSP 限制 |

**结论**：当 WebView 加载 `https://relay.gradievo.com/resource/frontend/...` 时，**invoke 应能正常工作**。

---

## 五、可能的失败原因（按优先级）

### 1. Capability URL 不匹配（主因）

- Gateway 返回的 `frontend_url` 不在 `remote.urls` 范围内
- 例如：返回 `https://cdn.other.com/...` 则 capability 不匹配，`__TAURI__` 不注入
- **解决**：确保 `FRONTEND_CDN_URL` 与 `remote.urls` 一致

### 2. 混合内容（macOS/iOS 特有）

- HTTPS 页面 → `ipc://` 请求可能被 WKWebView 拦截
- Tauri 会 fallback 到 postMessage，但 postMessage 对 **JSON 返回值** 有已知 bug（[#9266](https://github.com/tauri-apps/tauri/issues/9266)）
- **解决**：关注 Tauri 版本更新，或避免在 invoke 中返回复杂 JSON

### 3. Service Worker 干扰

- 远程页面 + Service Worker 时，二次启动后 invoke 可能失败（[#12673](https://github.com/tauri-apps/tauri/issues/12673)）
- **解决**：检查前端是否使用 SW，必要时禁用

### 4. 新增命令未加入白名单

- `allow-app-commands.toml` 中 `commands.allow` 需包含所有需 invoke 的命令
- **解决**：新增命令时同步更新

---

## 六、可行方案（4 名 Subagent 共识）

1. **方案 A（推荐）**：保证 Gateway 的 `FRONTEND_CDN_URL` 与 `remote-frontend.json` 的 `remote.urls` 完全一致；若换 CDN 域名，在 `remote.urls` 中补充。
2. **方案 B**：恢复 OTA 逻辑，增加 `frontend_url` 与 capability 匹配的日志，并在前端检测 `__TAURI__` 做 fallback 提示。
3. **方案 C**：临时写死 `navigate("https://relay.gradievo.com/resource/frontend/v0.3.0/")`，快速验证「URL 匹配 remote.urls 时 invoke 是否正常」。

---

## 七、当前状态

- **OTA 已禁用**：`setup.rs` 中不执行 `navigate()`，始终加载本地 `../dist`
- **因此**：当前 release 不会出现 OTA + invoke 失败
- **若重新启用 OTA**：按上述方案确保 capability 与 URL 配置正确后，invoke 应可正常工作

---

## 八、参考

- [Tauri 2 Capabilities - Remote API Access](https://v2.tauri.app/security/capabilities/#remote-api-access)
- [Tauri Issue #7662](https://github.com/tauri-apps/tauri/issues/7662)（混合内容）
- [Tauri Issue #9266](https://github.com/tauri-apps/tauri/issues/9266)（postMessage JSON 响应）
- [Tauri Issue #12673](https://github.com/tauri-apps/tauri/issues/12673)（Service Worker）
- 项目内：`docs/OTA_INVOKE_ROOT_CAUSE_ANALYSIS.md`、`docs/HOT_UPDATE_EXECUTION_PLAN.md`
