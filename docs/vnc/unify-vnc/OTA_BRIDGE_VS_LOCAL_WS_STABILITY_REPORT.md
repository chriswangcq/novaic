# OTA Bridge 与本地 WebSocket 稳定性研究报告

> 研究范围：OTA 模式与本地模式的稳定性差异、`shouldUseVncBridge`、`VncBridgeTransport`，以及 Bridge 连接/断开流程  
> 对照设计文档：`docs/OTA_VNC_BRIDGE_IMPLEMENTATION_PLAN.md`、`docs/unify-vnc/09-phase4-design-code-verification.md`  
> 关键文件：`vncBridge.ts`、`vnc_proxy.rs`、`vnc_bridge.rs`、`vncStream.ts`、`vncTransport.ts`、`useVnc.ts`

---

## 一、shouldUseVncBridge()：OTA 检测逻辑

### 1.1 当前实现

```typescript
// vncBridge.ts:22-25
export function shouldUseVncBridge(): boolean {
  if (typeof window === 'undefined') return false;
  return window.isSecureContext;
}
```

**关键发现**：实现使用 `window.isSecureContext`，**不是** `isOtaOrigin()`（后者检查 `OTA_ORIGINS`）。

### 1.2 语义差异

| 条件 | 含义 | 何时为 true |
|------|------|-------------|
| `isOtaOrigin()` | 页面来自 OTA CDN | `location.origin` 在 `['https://relay.gradievo.com', 'https://api.gradievo.com']` |
| `isSecureContext` | 安全上下文 | HTTPS、`localhost`、`127.0.0.1`、`file://`、部分 `tauri://` |

### 1.3 可靠性分析

