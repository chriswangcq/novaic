# OTA 实施方案 V2 — 前端专项评审

> 评审重点：Fallback UI、错误边界与可观测性、移动端 WebView

---

## 一、TauriRequiredFallback 组件设计

### 1.1 与现有设计系统的一致性

**现状**：项目已有 `tailwind.config.js` 定义 `nb-*` 设计 token，以及 `index.css` 中的基础样式（字体、滚动条、动画）。

**建议**：`TauriRequiredFallback` 必须与设计系统完全一致，避免「白屏/黑屏」或风格割裂。

| 项目 | 建议 |
|------|------|
| **背景** | `bg-nb-bg`（`#0d1117`），与 App 主背景一致 |
| **卡片/容器** | `bg-nb-surface border border-nb-border rounded-2xl`，与 AuthPage、initTimeout 错误页一致 |
| **主文案** | `text-nb-text` |
| **副文案** | `text-nb-text-secondary` 或 `text-nb-text-muted` |
| **图标** | 使用 `lucide-react`（如 `AlertTriangle`、`Smartphone`），与 AppErrorBoundary、initTimeout 一致 |
| **按钮/链接** | `btn-secondary` 或 `bg-nb-surface-2 hover:bg-nb-surface-hover`，与现有 `.btn` 风格统一 |

**参考现有实现**：

```tsx
// App.tsx initTimeout 错误页（第 376-392 行）
<div className="h-screen flex flex-col items-center justify-center bg-nb-bg gap-4">
  <AlertTriangle size={40} className="text-nb-warning" />
  <p className="text-nb-text text-center max-w-sm">...</p>
  <button className="... bg-nb-surface hover:bg-nb-surface-2 ...">重试</button>
</div>
```

### 1.2 响应式设计

**建议**：OTA Fallback 页面需适配桌面与移动端。

| 场景 | 建议 |
|------|------|
| **桌面** | 居中卡片，`max-w-md`，与 AuthPage 类似 |
| **移动端** | 全屏居中，`p-4` 或 `p-6`，避免内容贴边；文案 `text-sm` 或 `text-base` 可读 |
| **窄屏** | 使用 `min-h-screen` + `flex flex-col items-center justify-center`，与 `index.html` 的 `#preload-fallback` 布局一致 |

**示例结构**：

```tsx
<div className="min-h-screen flex flex-col items-center justify-center bg-nb-bg p-4 sm:p-6">
  <div className="w-full max-w-md ...">
    {/* 主文案、副文案、可选操作 */}
  </div>
</div>
```

### 1.3 多语言支持

**现状**：项目无 i18n 库（如 react-i18next），`STORAGE_KEYS.LOCALE` 存在但未使用；AuthPage、initTimeout 等均为中文。

**建议**：

- **短期**：与现有页面保持一致，使用中文文案即可，无需引入 i18n。
- **中期**：若项目计划多语言，可将 Fallback 文案抽到 `config` 或常量，便于后续接入 i18n。

**文案建议**（与文档 Phase 3 一致，可微调）：

- 主：`当前环境不支持 Tauri 功能，请使用 NovAIC App 打开此页面。`
- 副：`若您已在 App 中打开，请检查网络或尝试重新启动 App。`

---

## 二、错误边界

### 2.1 现状

- **AppErrorBoundary**：已存在，包裹整个 `App`，捕获 React 渲染/生命周期错误，展示「Something went wrong」+ 重试。
- **OTA 场景**：文档仅描述「`__TAURI__` 缺失时渲染 Fallback」，未覆盖「有 `__TAURI__` 但 invoke 偶发失败」的情况。

### 2.2 需区分的场景

| 场景 | 检测条件 | 建议处理 |
|------|----------|----------|
| **A. 完全无 __TAURI__** | `!('__TAURI__' in window)` | 文档已覆盖：渲染 `TauriRequiredFallback`（浏览器直接打开 OTA URL） |
| **B. 有 __TAURI__ 但 invoke 失败** | `__TAURI__` 存在，但 `invoke()` 抛错（capability 未匹配、网络、超时等） | **需补充**：由 Error Boundary 兜底，或业务层统一捕获并展示友好提示 |

