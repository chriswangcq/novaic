# OTA RE-ENABLE V2 — 前端构建、路由与 invoke 调用链评审

> 审阅文档：`docs/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md`  
> 审阅范围：novaic-app 前端代码结构、构建、路由、invoke 调用链

---

## 一、Vite 构建与 VITE_BASE 对 OTA 的影响

### 1.1 当前配置

| 配置项 | 值 | 来源 |
|--------|-----|------|
| `vite.config.ts` base | `process.env.VITE_BASE \|\| '/'` | 构建时注入 |
| OTA 部署 base | `/resource/frontend/v0.3.0/` | `deploy-frontend.sh` 设置 `VITE_BASE` |
| 构建命令 | `VITE_BASE="${VITE_BASE_PATH}" npm run build` | 脚本第 25 行 |

### 1.2 静态资源路径

**问题：`index.html` 中 favicon 使用绝对路径**

```html
<!-- 当前：index.html 第 5 行 -->
<link rel="icon" type="image/svg+xml" href="/icon.svg" />
```

- 当 base 为 `/resource/frontend/v0.3.0/` 时，`/icon.svg` 会请求 `https://relay.gradievo.com/icon.svg`（根路径），导致 404
- Vite 构建时**不会**自动改写 index.html 中的静态 `href`

**修改建议：**

```html
<link rel="icon" type="image/svg+xml" href="./icon.svg" />
```

或使用 Vite 的 base 占位（若项目支持）：

```html
<link rel="icon" type="image/svg+xml" href="%BASE_URL%icon.svg" />
```

- `./icon.svg` 在 OTA URL `https://relay.gradievo.com/resource/frontend/v0.3.0/` 下会解析为 `.../v0.3.0/icon.svg`，正确
- 本地 dev（base `/`）下同样有效

### 1.3 JS/CSS 资源

- Vite 构建时会对 `import` 的 JS/CSS 自动加上 base 前缀，无需额外处理
- `index.html` 中的 `<script type="module" src="/src/main.tsx">` 在构建时会被 Vite 替换为带 hash 的 chunk，并自动加上 base

### 1.4 API 调用

- 前端 API 通过 Tauri `invoke('gateway_get'/'gateway_post')` 调用，不依赖前端 base path
- `API_CONFIG.GATEWAY_URL` 来自 `VITE_GATEWAY_URL`，与 base 无关

**结论：** 除 favicon 外，静态资源与 API 在 OTA base 下可正常工作；需修正 `index.html` 中的 favicon 路径。

---

## 二、前端 invoke 调用链分析

### 2.1 执行顺序概览

```
main.tsx 加载
  → import App (仅加载模块，无 invoke)
  → ReactDOM.createRoot().render(<App />)
  → App 挂载
  → useEffect 依次执行
```

### 2.2 启动时 invoke 调用链（按时间顺序）

| 阶段 | 触发点 | invoke 命令 | 条件 |
|------|--------|-------------|------|
| 1 | `App` 首个 `useEffect` → `restoreSession()` | `get_gateway_url` | 始终执行 |
| 2 | 同上 | `set_gateway_url` | 仅当 Rust 为默认云端且与 config 不一致 |
| 3 | `getAccessToken()` → `getStoredUser()` → `secureGet()` → `detectTauri()` | `secure_storage_get` | 首次访问 secureStorage |
| 4 | `restoreSession()` | `update_cloud_token` | 有/无 token 时都会调用（空串或实际 token） |
| 5 | `isSignedIn` 后 `pushToken()` | `update_cloud_token` | 登录后 |
| 6 | `getAgentService().initialize()` → `connectUserStream()` | `listen` (×6) + `gateway_sse_connect` (×2) | 登录后 |
| 7 | `loadAgents()` → `api.listAgents()` | `gateway_get` | 初始化后 |
| 8 | 用户操作（VM、VNC、Scrcpy 等） | `gateway_*`, `get_vnc_proxy_url`, `get_scrcpy_proxy_url` 等 | 按需 |

### 2.3 __TAURI__ 检测前的 invoke 风险

