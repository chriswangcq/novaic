# OTA 热更新重新启用 — 实施方案（V2，已根据 5 名 Subagent 评审完善）

> 基于 `docs/OTA_INVOKE_4_AGENT_REPORT.md` 调研结论，整合 5 名 Subagent 评审意见后的完善版

---

## 一、目标与范围

| 项目 | 说明 |
|------|------|
| **主目标** | 恢复 OTA 逻辑，使 App 启动时从 Gateway 获取 CDN URL 并 navigate 到远程前端；确保 invoke 在 OTA 场景下正常工作 |
| **平台** | 桌面 macOS + 移动端 iOS/Android |
| **原则** | 本地优先（失败时 fallback 本地）、URL 与 capability 严格匹配、可回滚 |

---

## 二、前置条件（已满足）

| 条件 | 状态 |
|------|------|
| Gateway `/api/config/frontend` | ✅ 已实现 |
| `FRONTEND_CDN_URL` 与 `remote.urls` 一致 | ✅ 默认 `relay.gradievo.com` |
| `allow-app-commands` 白名单 | ✅ 24 个命令已配置 |
| 前端部署到 relay | ✅ `deploy-all.sh` 已支持 |

---

## 三、实施方案（Phase 1–4）

### Phase 1：恢复 OTA 核心逻辑（setup.rs）

**文件**：`novaic-app/src-tauri/src/setup.rs`

**实现要点**：

1. **环境变量** `NOVAIC_OTA_ENABLED`：支持 `1`、`true`、`yes`、`on`（不区分大小写）为启用，其余为禁用；默认未设置 = 禁用。
2. **仅 release 构建执行**；dev 模式始终跳过。
3. **窗口创建时机**：需确认 `get_webview_window("main")` 在 spawn 时是否已可用；若否，需轮询或 `on_window_created` 等待。
4. **移动端 show**：无论桌面或移动端，OTA 任务结束时**必须**调用 `show()`；当前 `#[cfg(desktop)]` 需扩展，确保移动端也能正确显示窗口。

**Fallback 决策树**（按评审补充）：

```
NOVAIC_OTA_ENABLED 未启用? → 跳过 OTA，show() 本地
dev 模式? → 跳过 OTA，show() 本地
get_webview_window("main") 为 None? → 打 warning，尝试 show()（若后续可拿到）
GET /api/config/frontend 超时(6s)/失败/非 2xx? → fallback 本地，show()
frontend_url 为空或 JSON 解析失败? → fallback 本地，show()
URL 不在 remote.urls? → fallback 本地，show()，打 warning
navigate() 失败? → fallback 本地，show()
以上均通过 → navigate()，show()
```

**伪代码（修正版）**：

```rust
let did_navigate = if is_ota_enabled() {
    match fetch_frontend_url(&gw_url).await {
        Ok(url) if url_matches_remote_urls(&url) => {
            if let Some(w) = app.get_webview_window("main") {
                w.navigate(&url).ok().is_some()
            } else { false }
        }
        Ok(_) => { tracing::warn!("[OTA] URL not in remote.urls"); false }
        Err(e) => { tracing::warn!("[OTA] fetch failed: {}", e); false }
    }
} else { false };

if let Some(w) = app.get_webview_window("main") {
    let _ = w.show();
}
```

**fetch_frontend_url 实现**：

- 超时：`connect_timeout` 3s，整体 `timeout` 6s
- 错误分类：超时、非 2xx、JSON 解析失败、空 URL，分别打不同级别日志
- 使用 `serde_json` + `FrontendConfig` 结构体解析

---

### Phase 2：URL 与 capability 匹配校验

**实现方式**（二选一）：

| 方案 | 说明 |
|------|------|
| **A. urlpattern** | 与 Tauri capability 行为一致，需引入 `urlpattern` crate |
| **B. host 白名单** | 简单，常量 `ALLOWED_OTA_HOSTS: &[&str] = &["relay.gradievo.com", "api.gradievo.com"]` |

