# VNC Frontend Flow Research: Maindesk vs Subuser

Research trace of VNC frontend components, transport acquisition, RFB options, retry logic, and behavioral differences between maindesk and subuser flows.

**Reference**: [docs/MAINDESK_VS_SUBUSER_VNC_ANALYSIS.md](./MAINDESK_VS_SUBUSER_VNC_ANALYSIS.md)

---

## 1. Component Trace

### 1.1 VNCViewShared

**File**: `novaic-app/src/components/Visual/VNCViewShared.tsx`

**Purpose**: Shared VNC connection for maindesk; multiple components (thumbnail + fullscreen) share one RFB connection via vncStream.

**Flow**:
```
VNCViewShared
  → streamKey = propDeviceId || agentId || ''
  → subscribeToVNCStream(streamKey, { onFrame, onStatusChange, onError })
  → vncStream.connectStream(agentId, deviceId?)
```

**Data source** (per DEVICE_SUBJECT_DESIGN.md):
- Maindesk: `device.id` + `binding.subject_type === 'main'`
- Uses `propDeviceId || agentId` as stream key; `agentId` from store `currentAgentId`

**Transport**: Does not call `getVncTransport` / `getVncUrl` directly. Delegates to `vncStream.connectStream()`.

---

### 1.2 DeviceVNCView

**File**: `novaic-app/src/components/Visual/DeviceVNCView.tsx`

**Purpose**: Live desktop view for a Device (Linux → noVNC RFB, Android → Scrcpy). Used in DeviceManagerPage split panel.

**Flow**:
```
DeviceVNCView
  → useDeviceVNCConnection(device)
  → returns [connState, connActions, transportOrUrl]
  → when status === 'running' && wsReady && transportOrUrl:
       new RFB(container, transportOrUrl, { shared: true, credentials: {} })
```

**Data source**: `device: Device` (device.id = maindesk VM id).

**Transport**: Via `useDeviceVNCConnection` → `getVncTransport(deviceId)` or `getVncUrl(deviceId)`.

---

### 1.3 VmUserVNCView

**File**: `novaic-app/src/components/VM/VmUserVNCView.tsx`

**Purpose**: TigerVNC desktop for a sub-user of a Linux VM. No start/stop controls — Xvnc lifecycle managed by systemd.

**Flow**:
```
VmUserVNCView
  → connect() on mount (useEffect)
  → transportOrUrl = await vmService.getVncTransport(`${deviceId}:${username}`)
  → new RFB(canvasRef.current, transportOrUrl, { wsProtocols: ['binary'] })
```

**Data source**: `deviceId`, `username` (from `binding.subject_id` when `subject_type === 'vm_user'`).

**Transport**: Direct call to `getVncTransport(\`${deviceId}:${username}\`)`.

---

### 1.4 useVNCConnection

**File**: `novaic-app/src/components/Visual/useVNCConnection.ts`

**Purpose**: VNC connection hook for agent-centric flow. Manages status, WebSocket probe, polling.

**Flow**:
```
useVNCConnection(agentId, onConnected, deviceId?)
  → checkWebSocket():
       if shouldUseVncBridge(): getVncTransport(agentId, deviceId)
       else: getVncUrl(agentId, deviceId) + WebSocket probe
  → if VM running but !connected: poll every 3s
  → returns [state, actions, wsUrlRef.current]
```

**Used by**: `VNCView.tsx` (note: some docs say useVNCConnection is dead code; VNCView imports it).

**Transport**: `getVncTransport(agentId, deviceId)` when OTA; `getVncUrl(agentId, deviceId)` otherwise.

---

### 1.5 useDeviceVNCConnection

**File**: `novaic-app/src/components/Visual/useDeviceVNCConnection.ts`

**Purpose**: Device-centric VNC connection hook. Mirrors useVNCConnection but uses `api.devices.*` for lifecycle.

**Flow**:
```
useDeviceVNCConnection(device)
  → checkWebSocket():
       if shouldUseVncBridge(): getVncTransport(deviceId)
       else: getVncUrl(deviceId) + WebSocket probe (WS_CONFIG.CONNECTION_TIMEOUT)
  → if device running but !connected: poll every 3s
  → returns [state, actions, transportOrUrl ?? wsUrlRef.current]
```

**Used by**: `DeviceVNCView`.

**Transport**: `getVncTransport(deviceId)` when OTA; `getVncUrl(deviceId)` otherwise.

---

### 1.6 vncStream

**File**: `novaic-app/src/services/vncStream.ts`

**Purpose**: Shared VNC stream manager. Single RFB connection per agentId, multiple subscribers (e.g. thumbnail + fullscreen).