### 2.3 建议方案

**方案 A（推荐）**：在 `main.tsx` 的 `render` 分支中，将 `App` 包裹在 `AppErrorBoundary` 内，确保 OTA 页面加载后 invoke 失败导致的 React 错误能被捕获：

```tsx
// main.tsx
const needsTauri = OTA_ORIGINS.some(o => location.origin === o) && !('__TAURI__' in window);

ReactDOM.createRoot(root).render(
  needsTauri ? (
    <TauriRequiredFallback />
  ) : (
    <React.StrictMode>
      <AppErrorBoundary>
        <App />
      </AppErrorBoundary>
    </React.StrictMode>
  )
);
```

**注意**：当前 `AppErrorBoundary` 在 `App.tsx` 内，需将 `AppErrorBoundary` 提取到独立文件或在 `main.tsx` 中复用，以便在 OTA 分支也能包裹 `App`。

**方案 B**：在 invoke 调用密集处（如 `vm.ts`、`auth` 恢复逻辑）增加 try-catch，失败时设置全局错误状态，由顶层组件展示「Tauri 调用失败，请重试」类 UI。可与方案 A 并存。

### 2.4 错误边界文案差异化（可选）

若希望区分「无 Tauri」与「有 Tauri 但失败」：

| 场景 | 主文案 | 副文案 |
|------|--------|--------|
| 无 __TAURI__ | 当前环境不支持 Tauri 功能，请使用 NovAIC App 打开此页面 | 若您已在 App 中打开，请检查网络或尝试重新启动 App |
| 有 __TAURI__ 但 invoke 失败 | Tauri 功能暂时不可用 | 请检查网络或重新启动 App 后重试 |

可通过 `AppErrorBoundary` 的 `error` 信息判断是否为 invoke 相关（如 `error.message` 含 `invoke`、`Permission denied` 等），动态选择文案。

---

## 三、可观测性

### 3.1 现状

- 后端：`tracing` 日志，格式 `[Frontend OTA] <action> <key=value>`。
- 前端：无专门 OTA 状态上报；`console.log`/`console.warn` 分散在 `App.tsx`、`vm.ts` 等。

### 3.2 建议：前端 OTA 可观测性

| 项目 | 建议 |
|------|------|
| **OTA 加载状态** | 在 `main.tsx` 检测到 `needsTauri` 时，`console.info('[OTA] TauriRequiredFallback rendered', { origin: location.origin })` |
| **invoke 失败率** | 可选：封装 `invoke` 的 wrapper，在 catch 中 `console.warn('[OTA] invoke failed', { cmd, error })`；或通过 Tauri 的 `invoke` 错误事件上报（若后端支持） |
| **开发环境** | `import.meta.env.DEV` 时输出更详细日志，如 `__TAURI__` 检测结果、`location.origin` |
| **生产环境** | 仅 `console.info` 关键节点（如 Fallback 展示），避免刷屏 |

### 3.3 控制台调试信息规范

建议在 `main.tsx` 增加：

```ts
// 开发环境或需要排查时输出
if (import.meta.env.DEV || sessionStorage.getItem('novaic_ota_debug') === '1') {
  const hasTauri = '__TAURI__' in window;
  const isOtaOrigin = OTA_ORIGINS.some(o => location.origin === o);
  console.debug('[OTA] env', {
    hasTauri,
    isOtaOrigin,
    origin: location.origin,
    willShowFallback: isOtaOrigin && !hasTauri,
  });
}
```

用户可通过 `sessionStorage.setItem('novaic_ota_debug', '1')` 开启调试输出。

### 3.4 可选：上报到后端

若 Gateway 或后端有埋点接口，可增加：

- `ota_fallback_shown`：展示 TauriRequiredFallback 时上报
- `ota_invoke_failed`：invoke 失败时上报（cmd、error 摘要）

当前文档未要求，可作为后续迭代。

---

## 四、移动端 WebView

### 4.1 现状

- **index.html**：`viewport-fit=cover`，支持刘海/安全区域。
- **index.css**：`height: 100dvh` + `var(--visual-viewport-height)`，键盘弹出时视口高度自适应。
- **main.tsx**：`visualViewport` 的 `resize`/`scroll` 监听，同步 `--visual-viewport-height`。
- **BottomTabBar**：`env(safe-area-inset-bottom)` 适配 Home Indicator。

