# OTA 变更 — 4 名资深前端 Subagent 挑刺 Review 汇总

> 对照方案 `OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md`、`OTA_V2_FRONTEND_3_AGENT_SUMMARY.md` 的逐项评审

---

## 一、问题汇总（按严重程度）

### 高

| # | 问题 | 来源 | 建议 |
|---|------|------|------|
| 1 | **HANDOVER 未说明 NOVAIC_OTA_ENABLED 启用方式** | Subagent 4 | 补充 OTA 开关：默认关闭，需设置 `NOVAIC_OTA_ENABLED=1` 才启用 |
| 2 | **HANDOVER 未说明 OTA 三处同步规则** | Subagent 2, 4 | 补充：config 的 OTA_ORIGINS、remote-frontend.json 的 remote.urls、setup.rs 的 OTA_ALLOWED_HOSTS 需同步 |
| 3 | **三处同步无 CI 校验** | Subagent 2, 3, 4 | 增加 CI 脚本校验 config / remote-frontend / setup 一致性 |
| 4 | **setup.rs 未对 main 窗口创建做轮询/等待** | Subagent 3 | 若 OTA 任务在窗口创建前执行，get_webview_window 可能为 None；建议轮询或 on_window_created 等待 |
| 5 | **方案中「AppErrorBoundary 捕获 invoke 失败」描述不准确** | Subagent 2, 3 | ErrorBoundary 无法捕获 useEffect 中的 Promise rejection；invoke 失败由 try/catch 处理；需更正文档 |

### 中

| # | 问题 | 来源 | 建议 |
|---|------|------|------|
| 6 | **缺少 console.info('[OTA] TauriRequiredFallback', { origin })** | Subagent 1, 2, 3, 4 | 在 TauriRequiredFallback 中增加可观测性日志 |
| 7 | **location.origin 与显式 :443 不匹配** | Subagent 1 | `https://relay.gradievo.com:443` 与 `https://relay.gradievo.com` 不匹配；文档明确或规范化 |
| 8 | **__TAURI__ 的 TypeScript 类型** | Subagent 1 | 使用 `(window as Window & { __TAURI__?: unknown })` 或扩展 Window 接口 |
| 9 | **TauriRequiredFallback 无 a11y** | Subagent 2 | 增加 role="alert"、aria-label、aria-live、图标 aria-hidden |
| 10 | **vite.config VITE_BASE 注释不准确** | Subagent 4 | 改为 `/resource/frontend/v0.3.0/` 示例 |

### 低

| # | 问题 | 来源 | 建议 |
|---|------|------|------|
| 11 | **sessionStorage.novaic_ota_debug 调试开关未实现** | Subagent 1, 4 | 可选，便于调试 |
| 12 | **#root 非空断言风险** | Subagent 1 | 增加防御性检查 |
| 13 | **缺少单元测试** | Subagent 1, 4 | 为 shouldShowTauriFallback 补充测试 |
| 14 | **缺少下载链接预留** | Subagent 2 | `{/* TODO: App Store / TestFlight */}` |
| 15 | **无多语言预留** | Subagent 2 | 若后续支持 i18n，可预留文案 key |

---

## 二、已正确实现的部分（4 名 Subagent 共识）

- index.html favicon 已改为 `./icon.svg` ✅
- `__TAURI__` 检测在 render 之前同步执行 ✅
- `needsTauriFallback` 分支渲染，不挂载 App 时不会触发 invoke ✅
- OTA_ORIGINS 已抽到 config 并加注释 ✅
- `typeof window !== 'undefined'` 防护 ✅
- TauriRequiredFallback 使用 nb-* token、AlertTriangle、safe-area ✅
- App 已通过 AppWithErrorBoundary 包裹 ✅
- setup.rs 中 NOVAIC_OTA_ENABLED、fetch_frontend_url、host 白名单已实现 ✅
- import 顺序与模块加载无 invoke 副作用 ✅
- 刷新与深层路径检测逻辑正确 ✅

---

## 三、Subagent 分工与结论

| Subagent | 重点 | 核心发现 |
|----------|------|----------|
| **1. main.tsx 与入口检测** | 检测逻辑、边界、类型 | 调试开关未实现；:443 不匹配；__TAURI__ 类型；#root 断言 |
| **2. TauriRequiredFallback 与 config** | 组件、OTA_ORIGINS、index | CI 未校验；a11y 缺失；可观测性日志缺失；AppErrorBoundary 误解 |
| **3. 调用链与 invoke 边界** | 竞态、import、ErrorBoundary | 无竞态；setup 窗口创建时机未等待；ErrorBoundary 无法捕获 invoke |
| **4. 可观测性、文档、运维** | 日志、调试、HANDOVER | 日志未实现；HANDOVER 缺 OTA 开关与同步规则；三处同步无校验 |

---

## 四、优先修改建议（客观听取）

### 建议立即处理（高）

1. **HANDOVER.md**：补充 NOVAIC_OTA_ENABLED 启用方式、OTA 三处同步规则
2. **setup.rs**：增加对 main 窗口的轮询或 on_window_created 等待（若 Tauri 窗口创建晚于 OTA 任务）
3. **方案文档**：更正「AppErrorBoundary 捕获 invoke 失败」描述，明确 ErrorBoundary 与 try/catch 分工

### 建议短期处理（中）

4. **TauriRequiredFallback**：增加 `console.info('[OTA] TauriRequiredFallback', { origin })`
5. **TauriRequiredFallback**：增加 a11y（role、aria-label、aria-hidden）
6. **main.tsx**：为 `__TAURI__` 补充 TypeScript 类型
7. **CI**：增加 OTA_ORIGINS 与 remote-frontend.json、setup.rs 的校验脚本

### 建议可选处理（低）

8. **main.tsx**：实现 sessionStorage.novaic_ota_debug 调试开关
9. **main.tsx**：#root 防御性检查
10. **单元测试**：shouldShowTauriFallback

---

## 五、需澄清或验证的点

| 点 | 说明 |
|----|------|
| **窗口创建时机** | Tauri 2 中 setup_shared 与主窗口创建的时序：若 spawn 时窗口已存在，则无需轮询；需在目标平台验证 |
| **:443 匹配** | 实际 OTA URL 是否可能带显式 :443？若仅标准 HTTPS，可文档明确，暂不实现规范化 |
| **CI 校验** | 校验脚本需解析 TS 与 JSON，可用 Node 或 shell；实现成本与收益需权衡 |
