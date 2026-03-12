# Hybrid Local First + 远程 URL 热更新 — 详细执行计划

> 基于 `docs/FRONTEND_HOT_UPDATE_SUMMARY.md` 与 `docs/REMOTE_URL_HOT_UPDATE_REPORT.json` 整理

---

## 一、目标与范围

| 目标 | 说明 |
|------|------|
| 主目标 | 实现前端 OTA 热更新：更新 CDN 即可生效，无需重新发布 App |
| 平台 | 桌面 macOS + 移动端 iOS/Android |
| 原则 | 本地优先、离线可用、支持版本回滚 |

---

## 二、阶段划分

```
Phase 1: 基础设施（Gateway API + CDN 部署）
    ↓
Phase 2: Tauri 客户端改造（setup + navigate + capabilities）
    ↓
Phase 3: 联调与验证
    ↓
Phase 4: 灰度与回滚机制
```

---

## 三、Phase 1：基础设施

### 3.1 Gateway 新增 `/api/config/frontend` 接口

**文件**：`novaic-gateway/main_gateway.py` 或新建 `gateway/api/config.py`

**接口设计**：

```
GET /api/config/frontend

Query（可选）：
  - app_version: 当前 App 版本（用于兼容性判断，可选）

Response 200：
{
  "frontend_url": "https://api.gradievo.com/static/v0.3.0/",
  "version": "0.3.0",
  "fallback_to_local": true,
  "min_app_version": "0.3.0"   // 可选：低于此版本强制用本地
}
```

**认证**：无需 JWT（App 启动时可能尚未登录），但建议限流防滥用。

**配置来源**（二选一或组合）：
- **方案 A**：环境变量 `FRONTEND_CDN_URL`、`FRONTEND_VERSION`
- **方案 B**：数据库 `config` 表新增 `frontend_url`、`frontend_version` 键
- **方案 C**：静态 JSON 文件 `{DATA_DIR}/frontend_config.json`

**推荐**：先用环境变量，便于部署时快速切换；后续可迁入 DB。

**任务清单**：

| # | 任务 | 负责人 | 产出 |
|---|------|--------|------|
| 1.1 | 新增 `GET /api/config/frontend` 路由 | - | `gateway/api/config.py` 或 main_gateway 内 |
| 1.2 | 实现配置读取逻辑（env / DB / JSON） | - | 可配置的 frontend_url、version |
| 1.3 | 在 `restart_gw.sh` 或 `jwt_secret.env` 中增加 `FRONTEND_CDN_URL` 示例 | - | 部署文档更新 |

---

### 3.2 前端构建产物部署到 CDN

**部署路径**：
- 主路径：`https://api.gradievo.com/static/{version}/`
- 或独立域名：`https://static.gradievo.com/novaic/{version}/`

**版本化规则**：
- 与 `tauri.conf.json` 的 `version` 或 `package.json` 的 `version` 对齐
- 例如：`0.3.0` → `/static/v0.3.0/` 或 `/static/0.3.0/`

**Nginx 配置**（api.gradievo.com）：

```nginx
# 在 novaic-cloud.conf 中增加
location /static/ {
    alias /opt/novaic/static/;   # 或 /var/www/novaic-static/
    add_header Cache-Control "public, max-age=3600";
    # 版本化路径可长期缓存
    location ~ ^/static/v[\d.]+/ {
        add_header Cache-Control "public, max-age=86400";
    }
}
```

**部署脚本**（建议新建 `novaic-app/scripts/deploy-frontend.sh`）：

```bash
#!/bin/bash
# 用法: ./scripts/deploy-frontend.sh [version]
# 1. npm run build
# 2. 将 dist/ 上传到服务器 /opt/novaic/static/v{version}/
# 3. 可选：更新 Gateway 的 frontend_config 指向新版本
```

**任务清单**：

| # | 任务 | 负责人 | 产出 |
|---|------|--------|------|
| 1.4 | 确定 CDN 路径与 Nginx 配置 | - | `novaic-cloud.conf` 更新 |
| 1.5 | 编写 `deploy-frontend.sh` 或 CI workflow | - | 一键部署脚本 |
| 1.6 | 首次部署：将当前 dist 上传到 `/static/v0.3.0/` | - | 可访问的 URL |

---

## 四、Phase 2：Tauri 客户端改造