**匹配规则**（补充到文档）：

- **协议**：仅 `https://`
- **Host**：必须为 `relay.gradievo.com` 或 `api.gradievo.com`
- **路径**：无限制（`/*` 通配）
- **部署约束**：`FRONTEND_CDN_URL` 的 host 必须在 `remote.urls` 的 host 列表中

**配置来源**：建议从 `remote-frontend.json` 读取或与常量保持同步，避免重复定义。

---

### Phase 3：前端 __TAURI__ 检测与 fallback 提示

**执行时机**：在 `main.tsx` 中、`ReactDOM.createRoot().render()` **之前**，**同步**检测。

**检测条件**：仅当 `isOtaOrigin()` 且 `!('__TAURI__' in window)` 时渲染 Fallback。

**实现要点**：

```tsx
// main.tsx，在 render 之前；需 typeof window !== 'undefined' 防护
const OTA_ORIGINS = ['https://relay.gradievo.com', 'https://api.gradievo.com']; // 与 remote-frontend.json 同步
const needsTauri = typeof window !== 'undefined' &&
  OTA_ORIGINS.some(o => location.origin === o) && !('__TAURI__' in window);

ReactDOM.createRoot(root).render(
  needsTauri ? <TauriRequiredFallback /> : <App />
);
```

**OTA_ORIGINS 同步**：建议抽到 `src/config/index.ts`，加注释「与 remote-frontend.json remote.urls 的 host 必须一致」；或构建时从 JSON 生成。

**Fallback 组件**：使用 `nb-*` 设计 token（`bg-nb-bg`、`text-nb-text`）、`lucide-react` 图标、`env(safe-area-inset-*)` 适配移动端。注：React ErrorBoundary 只能捕获渲染/生命周期中的同步错误，**无法捕获** `useEffect` 中 invoke 的 Promise rejection；invoke 失败由各调用处的 try/catch 处理。

**Fallback 文案**：

- 主：`此页面需在 NovAIC App 内打开`
- 副：`请在手机或电脑上打开 NovAIC App 后访问此链接。若已在 App 中，请检查网络或重启 App。`

**前置修改**：`index.html` 中 favicon 需改为 `href="./icon.svg"`，否则 OTA base（如 `/resource/frontend/v0.3.0/`）下会 404。

---

### Phase 4：日志、常量与可维护性

**日志**：统一使用 `tracing`，格式 `[Frontend OTA] <action> <key=value>`。

| 级别 | 场景 |
|------|------|
| `info` | OTA 禁用、成功 navigate、空 URL fallback |
| `warn` | 超时、请求失败、JSON 错误、URL 不在白名单 |
| `debug` | 开始请求、dev 模式跳过 |

**常量**：提取 `ALLOWED_FRONTEND_HOSTS`、`OTA_TIMEOUT_SECS`、`OTA_CONNECT_TIMEOUT_SECS`。

**可选：frontend_url 缓存**：

- 格式：`{url}\n{version}\n{timestamp}`
- 失效：version 失效，或仅用于离线 fallback
- 有网络时始终请求 Gateway

---

## 四、任务清单（按依赖排序）

| # | 任务 | 产出 |
|---|------|------|
| 1 | `NOVAIC_OTA_ENABLED` 开关（支持 1/true/yes/on） | setup.rs |
| 2 | 恢复 `fetch_frontend_url` + `navigate` | setup.rs |
| 3 | URL 与 `remote.urls` 校验（host 白名单或 urlpattern） | setup.rs |
| 4 | 移动端 `show()` 逻辑补充 | setup.rs |
| 5 | 窗口创建时机验证（必要时轮询） | setup.rs |
| 6 | 日志与 fallback 完善 | setup.rs |
| 7 | 前端 `__TAURI__` 同步检测（main.tsx） | main.tsx |
| 8 | 前端 index.html favicon 改为 `./icon.svg` | index.html |
| 9 | 前端 TauriRequiredFallback 组件（nb-* token、safe-area） | 新组件 |
| 10 | 部署文档更新 | HANDOVER.md |
| 11 | 可选：frontend_url 缓存 | setup.rs |

