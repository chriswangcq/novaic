# 跨平台架构：差异化与组件化分析

> 目标平台：Mac、Windows、Android、iPhone（不含 Web，不含 VMControl）  
> 当前：Tauri + React，连接云端 Gateway

---

## 一、需要抽象的核心层

### 1. Native Bridge（平台桥接层）

**现状**：所有原生能力通过 `invoke('xxx', ...)` 调用 Tauri 命令，强耦合 Tauri。

| 能力 | 当前实现 | Mac/Windows | Android | iPhone |
|------|----------|-------------|---------|--------|
| **HTTP / Gateway** | `invoke('gateway_get/post/...')` | Tauri reqwest | 需原生 HTTP + JWT | 同左 |
| **SSE 连接** | `invoke('gateway_sse_connect')`，Rust 侧 reqwest 绕过 WebView CORS | Tauri | 需原生 SSE 或 WebView fetch | 同左 |
| **Token 同步** | `invoke('update_cloud_token')` | Tauri CloudTokenState | 需 Keychain/Keystore | Keychain |
| **文件打开** | `invoke('open_file')` / `show_in_folder` | Tauri shell | Intent / Share | UIDocumentInteractionController |
| **文件下载缓存** | `invoke('download_file_to_cache')` | Tauri fs | 需原生下载 + 沙盒路径 | 同左 |
| **认证图片** | `invoke('fetch_authenticated_bytes')` | Tauri 带 JWT 请求 | 需原生或 WebView 带 Header | 同左 |

**组件化建议**：

```
platform/
  types.ts          # IPlatformBridge 接口
  tauri.ts          # Tauri 实现
  react-native.ts   # React Native 实现（Android/iOS）
  capacitor.ts      # Capacitor 实现（可选）
```

```typescript
// types.ts
interface IPlatformBridge {
  // 网络
  gatewayGet(path: string): Promise<unknown>;
  gatewayPost(path: string, body: unknown): Promise<unknown>;
  gatewayPatch(path: string, body: unknown): Promise<unknown>;
  gatewayDelete(path: string): Promise<unknown>;
  
  // SSE（移动端可用 fetch + ReadableStream 或原生）
  connectSSE(path: string, onMessage: (data: string) => void, onError: () => void): () => void;
  
  // Token
  setCloudToken(token: string): Promise<void>;
  
  // 文件
  openFile(path: string): Promise<void>;
  showInFolder(path: string): Promise<void>;
  downloadToCache(url: string, filename: string): Promise<{ path: string }>;
  fetchAuthenticatedBytes(url: string): Promise<ArrayBuffer>;
}
```

---

### 2. 存储层（Storage）

**现状**：

| 存储 | 当前 | 跨平台差异 |
|------|------|-------------|
| **IndexedDB** | idb，messages/logs/prefs/files | ✅ 各平台 WebView 均支持 |
| **localStorage** | Token、user_info | ⚠️ 移动端建议用 SecureStorage |
| **Rust data_dir** | api_key.txt, gateway_url.txt | ❌ 仅 Tauri，移动端需替代 |

**组件化建议**：

```
storage/
  SecureStorage.ts   # 抽象：Token、敏感配置
  ConfigStorage.ts   # 抽象：gateway_url、api_key 等非敏感配置
```

- **Desktop**：SecureStorage → localStorage（或 Tauri 加密存储）；ConfigStorage → 读 data_dir
- **Mobile**：SecureStorage → react-native-keychain / expo-secure-store；ConfigStorage → AsyncStorage 或原生

---

### 3. 窗口 / 导航（Window & Navigation）

**现状**：

| 能力 | 当前 | 差异 |
|------|------|------|
| **窗口拖动** | `data-tauri-drag-region`，`getCurrentWindow().startDragging()` | 仅桌面 |
| **红绿灯区** | `isMacOS ? 'pl-[76px]' : 'pl-2'` | 仅 Mac |
| **最大化** | `getCurrentWindow().toggleMaximize()` | 仅桌面 |
| **布局模式** | `useIsSidebarLayout()` 基于 `min-width` | 桌面=三栏，手机=底 Tab |

