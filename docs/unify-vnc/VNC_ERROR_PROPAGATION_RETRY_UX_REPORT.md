# VNC 错误传播与重试 UX 研究报告

> 对照设计文档，研究 VNC 连接失败时的用户反馈与重试体验。

---

## 一、错误传播路径总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  createVncTransport 失败                                                        │
│  (invoke 失败 / VncBridgeTransport.connect 失败)                                 │
│       → AgentDesktopView/DeviceDesktopView: transportError 页面，无 VncCanvas    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  createVncTransport 成功 → useVnc (main 路径)                                     │
│       → doConnect → RFB(transport)                                               │
│       → disconnect(clean=false) → reconnecting → 自动重连 5 次                    │
│       → 失败 → setErrorMsg('Connection lost, max retries exceeded')               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  vncStream 路径 (VNCViewShared / 缩略图)                                          │
│       → connectStream → getVncTransport / testWebSocket / RFB                     │
│       → onError / status='error' → 自动重连 3 次                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、错误信息分析

### 2.1 useVnc 的 setErrorMsg

| 场景 | 错误文案 | 来源 |
|------|----------|------|
| 重连失败（clean=false，5 次后） | `Connection lost, max retries exceeded` | 硬编码 |
| 需要凭证 | `VNC requires credentials (unexpected)` | 硬编码 |
| RFB 初始化异常 | `e.message` 或 `RFB connection failed` | catch 块 |
| disconnect clean=true | 无 errorMsg | 正常断开 |

**问题**：
- `Connection lost, max retries exceeded` 未区分「网络超时」「后端未就绪」「认证失败」
- useVnc 的 disconnect 事件只读取 `e?.detail?.clean`，**不读取 `e?.detail?.reason`**，后端传来的具体错误（如 "VNC connection timed out (30s)"）被丢弃
- 文案为英文，与部分组件中文不一致

### 2.2 vncStream 的 onError

| 场景 | 错误文案 | 来源 |
|------|----------|------|
| getVncTransport 失败 | `err?.message` 或 `Failed to get VNC transport` | catch |
| testWebSocket 失败 | `VNC WebSocket not available` | throw |
| RFB disconnect（连接失败） | `reason`（若存在） | e?.detail?.reason ?? e?.reason |
| 安全失败 | `e.detail?.reason` 或 `Security failure` | securityfailure |
| 其他 catch | `e.message` 或 `Connection failed` | catch |

**问题**：
- `reason` 依赖 noVNC/WebSocket 是否传递；vnc_proxy 30s 超时时**不发送 Close reason**，前端可能收不到
- `VNC WebSocket not available` 与 `Failed to create transport` 语义重叠，用户难以区分

### 2.3 createVncTransport 的 catch

| 场景 | 错误文案 | 用户看到 |
|------|----------|----------|
| invoke 失败 | `e.message` 或 `Failed to create transport` | transportError 页面 |
| VncBridgeTransport.connect 失败 | 同上 | 同上 |

**典型后端错误**（来自 vnc_proxy / vnc_bridge）：
- `VNC proxy not started yet`
- `No online VmControl device found. Ensure your PC is running NovAIC and connected.`
- `Not logged in — JWT token missing`
- `P2P setup failed: {err}. Please check NOVAIC_P2P_PORT and firewall.`
- `VmControl P2P not ready yet — please wait a moment and retry`
- `Remote P2P connect failed: {e}`

**是否区分**：
- 网络超时：createVncTransport 路径无超时；VncBridgeTransport 连接 vnc_proxy 时，若 30s 超时，后端可能不发送 Close reason，前端收到 generic 错误
- 后端未就绪：有明确文案（如 "VNC proxy not started yet"）
- 认证失败：有明确文案（如 "Not logged in"）

---

## 三、Retry 按钮

### 3.1 VncConnectionOverlay 行为

```tsx
// VncConnectionOverlay.tsx:26-45
if (status === 'failed' || status === 'reconnecting') {
  return (
    <div>
      <span>{errorMsg || 'Connection lost'}</span>
      {transportReady && <button onClick={connect}>Retry</button>}
      {!transportReady && <span>Preparing transport…</span>}
    </div>
  );
}
```

- `transportReady` 来自 `transport !== null`（VncCanvas 传入）
- 仅当 `transportReady=true` 时显示 Retry 按钮

### 3.2 createVncTransport 失败时

- AgentDesktopView / DeviceDesktopView 在 `transportError` 时直接 return，**不渲染 VncCanvas**
- 用户看到：错误文案 + 无 Retry 按钮
- **UX 问题**：用户无法重试，必须切换设备/重新进入页面

### 3.3 transport 为 null 时点 Retry

- 若 transport 为 null，`transportReady=false`，Retry 不显示，显示 "Preparing transport…"
- 若因竞态导致 transport 为 null 却 somehow 显示 Retry（理论上不应发生）：
  - `connect` = `doConnect`
  - `doConnect` 检查 `if (!t || !containerRef.current) return`
  - **静默 return，无任何反馈**

### 3.4 修复建议

- 在 transportError 页面增加 Retry 按钮，点击时重新调用 `createVncTransport`
- 若 `doConnect` 因 `!t` 提前 return，应 `setErrorMsg('Transport not ready, please wait')` 或 `setStatus('failed')` 并给出提示

---

## 四、reconnecting 状态

