# VNC Connection Failure in OTA Mode — Error Propagation Report

**Investigation focus**: What errors would the user see? Where could the flow fail silently or with wrong error message?

**Flow**: `useVNCConnection` / `vncStream.ts` → `vmService.getVncUrl(agentId, deviceId)` → `invoke('get_vnc_proxy_url')` → `new WebSocket(url)`

---

## 1. TauriRequiredFallback — When Does It Show?

**File**: `novaic-app/src/main.tsx`

```ts
function shouldShowTauriFallback(): boolean {
  const isOtaOrigin = OTA_ORIGINS.some((o) => location.origin === o);
  const hasTauri = '__TAURI__' in (window as Window & { __TAURI__?: unknown });
  return isOtaOrigin && !hasTauri;
}
```

**Shown when**:
- `location.origin` is in `OTA_ORIGINS` (`https://relay.gradievo.com`, `https://api.gradievo.com`)
- **and** `window.__TAURI__` is absent (pure browser, no Tauri webview)

**User sees**: "此页面需在 NovAIC App 内打开" — never reaches VNC flow.

**Implication**: In pure browser OTA, `invoke` would fail. The fallback prevents that by not rendering `App` at all. VNC failure investigation applies to **OTA + embedded webview** (has `__TAURI__`).

---

## 2. useVNCConnection — Error Handling & Silent Failures

**File**: `novaic-app/src/components/Visual/useVNCConnection.ts`

### checkWebSocket

```ts
const wsUrl = wsUrlRef.current || (await vmService.getVncUrl(agentId, deviceId ?? undefined));
// ...
const ws = new WebSocket(wsUrl);
await new Promise<void>((resolve, reject) => {
  const timeout = setTimeout(() => { ws.close(); reject(new Error('timeout')); }, WS_CONFIG.CONNECTION_TIMEOUT);
  ws.onopen = () => { ... resolve(); };
  ws.onerror = () => { ... reject(new Error('ws error')); };
});
```

**catch block** (lines 80–87):

```ts
} catch (e) {
  console.log('[VNC Connection] WebSocket not available, will retry...');
  setWsReady(false);
  setStatus(prev => prev === 'starting' ? prev : 'starting');
  return false;
}
```

**Critical finding**: `setErrorMsg` is **never called** in the catch block.

| Failure source | Result | User sees |
|----------------|--------|-----------|
| `invoke` fails (e.g. "VNC proxy not started yet", "No online VmControl device found") | `status = 'starting'`, `errorMsg = ''` | "Starting…" indefinitely, no error text |
| WebSocket timeout (30s) | Same | Same |
| WebSocket `onerror` | Same | Same |

**Silent failure**: Invoke and WebSocket failures are indistinguishable; both show "Starting…" with no error message.

### startVm

- `vmService.start` failure → `setStatus('error')`, `setErrorMsg(e.message || 'Failed to start VM')` ✓
- `checkWebSocket` failure (after start succeeds) → no `setErrorMsg` ✗

### refreshStatus / init

- `vmService.isRunning` failure → `status = 'unknown'`, no `errorMsg`
- `checkWebSocket` failure → starts 3s polling, no `errorMsg`

**Note**: `useVNCConnection` is not imported anywhere in the app — it's effectively dead code. The active flows are `useDeviceVNCConnection` and `VmUserVNCView`.

---

## 3. `vncStream.ts` — connectStream, testWebSocket, RFB Handlers

**File**: `novaic-app/src/services/vncStream.ts`

### getVncUrl (invoke) failure

```ts
state.wsUrl = await vmService.getVncUrl(agentId, deviceId).catch((err: any) => {
  notifySubscribers(state, 'error', err?.message || 'Failed to get VNC URL');
  state.status = 'error';
  notifySubscribers(state, 'status');
  throw err;
});
```

**Invoke failure is propagated** via `onError` with `err?.message || 'Failed to get VNC URL'`. ✓

### testWebSocket

```ts
const ws = new WebSocket(url);
ws.onerror = () => { clearTimeout(timeout); resolve(false); };
```

- On error: returns `false`, no `reject`. No `onError` call here.
- `connectStream` then does `state.wsUrl = null; throw new Error('VNC WebSocket not available')` → outer catch runs, `notifySubscribers(state, 'error', e.message || 'Connection failed')`. ✓

### RFB disconnect

- `wasConnected` → `status = 'disconnected'`
- `!wasConnected` → `status = 'error'`, `notifySubscribers(state, 'error', reason)` if `reason` present

**Note**: `subscribeToVNCStream` is **not used** anywhere in the app. Only `vncStream.ts` defines it; no component subscribes. So this error propagation path is currently unused.

---

## 4. useDeviceVNCConnection — Same Silent Failure Pattern

