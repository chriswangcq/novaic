# OTA 重新启用实施方案 — 前端与兼容性评审

> 针对 `docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md` 的评审，重点：前端生命周期、纯浏览器体验、移动端差异、Service Worker / Vite 影响

---

## 一、Phase 3：`__TAURI__` 检测 — 生命周期与首屏阻塞

### 1.1 当前方案的问题

实施方案写的是「在 `main.tsx` 或根组件 mount 时检测 `window.__TAURI__`」。若在 **App mount 后** 的 `useEffect` 中检测，存在以下问题：

| 问题 | 说明 |
|------|------|
| **invoke 已先执行** | `App.tsx` 的 `restoreSession` 在首个 `useEffect` 中立即调用 `invoke('get_gateway_url')`、`invoke('update_cloud_token')` 等。若 `__TAURI__` 不存在，这些调用会直接抛错 |
| **SSE 连接失败** | `getAgentService().initialize()` → `syncService.connectUserStream()` 使用 `invoke('gateway_sse_connect')` 和 `listen()`，纯浏览器下会立即失败 |
| **api 层全面依赖 invoke** | `api.ts` 中几乎所有接口都通过 `invoke('gateway_get/post/...')` 实现，`loadAgents()` 等会触发大量 invoke 调用 |

因此，**不能在 App mount 之后** 才检测，否则会先出现大量错误再显示提示。

### 1.2 推荐实现：在 main.tsx 入口同步检测

**执行时机**：在 `ReactDOM.createRoot().render()` **之前**，同步检测 `window.__TAURI__`。

**原因**：
- `__TAURI__` 由 Tauri 在页面加载时注入，在脚本执行时已就绪
- 检测为同步逻辑，不涉及异步，不会阻塞首屏
- 在挂载 App 前完成判断，可避免任何 invoke 调用

**实现示例**：

```tsx
// main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

// OTA 域名：仅在这些 origin 下需要 Tauri；本地 (tauri://, asset://) 必然有 __TAURI__
const OTA_ORIGINS = [
  'https://relay.gradievo.com',
  'https://api.gradievo.com',
];

function isOtaOrigin(): boolean {
  if (typeof window === 'undefined') return false;
  return OTA_ORIGINS.some((o) => window.location.origin === o);
}

function TauriRequiredFallback() {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-[#0d0d0d] text-white p-8">
      <p className="text-white/80 text-center max-w-md mb-4">
        当前环境不支持 Tauri 功能，请使用 NovAIC App 打开此页面。
      </p>
      <p className="text-white/50 text-sm">
        若您已在 App 中打开，请检查网络或尝试重新启动 App。
      </p>
    </div>
  );
}

// ... visualViewport 逻辑保持不变 ...

const root = document.getElementById('root')!;
const needsTauri = isOtaOrigin() && !('__TAURI__' in window);

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    {needsTauri ? <TauriRequiredFallback /> : <App />}
  </React.StrictMode>
);
```

### 1.3 结论

| 项目 | 建议 |
|------|------|
| **执行时机** | 在 `main.tsx` 中、`ReactDOM.render` 之前，同步检测 |
| **是否阻塞首屏** | 否，同步判断，无额外延迟 |
| **检测条件** | 仅当 `isOtaOrigin()` 且 `!('__TAURI__' in window)` 时渲染 fallback |

---

## 二、纯浏览器打开 OTA URL 的体验

### 2.1 是否需要区分处理

**需要**。纯浏览器（Safari/Chrome 直接打开 `https://relay.gradievo.com/resource/frontend/v0.3.0/`）与 Tauri App 内 WebView 的差异如下：

| 场景 | `__TAURI__` | invoke | 预期行为 |
|------|-------------|--------|----------|
| Tauri App 内 OTA | ✅ 注入 | ✅ 可用 | 正常使用 |
| 纯浏览器 | ❌ 不存在 | ❌ 抛错 | 显示「请使用 NovAIC App 打开」 |

### 2.2 建议的区分逻辑