**结论：在 `main.tsx` 中、`render` 之前做 `__TAURI__` 检测并渲染 Fallback 时，不会触发任何 invoke。**

原因：

1. **模块加载阶段**：`import App from './App'` 只加载模块，不执行 `useEffect`
2. **invoke 均在 useEffect 或用户操作中**：`restoreSession`、`pushToken`、`connectUserStream` 等都在 `useEffect` 内
3. **无顶层 invoke**：`config`、`store`、`auth`、`application` 等模块加载时无 invoke 调用
4. **Zustand store**：`create()` 时仅做同步状态初始化，读取 `localStorage`，不涉及 invoke

因此，按 Phase 3 方案在 `render` 前判断并渲染 `TauriRequiredFallback` 时，`App` 不会挂载，所有 invoke 都不会执行。

### 2.4 建议的 main.tsx 实现（与 Phase 3 一致）

```tsx
// main.tsx — 在 render 之前同步检测
const OTA_ORIGINS = ['https://relay.gradievo.com', 'https://api.gradievo.com'];
const needsTauri = OTA_ORIGINS.some(o => location.origin === o) && !('__TAURI__' in window);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {needsTauri ? <TauriRequiredFallback /> : <App />}
  </React.StrictMode>
);
```

---

## 三、路由配置与深层路径

### 3.1 当前路由机制

- 项目**未使用** React Router（无 `BrowserRouter`、`createBrowserRouter` 等）
- 页面状态由内部 state 控制：`currentPage`（setup/workspace）、`narrowPage`（sidebar/chat/devices/settings/more）
- 无 URL 路径与页面映射

### 3.2 深层路径与检测逻辑

- 检测条件：`location.origin === 'https://relay.gradievo.com'` 或 `'https://api.gradievo.com'`
- 与 `pathname` 无关，因此：
  - `https://relay.gradievo.com/resource/frontend/v0.3.0/`
  - `https://relay.gradievo.com/resource/frontend/v0.3.0/agents/xxx`
  - `https://relay.gradievo.com/any/path`

只要 origin 匹配，检测逻辑都能正确工作。

### 3.3 Nginx 与 SPA 回退

当前 nginx 配置（`setup-cnd-frontend-nginx.sh`）：

```nginx
location /resource/frontend/ {
    alias ${STATIC_DIR}/;
    index index.html;
    add_header Cache-Control "public, max-age=3600";
}
```

- 访问 `/resource/frontend/v0.3.0/agents/xxx` 时，会请求 `static/v0.3.0/agents/xxx`，文件不存在则返回 404
- 当前无 SPA 路由，因此不会出现该路径；若未来引入 URL 路由，建议增加 `try_files` 回退到 `index.html`：

```nginx
location /resource/frontend/ {
    alias ${STATIC_DIR}/;
    index index.html;
    try_files $uri $uri/ /resource/frontend/v0.3.0/index.html =404;
    add_header Cache-Control "public, max-age=3600";
}
```

---

## 四、第三方库在 App mount 前的初始化

### 4.1 Clerk

- 项目已从 Clerk 迁移到自定义 JWT（`auth.ts`），无 Clerk 相关初始化

### 4.2 Zustand

- `store.ts` 中 `create()` 在模块加载时执行
- 初始状态仅依赖 `localStorage`、`window.innerWidth` 等同步 API
- **不触发 invoke**

### 4.3 其他模块

| 模块 | 加载时机 | 是否 invoke |
|------|----------|-------------|
| `config/index.ts` | import 时 | 否，仅 `import.meta.env` 和 `console.warn` |
| `gateway/auth` | 通过 application 间接加载 | 否，`getCachedUser` 为同步内存读取 |
| `secureStorage` | 首次 `secureGet` 调用时 | 是，但首次调用在 `restoreSession` 的 `getAccessToken` 中，即 App 已挂载 |

**结论：** 在 `render` 前没有任何第三方库会触发 invoke。

---

## 五、具体修改建议汇总

### 5.1 必须修改