**File**: `novaic-app/src/components/Visual/useDeviceVNCConnection.ts`

### checkWebSocket (lines 55–73)

```ts
const url = wsUrlRef.current || await vmService.getVncUrl(deviceId);
// ...
} catch {
  setWsReady(false);
  setStatus(prev => prev === 'starting' ? prev : 'starting');
  return false;
}
```

**Same pattern**: `setErrorMsg` is never called. Invoke and WebSocket failures both result in `status = 'starting'` with no error message.

---

## 5. DeviceVNCView — What It Shows

**File**: `novaic-app/src/components/Visual/DeviceVNCView.tsx`

- `status === 'error'` → shows `errorMsg || 'Connection failed'` with Retry button ✓
- `status === 'starting'` → shows "Connecting to desktop…" with spinner
- `status === 'stopped'` / `unknown` → shows "VM is stopped" / "Waiting for VM…"

**When invoke fails in checkWebSocket**: `status` stays `starting` (never `error`). User sees "Connecting to desktop…" indefinitely.

---

## 6. VmUserVNCView — Correct Error Handling

**File**: `novaic-app/src/components/VM/VmUserVNCView.tsx`

```ts
try {
  wsUrl = await vmService.getVncUrl(`${deviceId}:${username}`);
} catch (e: any) {
  setConnState('error');
  setErrorMsg(e?.message ?? 'Failed to get VNC URL');
  return;
}
```

**Invoke failure is handled**: `connState = 'error'`, `errorMsg = e?.message ?? 'Failed to get VNC URL'`. User sees "Connection failed" with the actual error message. ✓

---

## 7. vm.ts — getVncUrl

**File**: `novaic-app/src/services/vm.ts`

```ts
async getVncUrl(agentId: string, deviceId?: string): Promise<string> {
  const url = await invoke<string>('get_vnc_proxy_url', { agentId, deviceId });
  return url;
}
```

- No `.catch` — errors propagate to caller.
- If invoke fails: `invoke` rejects with the Rust `Err` message (e.g. "VNC proxy not started yet", "No online VmControl device found. Ensure your PC is running NovAIC and connected.").

---

## 8. If invoke fails — does the frontend show a useful error?

| Component | Invoke failure handling | User-visible result |
|-----------|-------------------------|----------------------|
| **useVNCConnection** | Swallowed in catch, no `setErrorMsg` | "Starting…" indefinitely |
| **useDeviceVNCConnection** | Same | "Connecting to desktop…" indefinitely |
| **VmUserVNCView** | `setConnState('error')`, `setErrorMsg(e?.message ?? 'Failed to get VNC URL')` | Correct error message |
| **vncStream** (subscribeToVNCStream) | `notifySubscribers(state, 'error', ...)` | Correct, but **not used** |

---

## 9. WebSocket with undefined URL?

If `invoke` somehow returned `undefined` (e.g. Rust returns null), `getVncUrl` would resolve to `undefined`. Then:

- `new WebSocket(undefined)` → browser would throw or create invalid URL. In `checkWebSocket` / `testWebSocket` this would be caught by the outer catch.
- In `useDeviceVNCConnection` / `useVNCConnection`: same silent failure — no `setErrorMsg`, status stays `starting`.

---

## 10. Summary — Error Propagation Path

### Invoke failure vs WebSocket failure

| Failure type | useDeviceVNCConnection / useVNCConnection | VmUserVNCView |
|--------------|-------------------------------------------|---------------|
| **Invoke failure** | Silent: status `starting`, no error message | Shown: `errorMsg` with `e?.message` |
| **WebSocket timeout** | Silent: same | N/A (RFB handles its own errors) |
| **WebSocket error** | Silent: same | N/A |

### User-visible symptoms

| Symptom | Likely cause |
|---------|--------------|
| "Connecting to desktop…" or "Starting…" indefinitely | Invoke or WebSocket failure in `useDeviceVNCConnection` / `useVNCConnection` — error swallowed |
| "Connection failed" with specific message (e.g. "VNC proxy not started yet", "No online VmControl device found") | Invoke failure in `VmUserVNCView` — handled correctly |
| "此页面需在 NovAIC App 内打开" | OTA + pure browser (no `__TAURI__`) — expected fallback |

### Recommendations

1. **useDeviceVNCConnection** and **useVNCConnection**: In `checkWebSocket` catch block, set `setErrorMsg(e?.message ?? 'Connection failed')` and `setStatus('error')` when the failure is not retryable (e.g. invoke failure) or when retries are exhausted.
2. **Differentiate invoke vs WebSocket**: Consider setting `errorMsg` with distinct messages (e.g. "Failed to get VNC URL" vs "WebSocket connection failed") to aid debugging.
3. **vncStream**: `subscribeToVNCStream` is unused; either remove or wire it to a component that consumes `onError`.