**Flow**:
```
subscribeToVNCStream(agentId, subscriber, deviceId?)
  → connectStream(agentId, deviceId):
       transportOrUrl = getVncTransport(agentId, deviceId)
       if string: testWebSocket(url) before RFB
       new RFB(container, transportOrUrl, { shared: true, credentials: {} })
  → on disconnect: auto-reconnect after 2s, max 3 times
  → on connect error: auto-reconnect after 3s, max 3 times
```

**Used by**: `VNCViewShared` via `subscribeToVNCStream(streamKey, {...})` (deviceId not passed).

**Transport**: `getVncTransport(agentId, deviceId)` always (OTA or URL fallback inside vmService).

---

## 2. Transport Acquisition: getVncTransport vs getVncUrl

### 2.1 vmService.getVncTransport

**File**: `novaic-app/src/services/vm.ts`

```ts
async getVncTransport(agentId: string, deviceId?: string): Promise<string | VncBridgeTransport> {
  if (shouldUseVncBridge()) {
    const transport = new VncBridgeTransport(agentId, deviceId);
    await transport.connect();
    return transport;
  }
  return this.getVncUrl(agentId, deviceId);
}
```

- **OTA mode** (HTTPS / secure context): Returns `VncBridgeTransport` (Tauri IPC bridge).
- **Non-OTA**: Returns WebSocket URL from `getVncUrl`.

### 2.2 vmService.getVncUrl

```ts
async getVncUrl(agentId: string, deviceId?: string): Promise<string> {
  const url = await invoke<string>('get_vnc_proxy_url', { agentId, deviceId });
  return url;
}
```

