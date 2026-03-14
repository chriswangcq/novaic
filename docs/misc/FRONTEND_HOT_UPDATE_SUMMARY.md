# NovAIC 前端热更新方案汇总

> 由 5 名 subagent 从不同角度探索后汇总，2026-03-11

---

## 一、探索范围与结论概览

| 维度 | 负责人 | 核心结论 |
|------|--------|----------|
| **开发环境 HMR** | Agent 1 | 桌面端已工作；移动端真机需配置 `server.hmr` |
| **Tauri OTA 插件** | Agent 2 | 官方 updater 全量更新；CrabNebula 仅前端，但依赖其云服务 |
| **资源加载架构** | Agent 3 | 支持 `frontendDist` 远程 URL；可改为 CDN 加载实现热更新 |
| **移动端限制** | Agent 4 | Tauri updater 在 iOS/Android 未实现；WebView 远程加载合规 |
| **远程 URL 方案** | Agent 5 | 推荐 hybrid_local_first：本地优先 + Gateway 配置 + navigate |

---

## 二、开发环境热更新（HMR）

### 当前状态

- **Vite**：`@vitejs/plugin-react` 已启用，默认提供 React Fast Refresh
- **Tauri dev**：`beforeDevCommand: "npm run dev"` + `devUrl: "http://localhost:1420"`
- **流程**：`tauri dev` 启动 Vite → WebView 加载 localhost:1420 → HMR WebSocket 同源连接

### 已生效

- **桌面端**：改 `novaic-app/src/components/` 后热更新即时生效（HANDOVER.md 已说明）
- **入口**：`index.html` + `main.tsx` 符合 Vite 标准，无需额外配置

### 限制与优化

| 场景 | 问题 | 建议 |
|------|------|------|
| 移动端真机调试 | HMR WebSocket 可能连错 host | 根据 `TAURI_DEV_HOST` 配置 `server.hmr` |
| Vite 监听 | 默认不监听 node_modules | 依赖变更后需重启 dev server |
| Tauri 侧逻辑 | HMR 全页重载可能重复执行 tray 等 | 监听 `vite:beforeUpdate` 做清理 |

### 推荐配置（移动端真机）

```ts
// vite.config.ts
server: {
  host: process.env.TAURI_DEV_HOST || undefined,
  hmr: process.env.TAURI_DEV_HOST
    ? { host: process.env.TAURI_DEV_HOST, port: 1420 }
    : undefined,
}
```

---

## 三、生产环境热更新方案对比

### 方案 A：Tauri 官方 Updater（全量应用更新）

| 项目 | 说明 |
|------|------|
| 更新范围 | 完整二进制（Rust + 前端） |
| 平台 | macOS ✅ / Windows ✅ / Linux ✅ / iOS ⚠️ / Android ⚠️ |
| 分发 | 自托管 JSON 或动态服务器 |
| 配置 | `createUpdaterArtifacts: true` + 签名密钥 + endpoints |
| 流程 | `check()` → `downloadAndInstall()` → `relaunch()` |

**注意**：Tauri 官方 updater 在 iOS/Android 上**尚未实现**（PR #1120），`check()` 会报错，需用 `#[cfg(desktop)]` 排除。

### 方案 B：CrabNebula OTA Updater（仅前端）

| 项目 | 说明 |
|------|------|
| 更新范围 | 仅 Web 资源（HTML/JS/CSS） |
| 分发 | **必须**使用 CrabNebula Cloud |
| 许可 | PolyForm-Noncommercial-1.0.0（商业使用需确认） |
| 流程 | `check()` → `update.apply()` → `location.reload()` |

### 方案 C：WebView 远程加载（推荐）

| 项目 | 说明 |
|------|------|
| 更新范围 | 仅前端，CDN 部署后即生效 |
| 合规 | iOS 3.3.2、Google Play 均允许 WebView 中的 JS OTA |
| 实现 | 本地优先 + Gateway 返回 `frontend_url` + `navigate()` |
| 离线 | 保留本地 dist 作为 fallback |

---

## 四、推荐方案：Hybrid Local First + 远程 URL

