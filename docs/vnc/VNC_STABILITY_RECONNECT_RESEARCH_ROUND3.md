# 第三轮调研（深层）：VNC 稳定性与重连机制

**日期**：2026-03-12  
**范围**：vnc_proxy 超时与 Close reason、vncStream 重试策略、transportError 用户反馈、已知问题与已修复项

---

## 一、vnc_proxy 30s 超时与 Close reason

### 1.1 超时配置

| 常量 | 值 | 位置 |
|------|-----|------|
| `WS_UPGRADE_TIMEOUT` | 30s | `vnc_proxy.rs:63` |

```rust
/// WebSocket upgrade timeout: P2P + relay + tunnel can take time; abort if stuck.
const WS_UPGRADE_TIMEOUT: Duration = Duration::from_secs(30);
```

### 1.2 VNC handler：超时发送 Close reason ✅ 已修复

**实现**（`vnc_proxy.rs:178-219`）：

- 使用 `Arc<Mutex<Option<socket>>>` 在 handler 层持有 WebSocket 引用
- `tokio::select!` 竞争：`route_fut` vs `timeout_fut`
- 超时分支：`tokio::time::sleep(WS_UPGRADE_TIMEOUT)` 后，若 socket 仍在 guard 中，调用 `send_ws_close_with_reason(&mut ws, "VNC connection timed out (30s)")`

```rust
// P0-2: 超时时发送 Close reason，前端可显示明确错误
let socket = Arc::new(tokio::sync::Mutex::new(Some(socket)));
// ...
let timeout_fut = async move {
    tokio::time::sleep(WS_UPGRADE_TIMEOUT).await;
    let mut guard = socket.lock().await;
    if let Some(mut ws) = guard.take() {
        send_ws_close_with_reason(&mut ws, "VNC connection timed out (30s)").await;
    }
};
tokio::select! {
    r = route_fut => { /* ... */ }
    _ = timeout_fut => {
        tracing::error!("[VncProxy] Timeout (30s) device=... agent=...");
    }
}
```

**结论**：VNC 30s 超时时会发送带 reason 的 Close 帧，前端可展示 "VNC connection timed out (30s)"。

### 1.3 Scrcpy handler：超时未发送 Close reason ❌ 未修复

**实现**（`vnc_proxy.rs:224-234`）：

```rust
match tokio::time::timeout(WS_UPGRADE_TIMEOUT, route_scrcpy(socket, ...)).await {
    Ok(Ok(())) => {}
    Ok(Err(e)) => tracing::error!("[ScrcpyProxy] Error ...");  // route_scrcpy 内部会 send_ws_close
    Err(_) => tracing::error!("[ScrcpyProxy] Timeout (30s) ...");  // 仅日志，无 Close reason
}
```

- 超时触发时 `route_scrcpy` future 被取消，socket 随之 drop
- **未调用** `send_ws_close_with_reason`
- Scrcpy 前端会收到 abrupt close，无明确超时提示

### 1.4 route_vnc 内各错误路径：均已发送 Close reason ✅

| 错误点 | 文件行号 | 行为 |
|--------|----------|------|
| `get_or_create_local_conn` 失败 | 312 | `send_ws_close_with_reason(&mut ws, e.to_string())` |
| `open_vnc_stream` 失败（本地） | 320 | 同上 |
| `get_or_create_remote_conn` 失败 | 336 | 同上 |
| `open_vnc_stream` 失败（远端） | 344 | 同上 |
| `bridge_ws_quic` 内 QUIC 错误 | 361, 369 | 同上 |
| `open_vnc_stream` / `open_scrcpy_stream` 失败 | 438, 446 | 同上 |

### 1.5 send_ws_close_with_reason 实现

```rust
// vnc_proxy.rs:290-301
async fn send_ws_close_with_reason(ws: &mut axum::extract::ws::WebSocket, reason: impl AsRef<str>) {
    let reason_str = reason.as_ref();
    let truncated = if reason_str.len() > 120 {
        format!("{}...", &reason_str[..117])
    } else {
        reason_str.to_string()
    };
    let frame = CloseFrame { code: WS_CLOSE_INTERNAL_ERROR, reason: truncated.into() };
    let _ = ws.send(Message::Close(Some(frame))).await;
}
```

- Close code: 1011 (Internal Error)
- reason 最大 123 字节，超长会截断

---

## 二、vncStream 重试策略

### 2.1 配置参数

| 参数 | 值 | 来源 |
|------|-----|------|
| `VNC_RETRY_DELAY_MS` | 2000 | `config/index.ts` |
| `VNC_MAX_RETRIES` | 5 | `config/index.ts` |

