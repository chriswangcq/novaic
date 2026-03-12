# OTA 热更新重新启用 — 实施方案（初稿）

> 基于 `docs/OTA_INVOKE_4_AGENT_REPORT.md` 调研结论，重新启用 OTA 并确保 invoke 可用

---

## 一、目标与范围

| 项目 | 说明 |
|------|------|
| **主目标** | 恢复 OTA 逻辑，使 App 启动时从 Gateway 获取 CDN URL 并 navigate 到远程前端；确保 invoke 在 OTA 场景下正常工作 |
| **平台** | 桌面 macOS + 移动端 iOS/Android |
| **原则** | 本地优先（失败时 fallback 本地）、URL 与 capability 严格匹配、可回滚 |

---

## 二、前置条件（已满足）

| 条件 | 状态 | 说明 |
|------|------|------|
| Gateway `/api/config/frontend` | ✅ | 已实现，返回 `frontend_url`、`version` |
| `FRONTEND_CDN_URL` 与 `remote.urls` 一致 | ✅ | 默认 `https://relay.gradievo.com/resource/frontend/v0.3.0/`，`remote-frontend.json` 已包含 `https://relay.gradievo.com/*` |
| `allow-app-commands` 白名单 | ✅ | 24 个命令已配置 |
| 前端部署到 relay | ✅ | `deploy-all.sh` 已部署到 `relay.gradievo.com` |

---

## 三、实施方案（Phase 1–4）

### Phase 1：恢复 OTA 核心逻辑（setup.rs）

**文件**：`novaic-app/src-tauri/src/setup.rs`

**任务**：恢复 `spawn_frontend_ota_task` 中的 Gateway 请求与 `navigate` 逻辑。

**实现要点**：
1. 读取环境变量 `NOVAIC_OTA_ENABLED`（默认 0/未设置 = 禁用，1 = 启用）
2. 若启用：`GET {gw_url}/api/config/frontend`，超时 6s
3. 成功且 `frontend_url` 非空：`main_window.navigate(frontend_url)`
4. 失败/超时/空：保持本地，不 navigate
5. 仅 release 构建执行；dev 模式跳过

**伪代码**：
```rust
if let Ok(1) = std::env::var("NOVAIC_OTA_ENABLED").as_deref().map(|s| s.parse::<u8>()) {
    if let Ok(url) = fetch_frontend_url(&gw_url).await {
        if let Some(w) = app.get_webview_window("main") {
            w.navigate(&url)?;
        }
    }
}
w.show();
```

---

### Phase 2：URL 与 capability 匹配校验

**目的**：确保 `frontend_url` 落在 `remote.urls` 范围内，避免 invoke 失败。

**实现要点**：
1. 在 `remote-frontend.json` 中维护 `remote.urls` 列表（当前：`relay.gradievo.com/*`、`api.gradievo.com/*`）
2. 在 setup 中：navigate 前校验 `frontend_url` 的 host 是否在允许列表内（或使用 URLPattern 校验）
3. 若不在范围内：**不 navigate**，fallback 本地，并打 warning 日志
4. 若在范围内：navigate，并打 info 日志（便于排查）

**可选**：将允许的 host 列表提取为常量或配置，避免硬编码。

---

### Phase 3：前端 __TAURI__ 检测与 fallback 提示

**目的**：用户打开 OTA 页面后，若 invoke 不可用（如 capability 未匹配），给出友好提示。

**实现要点**：
1. 前端在 `main.tsx` 或根组件 mount 时检测 `window.__TAURI__`
2. 若不存在：显示「当前环境不支持 Tauri 功能，请使用 NovAIC  App 打开」或类似
3. 若存在：正常渲染（不阻塞）

**可选**：仅在 OTA 页面（`location.origin` 为 relay/api）时检测，本地页面可跳过。

---

### Phase 4：日志与可观测性

**实现要点**：
1. 在 setup 中：打印 `frontend_url`、是否 navigate、是否 fallback 本地
2. 可选：将 `frontend_url` 写入 `data_dir/frontend_url_cache.txt`，下次离线时复用（需校验 URL 是否仍有效）
3. 部署文档中明确：`FRONTEND_CDN_URL` 必须落在 `remote.urls` 的域名范围内

---

## 四、任务清单（按优先级）

| # | 任务 | 负责人 | 产出 |
|---|------|--------|------|
| 1 | 恢复 `spawn_frontend_ota_task` 的 Gateway 请求 + navigate | - | setup.rs |
| 2 | 增加 `NOVAIC_OTA_ENABLED` 环境变量开关 | - | setup.rs |
| 3 | 增加 `frontend_url` 与 `remote.urls` 的匹配校验 | - | setup.rs |
| 4 | 前端 `__TAURI__` 检测与 fallback 提示 | - | main.tsx 或 App.tsx |
| 5 | 日志与 fallback 逻辑完善 | - | setup.rs |
| 6 | 可选：`frontend_url` 缓存 | - | setup.rs |
| 7 | 部署文档更新（`FRONTEND_CDN_URL` 与 `remote.urls` 一致） | - | HANDOVER.md |

---

## 五、风险与缓解

| 风险 | 缓解 |
|------|------|
| `frontend_url` 不在 `remote.urls` | 校验逻辑拒绝 navigate，fallback 本地 |
| 混合内容（macOS/iOS） | Tauri 有 postMessage fallback；若出现 JSON 响应 bug，可关注 Tauri 版本更新 |
| Service Worker 干扰 | 检查前端是否使用 SW，必要时禁用 |
| 网络超时 | 6s 超时，失败则本地 |

---

## 六、验收标准

1. 设置 `NOVAIC_OTA_ENABLED=1` 且 Gateway 返回 `frontend_url` 在 `remote.urls` 内时，App 启动后 navigate 到 CDN，invoke 可正常调用（登录、VNC、VM 等）
2. 失败/超时/URL 不匹配时，fallback 本地，功能正常
3. 前端在 `__TAURI__` 缺失时给出明确提示

---

## 七、参考文档

- `docs/OTA_INVOKE_4_AGENT_REPORT.md`
- `docs/HOT_UPDATE_EXECUTION_PLAN.md`
- `docs/OTA_FLOW_CAPABILITY_SWITCH.md`
- `novaic-gateway/main_gateway.py`（`/api/config/frontend`）