### 4.1 useVnc 有 reconnecting，vncStream 无

| 路径 | 状态枚举 | reconnecting |
|------|----------|--------------|
| useVnc (main) | connecting \| connected \| disconnected \| reconnecting \| failed | ✅ 有 |
| vncStream | disconnected \| connecting \| connected \| error | ❌ 无 |

### 4.2 main 路径重连时用户看到什么

- useVnc：disconnect(clean=false) → `setStatus('reconnecting')`，启动定时器自动重连
- VncConnectionOverlay：`reconnecting` 与 `failed` **共用同一 UI**
  - 标题："Connection failed"
  - 副文案：errorMsg 或 "Connection lost"
  - Retry 按钮：显示

**UX 问题**：
- reconnecting 时用户看到 "Connection failed" 而非 "Reconnecting…"
- 用户可能误以为已失败，点击 Retry 会触发额外 `doConnect()`，与自动重连竞态
- vncStream 路径：自动重连时 status 为 `connecting`，用户看到转圈，无 "Reconnecting" 文案

### 4.3 修复建议

- reconnecting 时 overlay 显示 "Reconnecting…" + 进度（如 "Retry 2/5"），并禁用或隐藏 Retry 按钮
- 或：reconnecting 时显示 "Reconnecting…" + 可取消的 Retry，点击取消自动重连

---

## 五、后端 30s 超时

### 5.1 vnc_proxy 超时行为

```rust
// vnc_proxy.rs:184-187
match tokio::time::timeout(WS_UPGRADE_TIMEOUT, route_vnc(socket, ...)).await {
    Ok(Ok(())) => {}
    Ok(Err(e)) => tracing::error!("[VncProxy] Error ...");  // 有 send_ws_close_with_reason
    Err(_) => tracing::error!("[VncProxy] Timeout (30s) ...");  // 仅日志，无 Close reason
}
```

- 超时触发时：`route_vnc` future 被取消并 drop
- WebSocket 句柄随之 drop，连接被强制关闭
- **未调用** `send_ws_close_with_reason`
- 前端收到 abrupt close，通常**无带 reason 的 Close 帧**

### 5.2 前端表现

- 用户先看到 "Connecting to desktop…" 转圈约 30s
- 然后连接突然断开
- useVnc：disconnect(clean=false)，进入 reconnecting，最多 5 次后 failed，errorMsg = "Connection lost, max retries exceeded"
- 用户**无法得知**是「超时」还是其他网络问题

### 5.3 修复建议

- 超时分支在 drop 前，对已 upgrade 的 WebSocket 调用 `send_ws_close_with_reason(ws, "VNC connection timed out (30s)")`
- 需注意：timeout 时 `route_vnc` 可能尚未将 ws 传入 `bridge_ws_quic`（例如卡在 `get_or_create_remote_conn`），需在 handler 层持有 ws 引用，超时时主动发送 Close
- 前端 useVnc：在 disconnect 中读取 `e?.detail?.reason`，若有则 `setErrorMsg(reason)`，否则再使用默认 "Connection lost, max retries exceeded"

---

## 六、UX 问题汇总

| 问题 | 严重度 | 描述 |
|------|--------|------|
| transportError 无 Retry | 高 | createVncTransport 失败时用户无法重试 |
| 30s 超时无明确提示 | 高 | 用户看到长时间转圈后突然失败，无 "超时" 文案 |
| reconnecting 与 failed 共用 UI | 中 | 重连中显示 "Connection failed"，易误解 |
| Retry 与自动重连竞态 | 中 | reconnecting 时点 Retry 触发额外 doConnect |
| useVnc 不读取 disconnect reason | 中 | 后端传来的具体错误被丢弃 |
| transport=null 时 connect 静默 return | 中 | 无反馈（当前 transportReady=false 时 Retry 不显示，部分缓解） |
| 错误文案中英混用 | 低 | "Connection lost, max retries exceeded" 等为英文 |

---

## 七、修复建议优先级

1. **P0**：vnc_proxy 30s 超时前发送 `send_ws_close_with_reason(ws, "VNC connection timed out (30s)")`
2. **P0**：transportError 页面增加 Retry 按钮，重新调用 createVncTransport
3. **P1**：useVnc disconnect 中读取 `e?.detail?.reason`，优先展示后端错误
4. **P1**：reconnecting 时 overlay 显示 "Reconnecting…" 并禁用 Retry，避免竞态
5. **P2**：统一错误文案语言（中/英）与分类（超时 / 后端未就绪 / 认证失败）

---

## 八、相关文件索引

| 文件 | 职责 |
|------|------|
| `novaic-app/src/hooks/useVnc.ts` | RFB 会话、重连、setErrorMsg |
| `novaic-app/src/services/vncStream.ts` | 流订阅、onError、自动重连 |
| `novaic-app/src/services/vncTransport.ts` | createVncTransport |
| `novaic-app/src/components/Visual/VncConnectionOverlay.tsx` | 连接状态 overlay、Retry |
| `novaic-app/src/components/Visual/AgentDesktopView.tsx` | createVncTransport、transportError |
| `novaic-app/src/components/Visual/DeviceDesktopView.tsx` | 同上 |
| `novaic-app/src/components/Visual/VncCanvas.tsx` | useVnc、renderOverlay、transportReady |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | WS 代理、30s 超时、send_ws_close_with_reason |
| `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | OTA 桥接、close 事件 |
