# OTA 实施方案 V2 — 3 名资深前端 Subagent 评审汇总

> 针对 `docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md` 的前端专项评审

---

## 一、评审分工与结论

| Subagent | 重点 | 核心发现 |
|----------|------|----------|
| **1. 入口与 __TAURI__ 检测** | main.tsx、OTA_ORIGINS、Fallback UX | 侵入性低；OTA_ORIGINS 需与 remote.urls 同步（建议抽到 config 或构建生成）；需 `typeof window !== 'undefined'` 防护 |
| **2. 构建、路由与 invoke** | Vite base、调用链、路由 | **index.html favicon 用 `/icon.svg` 在 OTA base 下 404**，需改为 `./icon.svg`；invoke 均在 useEffect 中，render 前检测可完全避免 |
| **3. Fallback UI、错误边界** | 设计系统、Error Boundary、可观测性 | 使用 `nb-*` token 与现有风格一致；需区分「无 __TAURI__」与「有 __TAURI__ 但 invoke 失败」；移动端需 `env(safe-area-inset-*)` |

---

## 二、必须修改项（3 名 Subagent 共识）

| # | 修改 | 文件 | 说明 |
|---|------|------|------|
| 1 | favicon 路径 | `index.html` | `href="/icon.svg"` → `href="./icon.svg"`，否则 OTA base 下 404 |
| 2 | __TAURI__ 检测 | `main.tsx` | 在 `ReactDOM.render` 之前同步检测，条件满足时渲染 `TauriRequiredFallback` |
| 3 | OTA_ORIGINS 抽离 | `src/config/index.ts` | 集中维护，加注释「与 remote-frontend.json 同步」；或构建时从 JSON 生成 |
| 4 | window 防护 | `main.tsx` | `typeof window !== 'undefined'` 避免 SSR/测试环境报错 |

---

## 三、OTA_ORIGINS 与 remote.urls 同步方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| **A. 构建时生成** | 单一数据源，自动同步 | 需增加构建脚本 |
| **B. import JSON** | 无需脚本 | 前端依赖 Tauri 配置，路径需调整 |
| **C. config 常量 + 文档** | 实现简单 | 需人工同步，建议 CI 校验 |

**推荐**：短期用 **方案 C**，在 `src/config/index.ts` 定义 `OTA_ORIGINS`，文档中写明与 `remote-frontend.json` 的同步规则；中长期可引入方案 A。

---

## 四、TauriRequiredFallback 组件规范

| 项目 | 建议 |
|------|------|
| **设计 token** | `bg-nb-bg`、`text-nb-text`、`text-nb-text-secondary`、`border-nb-border` |
| **图标** | `lucide-react` 的 `AlertTriangle` 或 `Smartphone`，与 initTimeout、AppErrorBoundary 一致 |
| **布局** | `min-h-screen flex flex-col items-center justify-center p-4 sm:p-6` |
| **安全区域** | 移动端使用 `env(safe-area-inset-*)` 作为 padding |
| **文案** | 主：`此页面需在 NovAIC App 内打开`；副：`请在手机或电脑上打开 NovAIC App 后访问此链接。若已在 App 中，请检查网络或重启 App。` |
| **下载链接** | 若有 App Store/TestFlight 链接可加入；若无则预留 `{/* TODO */}` |

---

## 五、错误边界与可观测性

| 场景 | 处理 |
|------|------|
| **无 __TAURI__** | 渲染 `TauriRequiredFallback`（入口检测） |
| **有 __TAURI__ 但 invoke 失败** | 用 `AppErrorBoundary` 包裹 `App`，捕获 invoke 抛错 |
| **可观测性** | `console.info('[OTA] TauriRequiredFallback', { origin })`；可选 invoke wrapper 记录失败 |
| **调试** | `sessionStorage.novaic_ota_debug=1` 时输出 `__TAURI__`、`isOtaOrigin` 等 |

---

## 六、invoke 调用链确认

**结论**：所有 invoke 均在 `useEffect` 或用户操作中触发，**模块加载阶段无 invoke**。

| 触发点 | invoke 命令 |
|--------|-------------|
| `restoreSession` | `get_gateway_url`、`set_gateway_url`、`update_cloud_token` |
| `secureGet` | `secure_storage_get` |
| `connectUserStream` | `gateway_sse_connect`、`listen` |
| `loadAgents` | `gateway_get` |

当 `needsTauriFallback` 为 true 时只渲染 Fallback，不渲染 App，**不会执行任何 invoke**。

---

## 七、路由与深层路径

- 项目未使用 React Router，由内部 state 控制
- 检测基于 `location.origin`，不依赖 `pathname`
- 任意深层路径（如 `/resource/frontend/v0.3.0/agents/xxx`）只要 origin 匹配，检测逻辑均正确

---

## 八、实施清单（前端部分）

| # | 任务 | 产出 |
|---|------|------|
| 1 | index.html favicon 改为 `./icon.svg` | index.html |
| 2 | main.tsx 增加 __TAURI__ + OTA origin 检测 | main.tsx |
| 3 | OTA_ORIGINS 抽到 config，加同步说明 | src/config/index.ts |
| 4 | 新建 TauriRequiredFallback 组件 | 新组件 |
| 5 | Fallback 用 AppErrorBoundary 包裹 App（OTA 分支） | main.tsx |
| 6 | 检测逻辑加 `typeof window !== 'undefined'` | main.tsx |
| 7 | 可选：构建脚本从 remote-frontend.json 生成 OTA_ORIGINS | 构建脚本 |

---

## 九、参考文档

- `docs/OTA_V2_FRONTEND_REVIEW.md`（Subagent 2 详细报告）
- `docs/OTA_RE_ENABLE_FRONTEND_REVIEW.md`（Subagent 3 详细报告）
- Subagent 1 报告（内嵌在 agent 输出中）