### 架构

```
App 启动
  → 主窗口加载本地 index.html（或极简 loading）
  → setup 中 spawn 异步请求 Gateway: GET /api/config/frontend
  → 成功：main_window.navigate(remote_url)
  → 超时/失败：保持本地 asset
  → window.show()
```

### Gateway API

```
GET {gateway_url}/api/config/frontend

Response:
{
  "frontend_url": "https://api.gradievo.com/static/v1.2.3/",
  "version": "1.2.3",
  "fallback_to_local": true
}
```

### 前端部署

- **路径**：`api.gradievo.com/static/` 或 `static.gradievo.com`
- **版本化**：`/static/v1.2.3/` 便于回滚
- **CI**：`npm run build` 后上传 dist 到 CDN

### Tauri 配置

1. **tauri.conf.json**：`frontendDist: "../dist"` 保持本地 fallback
2. **capabilities**：`remote.urls` 允许 CDN 域名（否则远程页无法用 `invoke`）
3. **Rust setup**：请求 Gateway → `navigate()` 或保持本地

### 风险与缓解

| 风险 | 缓解 |
|------|------|
| CSP 阻止远程脚本 | 放行 CDN、`ipc.localhost`；或先 `csp: null` 调试 |
| 离线无法加载 | 保留本地 dist，超时后 fallback |
| 版本回滚 | Gateway 返回版本化 URL，支持配置强制版本 |
| `__TAURI__` 注入 | capabilities 中 `remote.urls` 显式允许 CDN |

---

## 五、移动端专项说明

### 政策合规

- **iOS**：3.3.2 允许解释型代码（JS）OTA，前提是不改变主要用途、不建应用商店
- **Android**：明确允许 WebView 中的 JS 更新

### Tauri Updater 现状

- 官方文档列出 iOS/Android 支持，但**实际未实现**
- 移动端调用 `check()` 会报错
- **建议**：用 `#[cfg(desktop)]` 或 feature flag 排除；移动端采用 WebView 远程加载

### 替代方案

| 方案 | 说明 |
|------|------|
| WebView 远程加载 | 主窗口加载 `https://cdn.example.com/app/`，合规且实现简单 |
| 版本检查 + 商店跳转 | REST API 检查版本，有新版本时 `shell.open()` 打开 App Store / Play Store |
| 混合模式 | 本地壳 + 远程拉取 JS 包，首屏快、可 OTA |

---

## 六、实施路线图

### Phase 1：开发环境优化（低风险）

- [ ] 移动端真机：vite.config.ts 增加 `TAURI_DEV_HOST` 下的 `server.hmr` 配置
- [ ] 可选：`import.meta.hot.on('vite:beforeUpdate', ...)` 清理 Tauri 侧逻辑

### Phase 2：Gateway 前端配置 API（中风险）

- [ ] Gateway 新增 `GET /api/config/frontend`，返回 `frontend_url`、`version`
- [ ] 前端 CI 部署到 CDN（如 `api.gradievo.com/static/v{x.y.z}/`）

### Phase 3：Tauri 远程加载（中风险）

- [ ] setup 中请求 Gateway，成功则 `navigate(remote_url)`
- [ ] capabilities 配置 `remote.urls` 允许 CDN
- [ ] 超时（3–5s）fallback 本地

### Phase 4：桌面端官方 Updater（可选）

- [ ] `tauri add updater`，配置签名与 endpoints
- [ ] 用于 Rust 或全量更新，与前端 OTA 互补

---

## 七、相关文档

| 文档 | 说明 |
|------|------|
| `docs/HMR_DEV_REPORT.json` | 开发环境 HMR 详细报告 |
| `docs/TAURI2_OTA_UPDATER_REPORT.json` | Tauri OTA 插件对比 |
| `docs/MOBILE_HOT_UPDATE_LIMITS_REPORT.json` | 移动端政策与限制 |
| `docs/REMOTE_URL_HOT_UPDATE_REPORT.json` | 远程 URL 方案细节 |
| `HANDOVER.md` | 项目交接文档 |