### 2.2 重试次数与退避

- **最大重试**：5 次（`VNC_MAX_RETRIES`）
- **退避公式**：`delay = VNC_RETRY_DELAY_MS * Math.pow(2, state.retryCount - 1)`
- **实际延迟**：2s, 4s, 8s, 16s, 32s（指数退避）

```typescript
// vncStream.ts:228-236 (disconnect 分支)
if (state.subscribers.size > 0 && state.retryCount < VNC_MAX_RETRIES) {
  state.retryCount++;
  const delay = VNC_RETRY_DELAY_MS * Math.pow(2, state.retryCount - 1);
  console.log(`[VNCStream] Scheduling reconnect for ${streamKey} (${state.retryCount}/${VNC_MAX_RETRIES}) in ${delay}ms`);
  state.retryTimer = setTimeout(() => {
    if (state && state.subscribers.size > 0) {
      connectStream(streamKey, pcId);
    }
  }, delay);
}
```

### 2.3 触发条件

| 场景 | 是否触发重试 | 条件 |
|------|--------------|------|
| RFB `disconnect`（非 clean 或 reason 存在） | ✅ | `state.subscribers.size > 0 && retryCount < 5` |
| `getVncTransport` 失败 / RFB 初始化 catch | ✅ | 同上 |
| `securityfailure` | ❌ | 不重试 |
| 用户主动 disconnectStream | ❌ | 清除 retryTimer |

### 2.4 与 useVnc 一致性

| 项目 | vncStream | useVnc |
|------|-----------|--------|
| 最大重试 | 5 次 | 5 次 |
| 退避策略 | 2s × 2^(n-1) | 2s × 2^n |
| 配置来源 | `WS_CONFIG` | `WS_CONFIG` |

**结论**：vncStream 与 useVnc 重试策略已统一（P1-1 已修复）。

---

## 三、transportError 时的用户反馈

### 3.1 createVncTransport 失败场景

- invoke 失败（如 VNC proxy 未启动、P2P 失败）
- `VncBridgeTransport.connect` 失败（如 WebSocket 连接超时）

### 3.2 AgentDesktopView ✅ 有 Retry

```tsx
// AgentDesktopView.tsx:88-111
const retryTransport = useCallback(() => {
  setTransportError(null);
  if (vncTarget) {
    createVncTransport(vncTarget)
      .then((t) => setTransport(t))
      .catch((e) => setTransportError(e instanceof Error ? e.message : 'Failed to create transport'));
  }
}, [vncTarget]);

if (transportError) {
  return (
    <div className="flex flex-col h-full items-center justify-center bg-black text-red-400 gap-3">
      <AlertCircle size={36} />
      <p className="text-sm">{transportError}</p>
      <button onClick={retryTransport} className="...">
        <RefreshCw size={14} /> Retry
      </button>
    </div>
  );
}
```

### 3.3 DeviceDesktopView ✅ 有 Retry

```tsx
// DeviceDesktopView.tsx:272-286
if (transportError) {
  return (
    <div className="flex flex-col h-full items-center justify-center bg-black text-red-400 gap-3">
      <AlertCircle size={36} />
      <p className="text-sm">{transportError}</p>
      <button onClick={retryTransport} className="...">
        <RefreshCw size={14} /> Retry
      </button>
    </div>
  );
}
```

### 3.4 VncConnectionOverlay（useVnc 路径）

- `status === 'failed'`：显示 "Connection failed" + errorMsg + Retry 按钮（需 `transportReady=true`）
- `status === 'reconnecting'`：显示 "Reconnecting…" + errorMsg，**无 Retry 按钮**（避免与自动重连竞态）

**结论**：transportError 时 AgentDesktopView / DeviceDesktopView 均有 Retry 按钮（P0-3 已修复）。

---

## 四、useVnc 对 disconnect reason 的读取

```typescript
// useVnc.ts:113-134
rfb.addEventListener('disconnect', ((e: Event & { detail?: { clean?: boolean; reason?: string } }) => {
  const reason = e?.detail?.reason ?? '';
  // ...
  if (retryCountRef.current >= MAX_RETRIES) {
    setStatus('failed');
    setErrorMsg(reason || 'Connection lost, max retries exceeded');
  }
}) as EventListener);
```

- **已读取** `e?.detail?.reason`，后端发送的 Close reason 会优先展示
- 依赖 noVNC/WebSocket 将 Close 帧的 reason 传递到 disconnect 事件的 `detail.reason`
- vnc_proxy 超时发送的 "VNC connection timed out (30s)" 理论上可被展示（需 noVNC 正确透传）