### 4.2 OTA 页面特殊考虑

| 项目 | 建议 |
|------|------|
| **viewport** | OTA 前端与本地前端共用同一 `index.html` 模板，`viewport-fit=cover` 已满足；CDN 部署的 OTA 前端需确保构建产物包含相同 meta |
| **安全区域** | `TauriRequiredFallback` 若为全屏居中，建议增加 `padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)`，避免内容被刘海/Home Indicator 遮挡 |
| **键盘** | Fallback 页面无输入框，键盘弹出概率低；若未来增加输入，需复用现有 `--visual-viewport-height` 逻辑 |
| **iOS/Android 差异** | iOS WebView 对 `env(safe-area-inset-*)` 支持较好；Android 部分机型需 `viewport-fit=cover` + `padding` 组合 |

### 4.3 TauriRequiredFallback 移动端样式建议

```tsx
<div
  className="min-h-screen flex flex-col items-center justify-center bg-nb-bg p-4 sm:p-6"
  style={{
    paddingTop: 'max(env(safe-area-inset-top), 1rem)',
    paddingBottom: 'max(env(safe-area-inset-bottom), 1rem)',
    paddingLeft: 'max(env(safe-area-inset-left), 1rem)',
    paddingRight: 'max(env(safe-area-inset-right), 1rem)',
  }}
>
  {/* 内容 */}
</div>
```

或使用 Tailwind 的 `pt-[env(safe-area-inset-top)]` 等（若项目 Tailwind 版本支持）。

---

## 五、具体修改建议汇总

### 5.1 文档补充建议（OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md）

在 **Phase 3** 中补充：

1. **TauriRequiredFallback 设计规范**：
   - 使用 `nb-*` 设计 token，与 AuthPage、AppErrorBoundary 一致
   - 响应式：`min-h-screen`、`max-w-md`、`p-4 sm:p-6`
   - 移动端安全区域：`env(safe-area-inset-*)`

2. **错误边界**：
   - OTA 分支下 `App` 也需被 `AppErrorBoundary` 包裹
   - 可选：区分「无 __TAURI__」与「有 __TAURI__ 但 invoke 失败」的文案

3. **可观测性**：
   - 前端 `console.info`/`console.debug` 规范
   - 可选：`novaic_ota_debug` 调试开关

### 5.2 实现清单（前端）

| # | 任务 | 产出 |
|---|------|------|
| 1 | 实现 `TauriRequiredFallback` 组件 | 新组件，符合设计系统 |
| 2 | 在 `main.tsx` 中集成 OTA 检测与 Fallback 分支 | main.tsx |
| 3 | 将 `AppErrorBoundary` 提取到独立模块，OTA 分支也包裹 `App` | AppErrorBoundary.tsx + main.tsx |
| 4 | 为 Fallback 增加安全区域 padding | TauriRequiredFallback.tsx |
| 5 | 增加 OTA 可观测性日志（含调试开关） | main.tsx |

### 5.3 UI/UX 改进建议

| 项目 | 建议 |
|------|------|
| **图标** | 使用 `Smartphone` 或 `AlertTriangle`，传达「需在 App 中打开」 |
| **副文案** | 可增加「下载 NovAIC App」链接（若已有下载页） |
| **重试** | 若检测到 `__TAURI__` 存在但曾失败，可提供「重试」按钮，触发 `window.location.reload()` |
| **动画** | 与现有 `animate-fade-in`、`animate-slide-up` 一致，避免生硬出现 |

---

## 六、参考

- `novaic-app/src/App.tsx`：AppErrorBoundary、initTimeout 错误页
- `novaic-app/src/components/Auth/AuthPage.tsx`：全屏居中卡片布局
- `novaic-app/src/components/Layout/BottomTabBar.tsx`：`env(safe-area-inset-bottom)` 用法
- `novaic-app/tailwind.config.js`：`nb-*` 设计 token
- `novaic-app/index.html`：`viewport-fit=cover`、`#preload-fallback`