- Invokes Tauri `get_vnc_proxy_url` → VNC proxy URL (ws://... or tunneled).

### 2.3 agentId / resource_id Format

| Flow       | agentId / resource_id      | Backend target (tunnel.rs)                          |
|-----------|----------------------------|-----------------------------------------------------|
| Maindesk  | `device.id` (vm_id)        | Unix socket `/tmp/novaic/novaic-vnc-{vm_id}.sock`   |
| Subuser   | `{deviceId}:{username}`    | TCP via port file → `127.0.0.1:{port}`              |

---

## 3. RFB Options Comparison

| Option        | VNCView / DeviceVNCView | vncStream       | VmUserVNCView      |
|---------------|-------------------------|-----------------|--------------------|
| shared        | `true`                  | `true`          | not set (default)  |
| credentials   | `{}`                    | `{}`            | not set            |
| wsProtocols   | not set                 | not set         | `['binary']`       |
| clipViewport  | `true`                  | `false`         | not set            |
| scaleViewport | `true`                  | `true`          | `true`             |
| resizeSession | `false`                 | `false`         | `false`            |
| focusOnClick  | `true`                  | `true`          | not set            |

**Differences**:
- Subuser uses `wsProtocols: ['binary']`; maindesk does not.
- Subuser does not set `shared` or `credentials`; maindesk sets both.
- Subuser does not set `clipViewport`; DeviceVNCView does; vncStream sets `false` (conflicts with scaleViewport).

---

## 4. Retry Logic Comparison

| Component / Flow      | WebSocket probe      | Poll retry (VM running, WS not ready) | Auto-reconnect on disconnect |
|-----------------------|----------------------|----------------------------------------|------------------------------|
| useVNCConnection      | Yes (checkWebSocket) | Yes, 3s interval                       | No (hook does not handle)    |
| useDeviceVNCConnection| Yes (checkWebSocket)  | Yes, 3s interval                       | No                           |
| vncStream             | Yes (testWebSocket)   | No (connect once)                      | Yes, 2s delay, max 3 times   |
| VmUserVNCView         | No                   | No                                     | No, manual Retry only        |

**Maindesk**: Probe + poll + vncStream auto-reconnect → robust against late VNC readiness.

**Subuser**: Single connect on mount, no probe, no poll, no auto-reconnect → fails if Xvnc/port file not ready; user must click Retry.

---

## 5. Behavioral Differences (Maindesk vs Subuser)

### 5.1 Connection Establishment

| Aspect              | Maindesk                                      | Subuser                                      |
|---------------------|-----------------------------------------------|----------------------------------------------|
| Entry point         | useDeviceVNCConnection / vncStream / useVNCConnection | VmUserVNCView.connect() on mount             |
| Pre-condition       | `status === 'running'` + `wsReady`            | None; connect immediately on mount           |
| WebSocket probe     | Yes (checkWebSocket / testWebSocket)          | No                                           |
| Poll retry          | Yes (3s) when VM running but WS not ready     | No                                           |
| Auto-reconnect      | vncStream: 2s, max 3                          | No                                           |
| Manual retry        | Retry button in error state                   | Retry / Reconnect button                     |

### 5.2 Backend Timing

- **Maindesk**: Unix socket `/tmp/novaic/novaic-vnc-{vm_id}.sock` typically exists soon after VM start.
- **Subuser**: TCP via `/tmp/novaic/share-{vm_id}/vnc-{username}.port`; depends on user login, Xvnc start, and port file write. More timing-sensitive.

### 5.3 Error Handling

| Failure type        | Maindesk (useDeviceVNCConnection)     | Subuser (VmUserVNCView)                          |
|---------------------|--------------------------------------|--------------------------------------------------|
| getVncTransport fail| setStatus('starting'), retry poll    | setConnState('error'), setErrorMsg, show Retry   |
| RFB connect fail    | status stays starting, retry        | setConnState('error'), setErrorMsg, show Retry   |
| Disconnect           | vncStream auto-reconnect (if used)    | setConnState('error'), show Reconnect            |

**Note**: useDeviceVNCConnection / useVNCConnection do not set `errorMsg` when `getVncTransport` / `getVncUrl` fails; the error is swallowed in the catch block and status stays `'starting'` with retry polling. VmUserVNCView correctly surfaces errors to the user.

### 5.4 State Machine

| Maindesk (useDeviceVNCConnection) | Subuser (VmUserVNCView) |
|----------------------------------|-------------------------|
| unknown → stopped → starting → running / error | connecting → connected / error / disconnected |

### 5.5 Lifecycle Controls

| Maindesk | Subuser |
|----------|---------|
| Start/Stop VM via api.devices.start/stop | No; Xvnc managed by systemd |
| View-only toggle (Linux) | No (not implemented) |

---

## 6. Call Graph Summary

```
MAINDESK (device.id, subject_type='main'):
  DeviceVNCView → useDeviceVNCConnection(device)
    → getVncTransport(deviceId) or getVncUrl(deviceId)
    → checkWebSocket + 3s poll
    → RFB(container, transportOrUrl, { shared, credentials, clipViewport })

  VNCViewShared → subscribeToVNCStream(streamKey)
    → vncStream.connectStream(agentId)
      → getVncTransport(agentId, deviceId)
      → testWebSocket (if URL)
      → RFB(container, transportOrUrl, { shared, credentials })
      → auto-reconnect on disconnect

SUBUSER (deviceId, username, subject_type='vm_user'):
  VmUserVNCView → connect() on mount
    → getVncTransport(`${deviceId}:${username}`)
    → RFB(canvas, transportOrUrl, { wsProtocols: ['binary'] })
    → no probe, no poll, no auto-reconnect
```

---

## 7. File Index

| File | Responsibility |
|------|----------------|
| `novaic-app/src/components/Visual/VNCViewShared.tsx` | Maindesk shared stream view (vncStream subscriber) |
| `novaic-app/src/components/Visual/DeviceVNCView.tsx` | Device maindesk view (useDeviceVNCConnection + RFB) |
| `novaic-app/src/components/Visual/VNCView.tsx` | Agent maindesk view (useVNCConnection + RFB) |
| `novaic-app/src/components/VM/VmUserVNCView.tsx` | Subuser TigerVNC view |
| `novaic-app/src/components/Visual/useVNCConnection.ts` | Agent VNC connection hook |
| `novaic-app/src/components/Visual/useDeviceVNCConnection.ts` | Device VNC connection hook |
| `novaic-app/src/services/vncStream.ts` | Shared VNC stream (subscribe/connect/reconnect) |
| `novaic-app/src/services/vm.ts` | getVncTransport, getVncUrl |
| `novaic-app/src/services/vncBridge.ts` | VncBridgeTransport, shouldUseVncBridge |
| `novaic-app/src/config/index.ts` | WS_CONFIG.CONNECTION_TIMEOUT (30s) |

---

## 8. Recommendations (from MAINDESK_VS_SUBUSER_VNC_ANALYSIS)

1. **Subuser retry**: Add poll retry or auto-reconnect for VmUserVNCView when Xvnc/port file may not be ready yet.
2. **RFB options**: Consider aligning `shared`, `credentials`, `clipViewport` between maindesk and subuser.
3. **wsProtocols**: Evaluate whether `wsProtocols: ['binary']` is required for subuser or can be unified.
4. **Pre-condition**: Optionally add a readiness check (e.g. port file existence) before connecting for subuser.