---

## 五、VNC 稳定性：已知问题 + 已修复项

### 5.1 已修复项

| # | 问题 | 修复状态 | 说明 |
|---|------|----------|------|
| P0-2 | vnc_proxy 30s 超时无 Close reason | ✅ 已修复 | VNC handler 使用 select + Arc<Mutex<socket>>，超时前发送 `send_ws_close_with_reason` |
| P0-3 | transportError 无 Retry | ✅ 已修复 | AgentDesktopView / DeviceDesktopView 均有 Retry 按钮 |
| P0-1 | useVnc clean 误判不重连 | ✅ 已修复 | 使用 `userInitiatedDisconnectRef`，不再依赖 `e.detail?.clean` |
| P1-1 | vncStream 重试 3 次、固定 2s | ✅ 已修复 | 改为 5 次、指数退避（2s, 4s, 8s, 16s, 32s） |
| P1-2 | vncStream testWebSocket | ✅ 已修复 | 已移除 testWebSocket，依赖后端 ensure_vnc_endpoint |
| P1-3 | vncStream 未接入 DeviceStatusStore | ✅ 已修复 | connect 时 incrementVncConnectionCount，disconnect 时 decrement |
| P1-4 | vncStream 无 requestId 竞态 | ✅ 已修复 | 增加 connectRequestId 校验，StreamState 持久化 deviceId |
| P0-6 | reconnectVNCStream 未传 deviceId | ✅ 已修复 | 支持可选 pcClientId 参数，StreamState.deviceId 持久化 |
| 3.1/3.2 | send_ws_close 带 reason | ✅ 已实现 | route_vnc 内所有错误路径均调用 `send_ws_close_with_reason` |
| reconnecting UI | 重连中显示 "Connection failed" | ✅ 已修复 | VncConnectionOverlay 区分 reconnecting / failed，reconnecting 显示 "Reconnecting…" |
| P1-5 | createVncTransport 无超时 | ✅ 已修复 | `VNC_TRANSPORT_TIMEOUT_MS: 30000`，vncTransport.ts 中 30s 超时 reject |

### 5.2 已知问题（未修复或待验证）

| # | 问题 | 严重度 | 说明 |
|---|------|--------|------|
| Scrcpy 30s 超时无 Close reason | 中 | scrcpy_handler 仍用 `tokio::time::timeout`，超时分支不发送 Close |
| 30s 可能不足 | 中 | 远端 + subuser 且 port 未就绪时，P2P(10–30s) + ensure_vnc_endpoint(0–30s) 易超时 |
| noVNC reason 透传 | 低 | 需验证 noVNC 是否将 WebSocket Close reason 传到 disconnect 的 detail.reason |
| 错误文案中英混用 | 低 | "Connection lost, max retries exceeded" 等为英文 |
| doConnect 静默 return | 低 | `!t \|\| !containerRef.current` 时静默 return，当前 transportReady=false 时 Retry 不显示，部分缓解 |

### 5.3 建议后续修复

1. **Scrcpy 超时**：将 scrcpy_handler 改为与 vnc_handler 相同的 select + Arc<Mutex<socket>> 模式，超时时发送 Close reason
2. **超时延长**：考虑远端 + subuser 场景将 WS_UPGRADE_TIMEOUT 延长至 60s，或根据 `is_remote + subject_type` 动态设置
3. **noVNC 验证**：在 30s 超时场景下抓包/日志确认 disconnect 事件是否携带 reason

---

## 六、关键代码索引

| 文件 | 职责 |
|------|------|
| `novaic-app/src-tauri/src/vnc_proxy.rs` | 30s 超时、send_ws_close_with_reason、VNC/Scrcpy handler |
| `novaic-app/src/services/vncStream.ts` | 5 次指数退避重试、connectRequestId、deviceId 持久化 |
| `novaic-app/src/hooks/useVnc.ts` | 5 次指数退避、disconnect reason 读取、userInitiatedDisconnectRef |
| `novaic-app/src/components/Visual/AgentDesktopView.tsx` | transportError + Retry |
| `novaic-app/src/components/Visual/DeviceDesktopView.tsx` | transportError + Retry |
| `novaic-app/src/components/Visual/VncConnectionOverlay.tsx` | reconnecting / failed 区分、Retry 按钮 |
| `novaic-app/src/config/index.ts` | VNC_RETRY_DELAY_MS、VNC_MAX_RETRIES、VNC_TRANSPORT_TIMEOUT_MS |