### 4.1 修改 tauri.conf.json

**变更**：

```json
{
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "",
        "visible": false,
        "width": 1280,
        "height": 800,
        ...
      }
    ]
  }
}
```

**说明**：`visible: false` 使主窗口启动时隐藏，待 `navigate` 完成后再 `show()`，避免用户看到从本地到远程的闪烁。

---

### 4.2 配置 Tauri Capabilities（remote.urls）

**文件**：`novaic-app/src-tauri/capabilities/default.json`（若不存在则新建 `capabilities/` 目录）

**说明**：Tauri 2 使用 capabilities 控制权限。需为加载远程 URL 的窗口配置 `remote.urls`，否则 `window.__TAURI__` 不会注入，`invoke` 等 API 不可用。默认仅本地 bundled 前端可访问，远程页需显式放行。

**配置示例**（Tauri 2 支持 `remote: { urls: string[] }`）：

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "identifier": "main-window-capability",
  "windows": ["main"],
  "remote": {
    "urls": [
      "https://api.gradievo.com/*",
      "https://static.gradievo.com/*"
    ]
  },
  "permissions": [
    "core:default",
    "dialog:default",
    "fs:default",
    "os:default",
    "process:default",
    "shell:default",
    "gateway:*",
    "config:*",
    "auth:*",
    "file:*",
    "vnc_urls:*"
  ]
}
```

**任务**：查阅 Tauri 2 文档确认 `remote.urls` 的配置方式（可能在 `tauri.conf.json` 的 `app.security` 或独立 capabilities 文件）。

---

### 4.3 Rust：setup 中请求 Gateway 并 navigate

**修改文件**：
- `novaic-app/src-tauri/src/lib.rs`（桌面 setup 逻辑）
- `novaic-app/src-tauri/src/mobile.rs`（移动端 setup，复用或调用共享逻辑）

**逻辑流程**：

```
1. setup_shared() 完成后，获取 gw_url、cloud_token（可选）
2. spawn 异步任务：
   a. 请求 GET {gw_url}/api/config/frontend，超时 3–5s
   b. 若成功且 frontend_url 非空：
      - main_window.navigate(frontend_url)
      - 可选：将 frontend_url 写入 data_dir 缓存，下次离线时复用
   c. 若超时或失败：
      - 保持当前页面（本地 asset）
3. main_window.show()
```

**实现要点**：
- 使用 `reqwest` 请求 Gateway（已有依赖）
- 桌面与移动端均需执行此逻辑
- 开发模式（`devUrl`）下**跳过**此逻辑，直接加载 dev server

**伪代码**：

```rust
// 在 setup 中，setup_shared 之后
let gw_url = app.state::<GatewayUrlState>().inner().clone();
let main_window = app.get_webview_window("main").expect("main window");

tauri::async_runtime::spawn(async move {
    let url = format!("{}/api/config/frontend", gw_url.trim_end_matches('/'));
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .ok()?;
    let resp = client.get(&url).send().await.ok()?;
    let json: serde_json::Value = resp.json().await.ok()?;
    let frontend_url = json.get("frontend_url")?.as_str()?;
    if !frontend_url.is_empty() {
        let _ = main_window.navigate(frontend_url);
    }
    let _ = main_window.show();
});
```

**注意**：需在 `setup` 同步阶段 spawn，且 `show()` 必须在 navigate 之后调用；若采用「先 show 再 navigate」，则会有短暂白屏。

**任务清单**：

| # | 任务 | 负责人 | 产出 |
|---|------|--------|------|
| 2.1 | 在 lib.rs 桌面 setup 中增加 frontend 拉取 + navigate 逻辑 | - | 桌面端支持 |
| 2.2 | 在 mobile.rs 或 setup_shared 中增加相同逻辑（移动端） | - | 移动端支持 |
| 2.3 | 开发模式（devUrl）下跳过 navigate，直接 show | - | 不影响 tauri dev |
| 2.4 | 超时与错误处理：失败时保持本地并 show | - | 离线可用 |

---

### 4.4 前端 base 与 API 路径

**问题**：前端部署到 `https://api.gradievo.com/static/v0.3.0/` 时，相对路径 `/api` 会变成 `https://api.gradievo.com/api`，与 Gateway 一致，通常无需改动。