**组件化建议**：

```
layout/
  WindowChrome.tsx     # 抽象：标题栏、拖拽区、红绿灯
  useWindowChrome.ts   # 返回 { isDesktop, isMac, canDrag, onMaximize }
  useLayoutMode.ts     # 返回 'sidebar' | 'mobile'，由平台 + 宽度决定
```

- **Desktop**：WindowChrome 渲染拖拽区、红绿灯占位
- **Mobile**：WindowChrome 为空或仅状态栏占位，无拖拽

---

### 4. 文件与附件（Files & Attachments）

**现状**：

- `FileAttachment.tsx`：`invoke('open_file')`、`invoke('show_in_folder')`、`invoke('download_file_to_cache')`
- 图片：`invoke('fetch_authenticated_bytes')` + IndexedDB 缓存

**组件化建议**：

```
components/FileAttachment/
  FileAttachment.tsx      # 纯 UI，通过 props 接收 handlers
  useFileActions.ts      # 返回 { openFile, showInFolder, downloadAndOpen }
```

`useFileActions` 内部调用 `platformBridge.openFile` 等，由平台实现决定行为。

---

### 5. 认证流程（Auth）

**现状**：

- `auth.ts`：localStorage 存 Token，`invoke('update_cloud_token')` 推给 Rust
- 云端 Gateway 校验 JWT

**跨平台差异**：

| 环节 | Desktop | Android | iPhone |
|------|---------|---------|--------|
| Token 存储 | localStorage | Keystore | Keychain |
| Token 同步到原生 | update_cloud_token | 无（或 RN 模块） | 无 |
| 生物识别 | 无 | 可选 | 可选 |

**组件化建议**：

```
auth/
  AuthService.ts       # 抽象：login, logout, getAccessToken, getCurrentUser
  TokenStorage.ts      # 抽象：get/set token（由平台提供 SecureStorage）
```

---

### 6. API 客户端（Gateway Client）

**现状**：`services/api.ts` 全部通过 `invoke('gateway_*')`，Rust 侧带 JWT 请求 Gateway。

**组件化建议**：

```
gateway/
  client.ts            # 封装 gatewayGet/Post/Patch/Delete
  platformClient.ts    # 注入 IPlatformBridge，或直接用 fetch（移动端）
```

- **Desktop**：继续用 `invoke`，由 Tauri 处理 CORS、证书
- **Mobile**：可用 `fetch` + `appendTokenToUrl` 或 Header，若 Gateway 支持；或通过原生模块发请求

---

### 7. SSE 连接（SSE Stream）

**现状**：

- `gateway/sse.ts`：`invoke('gateway_sse_connect')`，Rust 用 reqwest 建 SSE，通过 Tauri event 回传
- 目的：绕过 WebView CORS/SSL 限制

**跨平台差异**：

| 平台 | 方案 |
|------|------|
| Desktop (Tauri) | 保持 Rust reqwest，event 回传 |
| Android / iPhone | WebView 内 fetch 若受 CORS 限制，需原生 SSE 或 Gateway 支持 CORS；或通过原生 HTTP 模块 |

**组件化建议**：

```
gateway/
  sse.ts               # 抽象：connectUserStream(), disconnectUserStream()
  sseTauri.ts          # Tauri 实现（invoke + listen）
  sseNative.ts         # 移动端：EventSource / fetch + ReadableStream / 原生模块
```

---

### 8. 对话框与确认（Dialogs）

**现状**：`window.confirm()` 用于删除确认，未用 Tauri dialog plugin。

**跨平台**：

- Desktop：`window.confirm` 或 Tauri dialog
- Mobile：需原生 Alert / 自定义 Modal

**组件化建议**：