---

## 五、remote.urls 与 frontend_url 匹配规则

| 规则 | 说明 |
|------|------|
| 协议 | 仅 `https` |
| Host | `relay.gradievo.com` 或 `api.gradievo.com` |
| 路径 | 无限制（`/*`） |
| 部署约束 | `FRONTEND_CDN_URL` 的 host 必须在 remote.urls 的 host 列表中 |

---

## 六、安全与配置

| 项目 | 说明 |
|------|------|
| 权限边界 | 由 `remote.urls` + `allow-app-commands` 定义 |
| Gateway 信任 | Gateway 为信任根，其返回的 `frontend_url` 决定可加载的远程前端 |
| CSP | 当前 `csp: null`，若未来启用需验证 OTA 与 invoke 兼容性 |
| 新命令 | 需同步更新 `allow-app-commands.toml` |

---

## 七、部署与运维

### 7.1 发布顺序（启用 OTA 后）

| 场景 | 推荐顺序 |
|------|----------|
| 仅前端热更新 | 1) deploy-frontend → 2) 更新 Gateway FRONTEND_CDN_URL → 3) 重启 Gateway |
| 全量发布 | 1) 前端到 Relay → 2) Gateway 更新并重启 → 3) Relay（若有变更）→ 4) App（若有变更）|

**原则**：先部署静态资源，再切换 Gateway 指向，避免 404。

### 7.2 回滚流程（CDN 前端有 bug 时）

1. SSH 登录 api.gradievo.com
2. 编辑 `/opt/novaic/jwt_secret.env`：将 `FRONTEND_CDN_URL` 改为旧版本 URL
3. 执行：`bash /opt/novaic/restart_gw.sh`
4. 验证：`curl -s https://api.gradievo.com/api/config/frontend | jq .frontend_url`
5. 用户下次启动 App 将加载旧版本前端

**约定**：部署新版本时，至少保留上一版本目录，不要删除。

### 7.3 运维检查清单

**发布前**：前端构建通过；`remote-frontend.json` 包含目标 CDN 域名；旧版本目录仍存在。

**发布中**：1) rsync 前端到 Relay；2) 验证 CDN 可访问；3) 更新 Gateway `FRONTEND_CDN_URL`；4) 重启 Gateway；5) 验证 `/api/config/frontend` 返回预期 URL。

**发布后**：桌面/手机 App 能加载 CDN 前端；invoke 正常；记录版本号便于回滚。

---

## 八、风险与缓解

| 风险 | 缓解 |
|------|------|
| `frontend_url` 不在 `remote.urls` | 校验拒绝 navigate，fallback 本地 |
| 混合内容（macOS/iOS） | Tauri 有 postMessage fallback；关注 #9266 JSON 响应 bug |
| Service Worker | 项目未使用；未来不要为 OTA 前端引入 SW |
| 窗口在 spawn 时未创建 | 验证时机，必要时轮询或 `on_window_created` |
| 移动端 show 缺失 | 任务 #4 明确补充 |

---

## 九、验收标准

1. `NOVAIC_OTA_ENABLED=1` 且 Gateway 返回 URL 在 `remote.urls` 内时，navigate 到 CDN，invoke 正常
2. 失败/超时/URL 不匹配时，fallback 本地，功能正常
3. 前端在 OTA origin 且 `__TAURI__` 缺失时，显示 Fallback 页面，不触发 invoke 错误
4. 移动端 OTA 成功/失败后窗口均正确显示

---

## 十、参考文档

- `docs/OTA_INVOKE_4_AGENT_REPORT.md`
- `docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md`（初稿）
- `docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_REVIEW.md`（5 名 Subagent 评审汇总）
- `docs/HOT_UPDATE_EXECUTION_PLAN.md`
- `novaic-gateway/main_gateway.py`（`/api/config/frontend`）