1. **OTA origin + 无 `__TAURI__`**：渲染 `TauriRequiredFallback`，不挂载 App
2. **本地 (tauri://, asset://)**：不检测，直接挂载 App（本地必然有 `__TAURI__`）
3. **OTA origin + 有 `__TAURI__`**：正常挂载 App

### 2.3 Fallback 文案建议

- 主文案：`当前环境不支持 Tauri 功能，请使用 NovAIC App 打开此页面。`
- 副文案：`若您已在 App 中打开，请检查网络或尝试重新启动 App。`（覆盖 capability 未匹配等边缘情况）

---

## 三、iOS / Android 与桌面端差异

### 3.1 移动端需额外考虑的点

| 场景 | 风险 | 建议 |
|------|------|------|
| **网络切换** | WiFi ↔ 蜂窝切换时，OTA 请求可能失败或超时 | 已有 6s 超时，失败则 fallback 本地；网络切换对已加载页面的 invoke 无影响（进程内通信） |
| **后台恢复** | App 从后台恢复时，WebView 可能被系统回收或重载 | 若重载同一 OTA URL，capability 仍匹配，invoke 应可用；建议在文档中注明需验证 |
| **iOS WKWebView** | `OTA_INVOKE_4_AGENT_REPORT` 提到 postMessage fallback 存在 JSON 返回值 bug | 关注 Tauri 版本与 [Issue #9266](https://github.com/tauri-apps/tauri/issues/9266)；复杂 JSON 返回值可能异常 |
| **移动端窗口显示** | `setup.rs` 中 `w.show()` 仅 `#[cfg(desktop)]` | Phase 1 需确认移动端在 OTA 成功/失败后窗口都能正确显示；当前 `#[cfg(not(desktop))]` 仅打印日志，需补充移动端 show 逻辑 |

### 3.2 setup.rs 移动端 show 逻辑

当前实现：

```rust
#[cfg(desktop)]
if let Some(w) = app.get_webview_window("main") {
    let _ = w.show();
}
#[cfg(not(desktop))]
if app.get_webview_window("main").is_none() {
    eprintln!("[Frontend OTA] main window not found");
}
```

建议：在 Phase 1 中为移动端增加显式 `show`，确保 OTA 超时或失败时主窗口仍可见：

```rust
#[cfg(not(desktop))]
if let Some(w) = app.get_webview_window("main") {
    let _ = w.show();  // 移动端无托盘，必须确保窗口可见
}
```

### 3.3 useIsMobile 的兼容性

`useIsMobile.ts` 已正确处理非 Tauri 环境：

```ts
try {
  const osType = getOsType();  // Tauri plugin
  setIsMobile(osType === 'android' || osType === 'ios');
} catch {
  // Web / non-Tauri: fallback to userAgent
  const ua = navigator.userAgent.toLowerCase();
  setIsMobile(/android|iphone|ipad|ipod/.test(ua));
}
```

在纯浏览器下会走 `userAgent` 分支，无需修改。

---

## 四、Service Worker 与 Vite 构建产物

### 4.1 Service Worker

**结论**：当前项目未使用 Service Worker。

```bash
# grep 结果：无 service-worker、workbox、sw.js 等
```

`OTA_INVOKE_4_AGENT_REPORT` 中提到的 [Tauri #12673](https://github.com/tauri-apps/tauri/issues/12673)（远程页面 + SW 导致 invoke 二次启动失败）对本项目不适用。

**建议**：在 Phase 4 或部署文档中注明：**不要**为 OTA 前端引入 Service Worker，以免未来触发该问题。

### 4.2 Vite 构建与 invoke

| 项目 | 影响 |
|------|------|
| **VITE_BASE** | 部署时使用 `VITE_BASE=/resource/frontend/v0.3.0/`，影响静态资源路径，**不影响** invoke（invoke 为运行时 API） |
| **chunk 分割** | 动态 import 的 chunk 路径由 base 决定；若 base 错误会导致 404，但 invoke 本身不受影响 |
| **@tauri-apps/api/core** | 运行时通过 `window.__TAURI__.core.invoke` 调用，与构建产物无关 |

**结论**：Vite 配置与构建产物不会影响 OTA 页面的 invoke，只要 `remote.urls` 与 `frontend_url` 匹配即可。

### 4.3 部署一致性

`deploy-all.sh` 中：

- `VITE_BASE_PATH="/resource/frontend/v${VERSION}/"`
- Gateway 的 `FRONTEND_CDN_URL` 需与 `remote.urls` 一致

需在文档中明确：`FRONTEND_CDN_URL` 必须落在 `remote-frontend.json` 的 `remote.urls` 范围内。

---

## 五、具体修改建议汇总

### 5.1 对实施方案文档的修改

| 位置 | 原描述 | 建议修改 |
|------|--------|----------|
| Phase 3 实现要点 | 「main.tsx 或根组件 mount 时检测」 | 改为「在 main.tsx 中、ReactDOM.render 之前同步检测」 |
| Phase 3 可选 | 「仅在 OTA 页面时检测」 | 改为「**必须**仅在 OTA origin 时检测，本地跳过」 |
| Phase 1 | 未提及移动端 show | 补充「移动端在 OTA 完成/超时后也需调用 `w.show()`」 |
| 风险与缓解 | Service Worker | 补充「当前未使用 SW；未来引入需评估 Tauri #12673」 |
| 风险与缓解 | 移动端 | 补充「iOS postMessage JSON bug、后台恢复后 invoke 可用性需验证」 |

### 5.2 前端实现清单

1. **main.tsx**
   - 定义 `OTA_ORIGINS` 与 `isOtaOrigin()`
   - 在 `ReactDOM.render` 前：若 `isOtaOrigin() && !('__TAURI__' in window)`，渲染 `TauriRequiredFallback`，否则渲染 `App`

2. **TauriRequiredFallback 组件**
   - 简洁的全屏提示
   - 主文案 + 副文案（见 2.3）

3. **不修改 App.tsx**
   - 检测在入口完成，App 仅在 Tauri 可用时挂载，无需在 App 内再判断

### 5.3 兼容性风险矩阵

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 纯浏览器打开 OTA URL | 中 | Phase 3 入口检测 + Fallback 页面 |
| capability 与 URL 不匹配 | 高 | Phase 2 校验，不 navigate |
| iOS postMessage JSON bug | 低 | 关注 Tauri 更新，避免复杂 JSON 返回值 |
| 移动端 OTA 后窗口不显示 | 中 | Phase 1 为移动端补充 `w.show()` |
| 后台恢复后 invoke 异常 | 低 | 文档注明需验证，必要时重载 |
| Service Worker 引入 | 低 | 文档注明不引入 SW |

---

## 六、验收补充

在原有验收标准基础上，建议增加：

1. **纯浏览器**：在 Safari/Chrome 中直接打开 OTA URL，应显示「请使用 NovAIC App 打开」，且不出现 invoke 相关报错。
2. **移动端**：OTA 成功或超时后，主窗口可见；从后台恢复后，invoke 仍可用（或可重载恢复）。
3. **首屏**：`__TAURI__` 检测不增加可感知的首屏延迟。

---

## 七、参考

- `docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md`
- `docs/OTA_INVOKE_4_AGENT_REPORT.md`
- `docs/OTA_INVOKE_ROOT_CAUSE_ANALYSIS.md`
- `novaic-app/src/main.tsx`、`novaic-app/src/App.tsx`
- `novaic-app/src-tauri/src/setup.rs`