```
ui/
  confirm.ts           # confirm(message): Promise<boolean>
  platformConfirm.ts  # Desktop: window.confirm；Mobile: Alert.alert
```

---

### 9. 布局与响应式（Layout）

**现状**：`useMediaQuery`、`useIsSidebarLayout` 基于 `window.matchMedia`，逻辑可复用。

**差异**：

| 维度 | Desktop | Mobile |
|------|---------|--------|
| 断点 | 768/1024/1280 | 同左，但手机多为单栏 |
| 导航 | 侧边栏 + 三栏 | 底 Tab + 全屏页 |
| 安全区 | 无 | 刘海、Home Indicator |

**组件化建议**：

```
layout/
  useLayoutMode.ts     # 'sidebar' | 'mobile'，可加 isTablet
  useSafeArea.ts       # 移动端：paddingBottom 等
  LayoutContainer.tsx  # 根据 layoutMode 切换 SidebarLayout | MobileLayout
```

---

### 10. 配置与环境（Config）

**现状**：

- `VITE_GATEWAY_URL` 编译时注入
- `gateway_url.txt` 运行时覆盖（Tauri data_dir）

**跨平台**：

- Desktop：data_dir 文件
- Mobile：AsyncStorage / 原生配置 / 远程配置

**组件化建议**：

```
config/
  ConfigProvider.ts   # 抽象：getGatewayUrl()（get_api_key 已删除）
  configTauri.ts       # 读 data_dir
  configMobile.ts      # 读 AsyncStorage 或原生
```

---

## 二、组件化优先级建议

| 优先级 | 模块 | 原因 |
|--------|------|------|
| P0 | Native Bridge (IPlatformBridge) | 所有原生调用的统一入口 |
| P0 | Gateway Client 抽象 | API 请求与平台解耦 |
| P0 | SSE 连接抽象 | 实时推送与平台解耦 |
| P1 | Storage / SecureStorage | Token 与敏感数据安全 |
| P1 | 文件操作 (useFileActions) | 附件打开、下载 |
| P2 | WindowChrome / 布局 | 桌面与移动 UI 差异 |
| P2 | Config 抽象 | 多环境配置 |
| P3 | Dialog 抽象 | 删除确认等交互 |

---

## 三、技术选型建议

| 平台 | 框架 | 说明 |
|------|------|------|
| Mac / Windows | Tauri 2 | 保持现状 |
| Android / iPhone | React Native + 新 Bridge | 或 Capacitor（复用部分 Web 代码，但 Bridge 仍需封装） |

若选 **React Native**：

- 共享：React 组件、Zustand、业务逻辑、IndexedDB（需 react-native-idb 或 AsyncStorage 替代）
- 重写：所有 `invoke` 调用 → 通过 `NativeModules` 或 `TurboModule` 实现 `IPlatformBridge`

若选 **Capacitor**：

- 共享：更多 Web 代码，包括部分 DOM API
- 差异：Capacitor 插件替代 Tauri 插件，SSE 可能仍受 CORS 限制

---

## 四、总结：差异化清单

| 类别 | 需组件化 | 平台差异 |
|------|----------|----------|
| **网络** | IPlatformBridge.gateway* | Tauri invoke vs 原生 HTTP |
| **SSE** | connectSSE | Rust reqwest vs EventSource/原生 |
| **存储** | SecureStorage, ConfigStorage | localStorage vs Keychain/Keystore |
| **文件** | openFile, downloadToCache | Tauri shell/fs vs Intent/UIDocument |
| **窗口** | WindowChrome | 拖拽、红绿灯仅桌面 |
| **布局** | useLayoutMode | 三栏 vs 底 Tab |
| **认证** | TokenStorage | 同上 |
| **配置** | ConfigProvider | data_dir vs AsyncStorage |

核心原则：**业务逻辑与 UI 不依赖具体平台 API**，通过 `IPlatformBridge` 和少量抽象层注入平台实现。