| # | 文件 | 修改内容 |
|---|------|----------|
| 1 | `index.html` | `href="/icon.svg"` → `href="./icon.svg"` |
| 2 | `main.tsx` | 在 `render` 前增加 `__TAURI__` + OTA origin 检测，条件满足时渲染 `TauriRequiredFallback` |

### 5.2 建议新增

| # | 文件 | 修改内容 |
|---|------|----------|
| 3 | `main.tsx` | 新增 `TauriRequiredFallback` 组件（或单独文件），文案按 Phase 3 |
| 4 | `setup-cnd-frontend-nginx.sh` | 为未来 SPA 路由增加 `try_files` 回退（可选） |

### 5.3 TauriRequiredFallback 组件示例

```tsx
function TauriRequiredFallback() {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-nb-bg text-nb-text p-8 gap-4">
      <p className="text-center max-w-md">
        当前环境不支持 Tauri 功能，请使用 NovAIC App 打开此页面。
      </p>
      <p className="text-nb-text-secondary text-sm text-center max-w-md">
        若您已在 App 中打开，请检查网络或尝试重新启动 App。
      </p>
    </div>
  );
}
```

---

## 六、需注意的边界情况

### 6.1 OTA 与本地构建的 base 差异

- 本地 dev：`base: '/'`，favicon `./icon.svg` 解析为 `/icon.svg`，正常
- Tauri 打包：通常 `base: '/'`，同上
- OTA 部署：`base: '/resource/frontend/v0.3.0/'`，`./icon.svg` 解析为 `.../v0.3.0/icon.svg`，正确

### 6.2 secureStorage 的 detectTauri

- `secureStorage.detectTauri()` 通过 `invoke('secure_storage_get', { key: '__probe__' })` 探测
- 仅在首次 `secureGet` 时调用，而首次调用在 `restoreSession` → `getAccessToken` → `getStoredUser` → `secureGet`
- 在 `needsTauri` 为 true 时不会渲染 `App`，因此不会执行到此处

### 6.3 混合内容（macOS/iOS）

- 文档已提及 Tauri postMessage 回退及 JSON 响应 bug（#9266）
- 若 invoke 返回复杂 JSON 异常，需关注 Tauri 版本与相关 issue

### 6.4 版本切换时的 base

- 每次发布新版本会变更 base（如 `/resource/frontend/v0.3.1/`）
- Gateway 的 `FRONTEND_CDN_URL` 需与 `remote.urls` 的 host 一致
- 部署顺序：先部署静态资源，再更新 Gateway 配置并重启

---

## 七、调用链时序图（简化）

```
main.tsx
  │
  ├─ import App (无 invoke)
  │
  ├─ needsTauri? ──Yes──> render(TauriRequiredFallback)  [结束，无 invoke]
  │
  └─ No
       │
       └─ render(App)
            │
            └─ App mount
                 │
                 ├─ useEffect[1] restoreSession
                 │    ├─ invoke('get_gateway_url')
                 │    ├─ invoke('set_gateway_url') [条件]
                 │    ├─ getAccessToken → secureGet → detectTauri → invoke('secure_storage_get')
                 │    └─ invoke('update_cloud_token')
                 │
                 └─ useEffect[2] (isSignedIn)
                      ├─ pushToken → invoke('update_cloud_token')
                      └─ getAgentService().initialize()
                           ├─ connectUserStream → invoke('gateway_sse_connect') ×2
                           └─ loadAgents → api.listAgents → invoke('gateway_get')
```

---

## 八、验收检查清单

- [ ] `index.html` favicon 使用 `./icon.svg`
- [ ] `main.tsx` 在 render 前完成 `__TAURI__` + OTA origin 检测
- [ ] `needsTauri` 为 true 时仅渲染 `TauriRequiredFallback`，不渲染 `App`
- [ ] `VITE_BASE=/resource/frontend/v0.3.0/` 构建后，静态资源可正常加载
- [ ] 在浏览器直接打开 OTA URL 且无 Tauri 时，显示 Fallback 文案，无 invoke 报错