**需确认**：
- Vite `base`：若为 `'/static/v0.3.0/'`，则资源路径正确
- 前端 `gateway_get` 等调用的 base URL：应使用 `invoke('get_gateway_url')`，与当前一致

**任务**：验证 `npm run build` 后，`dist/index.html` 内脚本路径、API 请求 base 是否正确。

---

## 五、Phase 3：联调与验证

### 5.1 验证矩阵

| 场景 | 预期行为 | 验证方法 |
|------|----------|----------|
| 有网 + Gateway 正常 | 加载远程 URL，显示最新前端 | 改 CDN 内容，重启 App 可见 |
| 有网 + Gateway 超时 | 使用本地 asset | 断 Gateway 或 mock 超时 |
| 无网 | 使用本地 asset | 断网启动 |
| 开发模式 tauri dev | 加载 localhost:1420，不 navigate | 改代码热更新正常 |
| 远程页 invoke | 可调用 get_gateway_url、gateway_get 等 | 检查 capabilities |

### 5.2 测试清单

- [ ] Gateway `/api/config/frontend` 返回正确 JSON
- [ ] 桌面 macOS：有网时加载 CDN，无网时本地
- [ ] iOS 真机：同上
- [ ] Android 真机：同上
- [ ] 远程页可正常调用 Tauri 命令
- [ ] 登录、SSE、消息发送等核心流程正常

---

## 六、Phase 4：灰度与回滚

### 6.1 版本回滚

**Gateway 配置**：
- 支持 `FRONTEND_VERSION` 或 DB 配置，指向旧版本路径如 `/static/v0.3.0/`
- 出问题时，改配置并重启 Gateway，所有新启动的 App 即回滚

**客户端缓存**（可选）：
- 将上次成功的 `frontend_url` 存 `data_dir/frontend_url_cache.txt`
- 当 Gateway 请求失败时，尝试加载缓存的 URL（若仍可达）

### 6.2 灰度发布

- Gateway 可按 `app_version` 或 `user_id` 返回不同 `frontend_url`
- 初期可先对所有用户返回同一 URL，稳定后再扩展

---

## 七、文件变更清单

| 仓库 | 文件 | 变更类型 |
|------|------|----------|
| novaic-gateway | `gateway/api/config.py` 或 main_gateway | 新增 `/api/config/frontend` |
| novaic-gateway | `nginx/novaic-cloud.conf` | 新增 `/static/` location |
| novaic-gateway | `scripts/jwt_secret.env.example` | 新增 `FRONTEND_CDN_URL` 示例 |
| novaic-app | `src-tauri/tauri.conf.json` | `visible: false` |
| novaic-app | `src-tauri/capabilities/*.json` | 新增 `remote.urls` |
| novaic-app | `src-tauri/src/lib.rs` | setup 中 frontend 拉取 + navigate |
| novaic-app | `src-tauri/src/mobile.rs` | 同上（或复用） |
| novaic-app | `vite.config.ts` | 可选：`base: '/static/v' + version + '/'` |
| novaic-app | `scripts/deploy-frontend.sh` | 新增部署脚本 |

---

## 八、风险与缓解

| 风险 | 缓解 |
|------|------|
| 远程页无法调用 Tauri | 确保 capabilities 的 `remote.urls` 包含 CDN 域名 |
| CSP 阻止脚本 | 先 `csp: null` 验证，再按需收紧 |
| 启动延迟 | 超时 3–5s，失败即用本地，不阻塞 |
| 版本不一致 | Gateway 返回版本化 URL，便于回滚 |

---

## 九、时间估算

| Phase | 预估工时 | 依赖 |
|-------|----------|------|
| Phase 1 | 1–2 天 | 无 |
| Phase 2 | 2–3 天 | Phase 1 |
| Phase 3 | 1 天 | Phase 2 |
| Phase 4 | 0.5 天 | Phase 3 |

**总计**：约 5–7 人天

---

## 十、参考文档

- `docs/FRONTEND_HOT_UPDATE_SUMMARY.md`
- `docs/REMOTE_URL_HOT_UPDATE_REPORT.json`
- `docs/MOBILE_HOT_UPDATE_LIMITS_REPORT.json`
- [Tauri 2 Remote URL / Capabilities](https://v2.tauri.app/)
- `HANDOVER.md` — Gateway 部署、Nginx 配置