| 场景 | shouldUseVncBridge | 结果 | 风险 |
|------|--------------------|------|------|
| OTA (https://relay.gradievo.com) | true | 使用 Bridge | ✅ 正确 |
| 本地打包 (tauri://localhost) | 可能 true | 可能用 Bridge | 无 Mixed Content，Bridge 多余但无害 |
| 开发 (http://localhost:5173) | 部分浏览器 true | 可能用 Bridge | 同上 |
| 非 OTA 的 HTTPS | true | 使用 Bridge | ✅ 正确（Mixed Content 同样存在） |

### 1.4 误判风险

- **假阴性（漏用 Bridge）**：`isSecureContext` 为 false 时使用 WebSocket URL。OTA 场景下 HTTPS 页面必然为 secure context，假阴性几乎不可能。
- **假阳性（多用 Bridge）**：`isSecureContext` 为 true 时使用 Bridge。例如 `tauri://localhost` 或 `http://localhost` 可能被视为 secure context，会使用 Bridge 而非本地 WebSocket。功能上无问题，但会增加一次 IPC 开销。
- **Mixed Content**：若误判为 false 而使用 `ws://`，HTTPS 页面会触发 Mixed Content 被 WebKit 拦截（见 `VNC_WEBSOCKET_OTA_MIXED_CONTENT_REPORT.md`）。

### 1.5 修复建议

1. **保持现状**：`isSecureContext` 是安全且保守的代理，能覆盖所有 Mixed Content 场景。
2. **可选优化**：若希望与「OTA」语义严格一致，可改为：

   ```typescript
   export function shouldUseVncBridge(): boolean {
     if (typeof window === 'undefined') return false;
     return isOtaOrigin() || window.isSecureContext;
   }
   ```

   这样 `isOtaOrigin()` 为 true 时一定用 Bridge；否则仍用 `isSecureContext` 兜底。

---

## 二、VncBridgeTransport.connect()：连接失败与前端感知

### 2.1 调用链

```
createVncTransport / getVncTransport
  → new VncBridgeTransport(agentId, deviceId)
  → await transport.connect()
  其中：
  → invoke('vnc_bridge_connect', { agentId, deviceId })
  → 后端：resolve_device_id → ws_url → tokio_tungstenite::connect_async
```

### 2.2 后端失败路径

| 失败点 | 错误类型 | 返回给前端 |
|--------|----------|------------|
| `p.port == 0` | VncProxy 未启动 | `Err("VNC proxy not started yet")` |
| `resolve_device_id` 失败 | 无在线设备、my-devices 失败 | `Err("No online VmControl device found..."` 或 `Err(...)` |
| `tokio_tungstenite::connect_async` 失败 | 网络超时、连接被拒 | `Err("VNC WebSocket connect failed: ...")` |

### 2.3 前端 connect() 处理

```typescript
// vncBridge.ts:61-76
async connect(): Promise<void> {
  this.readyState = this.CONNECTING;
  try {
    this.bridgeId = await invoke<string>('vnc_bridge_connect', { ... });
    this.readyState = this.OPEN;
    await this.setupListeners();
    this.onopen?.();
  } catch (e) {
    this.readyState = this.CLOSED;
    this.onerror?.(e);
    this.onclose?.({ code: 1011, reason: String(e) });
  }
}
```

- **成功**：`readyState = OPEN`，`onopen?.()` 被调用。
- **失败**：`readyState = CLOSED`，`onerror` 和 `onclose` 被调用，`connect()` 抛出异常。

### 2.4 调用方感知

| 调用方 | 失败处理 |
|--------|----------|
| `createVncTransport` | `await transport.connect()` 抛异常 → 调用方收到 rejected Promise |
| `vmService.getVncTransport` | 同上 |
| `vncStream.connectStream` | `getVncTransport().catch(...)` 捕获，`notifySubscribers(state, 'error', ...)`，`state.status = 'error'` |
| `useVnc` | 通过 `createVncTransport` 获取 transport，若失败则 `doConnect` 的 try 捕获，`setStatus('failed')` |

**结论**：连接失败时，前端能通过 Promise 异常和 `onerror`/`onclose` 感知，错误路径完整。

### 2.5 潜在问题

1. **无超时**：`invoke('vnc_bridge_connect')` 无显式超时。P2P 建连可能较慢（10–30s），用户可能长时间无反馈。
2. **建议**：在 `connect()` 中增加超时包装，例如使用 `Promise.race` 与 `WS_CONFIG.CONNECTION_TIMEOUT`（30s）。

---

## 三、Bridge vs 本地 WebSocket：错误处理一致性

### 3.1 流程对比

| 步骤 | 本地模式 (WebSocket URL) | OTA 模式 (Bridge) |
|------|--------------------------|-------------------|
| 获取传输 | `get_vnc_proxy_url` → URL 字符串 | `getVncTransport` → `VncBridgeTransport` + `connect()` |
| 可用性检测 | `testWebSocket(url)` | 无（`connect()` 即检测） |
| 传给 RFB | `new RFB(container, url)` | `new RFB(container, transport)` |

### 3.2 vncStream 中的差异

```typescript
// vncStream.ts:132-149
state.transportOrUrl = await vmService.getVncTransport(agentId, deviceId).catch(...);

// 非 OTA 时测试 WebSocket 可用性（OTA 下 getVncTransport 已建立连接）
if (typeof state.transportOrUrl === 'string') {
  const wsAvailable = await testWebSocket(state.transportOrUrl);
  if (!wsAvailable) {
    state.transportOrUrl = null;
    throw new Error('VNC WebSocket not available');
  }
}
```

- **本地**：先拿 URL，再 `testWebSocket`；失败则 `throw`。
- **OTA**：`getVncTransport` 内部已 `await transport.connect()`，失败会抛异常，被 `.catch()` 捕获。

### 3.3 错误处理一致性

| 失败场景 | 本地模式 | OTA 模式 | 一致性 |
|----------|----------|----------|--------|
| 获取传输失败 | `getVncUrl` 抛异常 | `connect()` 抛异常 | ✅ 均进入 catch |
| 传输不可用 | `testWebSocket` 返回 false → throw | 无 testWebSocket | ⚠️ 见下 |
| catch 块 | `close()` Bridge（若有）、`state.transportOrUrl = null`、`status = 'error'`、重连 | 同上 | ✅ 一致 |

**OTA 无 testWebSocket**：OTA 下 `getVncTransport` 的 `connect()` 已建立 Bridge，成功即表示可用，因此不再做 `testWebSocket` 是合理的。失败时由 `connect()` 抛异常，同样进入 catch。

### 3.4 createVncTransport 与 vncStream 的 Bridge 失败路径

- **createVncTransport**：`await transport.connect()` 失败 → 抛异常 → 调用方（如 useVnc）在 try/catch 中处理。
- **vncStream**：`getVncTransport().catch(...)` 捕获 → `notifySubscribers(state, 'error', ...)`、`state.transportOrUrl = null`、`status = 'error'`。

两者在 Bridge 连接失败时都会进入错误路径，行为一致。

---

## 四、Bridge 断开：onclose 与 vnc_bridge:close

### 4.1 断开场景

| 场景 | 触发方 | 前端感知路径 |
|------|--------|--------------|
| 用户主动关闭 | 前端 | `transport.close()` → `invoke('vnc_bridge_close')` → `cleanup()` → `onclose?.({})` |
| 后端/代理关闭 | 后端 | Bridge 任务收到 WS Close/Err → `emit('vnc_bridge:{id}:close', reason)` → 前端 `unlistenClose` → `onclose?.({ reason })` |
| 后端进程崩溃 | 系统 | 无事件 | ❌ 前端无法感知 |

### 4.2 VncBridgeTransport.close() 与 vnc_bridge:close 对应关系

```typescript
// vncBridge.ts:99-108
close(): void {
  if (this.readyState === this.CLOSED || this.readyState === this.CLOSING) return;
  this.readyState = this.CLOSING;
  if (this.bridgeId) {
    invoke('vnc_bridge_close', { bridgeId: this.bridgeId });
  }
  this.cleanup();
  this.readyState = this.CLOSED;
  this.onclose?.({});
}
```

- **前端主动 close**：直接调用 `onclose?.({})`，不依赖 Tauri 事件。
- **后端主动 close**：通过 `vnc_bridge:{id}:close` 事件 → `unlistenClose` 回调 → `cleanup()` → `onclose?.({ reason })`。

### 4.3 后端 vnc_bridge_close 行为

```rust
// vnc_bridge.rs:212-218
pub async fn vnc_bridge_close(..., bridgeId: String) -> Result<(), String> {
    bridge_state.bridges.write().await.remove(&bridgeId);
    Ok(())
}
```

- 仅从 `bridges` 中移除，`tx` 被 drop。
- Bridge 任务中的 `rx.recv()` 会得到 `None`，但 `tokio::select!` 使用 `Some(data) = rx.recv()`，该分支在 `None` 时被禁用，任务继续等待 `ws_read.next()`。
- **结果**：Bridge 任务不会因 `vnc_bridge_close` 立即退出，WebSocket 连接会保持到对端关闭或超时，存在资源泄漏风险。

### 4.4 onclose 可靠性

| 场景 | onclose 是否触发 | 说明 |
|------|-----------------|------|
| 前端 close() | ✅ | 同步调用 `onclose?.({})` |
| VncProxy 关闭 WS | ✅ | Bridge 任务 emit close 事件 |
| P2P/网络错误 | ✅ | Bridge 任务 emit close 事件 |
| 后端进程崩溃 | ❌ | 无 IPC，前端无法感知 |
| Tauri WebView 被销毁 | ❌ | 同上 |

### 4.5 修复建议

1. **后端**：`vnc_bridge_close` 应通知 Bridge 任务主动关闭 WebSocket，例如通过 `CancellationToken` 或专用关闭 channel，避免连接长期挂起。
2. **前端**：可增加心跳或 `readyState` 轮询，用于检测「假连接」；或依赖 noVNC 的 disconnect 超时（若存在）。
3. **文档**：明确说明「后端异常退出时，前端可能无法及时感知断开」。

---

## 五、问题汇总与修复优先级

| 编号 | 严重程度 | 描述 | 建议 |
|------|----------|------|------|
| P1 | 中 | `vnc_bridge_close` 后 Bridge 任务不退出，WebSocket 连接可能泄漏 | 增加关闭信号（如 CancellationToken），让任务主动关闭 WS |
| P2 | 中 | `vnc_bridge_connect` 无超时 | 在 `connect()` 中增加 `Promise.race` 超时（如 30s） |
| P3 | 低 | 后端崩溃时前端无法感知断开 | 文档说明；可选：心跳或超时检测 |
| P4 | 低 | `shouldUseVncBridge` 使用 `isSecureContext` 而非 `isOtaOrigin` | 保持现状或改为 `isOtaOrigin() \|\| isSecureContext` 以明确语义 |

---

## 六、结论

1. **OTA 检测**：`shouldUseVncBridge()` 使用 `isSecureContext`，能覆盖 OTA 及所有 Mixed Content 场景，误判风险低。
2. **Bridge 连接失败**：`connect()` 的 catch 会设置 `onerror`/`onclose` 并抛异常，调用方能正确感知并进入错误处理。
3. **Bridge vs 本地**：vncStream 在 OTA 下跳过 `testWebSocket` 合理；Bridge 与本地模式的错误路径一致。
4. **Bridge 断开**：前端主动 close 时 `onclose` 可靠；后端关闭时通过 `vnc_bridge:close` 事件也能触发；后端崩溃时无法感知。`vnc_bridge_close` 存在 Bridge 任务不退出、WebSocket 泄漏的问题，建议增加显式关闭机制。
