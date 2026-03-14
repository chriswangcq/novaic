# Device/Agent Switch Flow Analysis

Tracing what happens when the user switches device (`selectedDeviceId`) or agent (`currentAgentId`) in novaic-app.

---

## 1. Transport Cache Invalidation

### Cache Structure
- **Location**: `vncTransport.ts` — module-level `Map<string, VncBridgeTransport>`
- **Key**: `cacheKey(target)` = `${resourceId}|${pcClientId ?? ''}`

### When Cache Entry Is Removed

| Trigger | Mechanism |
|---------|-----------|
| **Explicit close** | `VncBridgeTransport.close()` → `_evictFromCache()` → `transportCache.delete(key)` |
| **Stale cached** | `createVncTransport` sees `cached.readyState !== OPEN` → `transportCache.delete(key)` before creating new |
| **Backend close** | `vnc_stream:close` event → `cleanup()` + `readyState=CLOSED`; entry stays until next `createVncTransport` for same key (then deleted as stale) |

### On Switch: No Proactive Invalidation
- Switching device/agent does **not** explicitly invalidate the old transport’s cache entry.
- Old transport is closed by `useVnc.doConnect` when it sees `prevTransport !== t` (new transport).
- `close()` → `_evictFromCache()` → cache entry removed.

---

## 2. AgentDesktopView / DeviceDesktopView: Mount vs Update

### Agent Switch (currentAgentId)

```
VisualPanel (or thumbnail)
  └── AgentDesktopView agentId={currentAgentId}
```

- **Unmount/remount**: **No** — same component instance.
- **Update**: `agentId` changes → `useAgentDevice(agentId)` fetches new binding → `vncTarget` changes → effect runs.

### Device Switch (selectedDeviceId) — DeviceManagerPage

```
DeviceManagerPage
  └── effectiveSelectedDevice ? (
        selectedVmUser
          ? DeviceDesktopView (vm_user)
          : DeviceVNCView (main) → DeviceDesktopView
      ) : empty state
```

| Switch Type | Unmount/Remount? |
|-------------|------------------|
| Device A (main) → Device B (main) | **No** — same component type, props update |
| Device A (vm_user) → Device B (vm_user) | **No** — same component type, props update |
| Device A (main) → Device A (vm_user) | **Yes** — `DeviceVNCView` ↔ `DeviceDesktopView` |
| Device A (vm_user) → Device A (main) | **Yes** — `DeviceDesktopView` ↔ `DeviceVNCView` |
| Tab: devices → chat | **Yes** — `DeviceManagerPage` unmounts |

### DeviceFloatingPanel
- Renders multiple `DeviceCard`s; each can show `DeviceDesktopView` or `VNCViewShared`.
- Driven by agent binding, not `selectedDeviceId`.
- Switching agent changes which devices are shown; switching `selectedDeviceId` does not affect floating panels.

---

## 3. createVncTransport: Old vs New Target During Switch

### Agent Switch

```
currentAgentId: A → B
  → useAgentDevice(B) fetches binding
  → vncTargetKey: "deviceA|pc1" → "deviceB|pc2"
  → useEffect([vncTargetKey]) runs
  → reqId = ++requestIdRef.current
  → createVncTransport(newTarget) starts (async)
```

- **Old target**: `createVncTransport` for old target is not re-triggered; any in-flight call is ignored via `reqId`.
- **New target**: `createVncTransport(newTarget)` runs; on resolve, `reqId === requestIdRef.current` → `setTransport(t)`.

### Device Switch (same component type)

```
selectedDeviceId: A → B
  → DeviceDesktopView/DeviceVNCView receives new props
  → vncTarget = buildVncTarget(props) changes
  → useEffect([vncTarget, ...]) runs
  → createVncTransport(newTarget) starts
```

- Same pattern: old in-flight calls ignored by `requestIdRef`, new transport set on success.

### Stale Result Guard
- Both views use `requestIdRef` so that when `createVncTransport` resolves, they only apply the result if `reqId === requestIdRef.current`.
- Fast switches: old promises resolve after a newer request; their results are discarded.

---

## 4. Flow Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ USER ACTION: Switch device (selectedDeviceId) or agent (currentAgentId)           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │ AGENT SWITCH          │               │ DEVICE SWITCH          │
        │ setCurrentAgentId(B)  │               │ setSelectedDeviceId(B) │
        └───────────────────────┘               └───────────────────────┘
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │ AgentDesktopView      │               │ DeviceManagerPage      │
        │ agentId prop changes  │               │ selectedDeviceId from  │
        │ (stays mounted)       │               │ store → selectedDevice│
        └───────────────────────┘               └───────────────────────┘
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │ useAgentDevice(B)     │               │ effectiveSelectedDev  │
        │ → vncTarget for B     │               │ → DeviceVNCView or    │
        └───────────────────────┘               │   DeviceDesktopView   │
                    │                           │   (props change or      │
                    │                           │   unmount if main↔vm)  │
                    │                           └───────────────────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
        ┌───────────────────────────────────────────────────────────────────────┐
        │ vncTargetKey changes (resourceId|pcClientId)                            │
        │ useEffect([vncTargetKey]) runs                                          │
        │   reqId = ++requestIdRef.current                                         │
        │   setTransport(null) if no target                                        │
        │   createVncTransport(newTarget) — async                                 │
        └───────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │ createVncTransport    │               │ transportCache         │
        │ - cacheKey(target)    │               │ - get(key): reuse if   │
        │ - cached? OPEN→reuse  │               │   OPEN else delete    │
        │ - else new transport  │               │ - set(key, transport)  │
        │ - connect()           │               │   on success           │
        └───────────────────────┘               └───────────────────────┘
                    │
                    ▼ (on resolve)
        ┌───────────────────────┐
        │ if reqId === current  │
        │   setTransport(t)     │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────────────────────────────────┐
        │ VncCanvas receives new transport                                        │
        │ useVnc(transport, containerRef) effect runs                             │
        │   canConnect? doConnect()                                               │
        └───────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────────────────────────────────────────────┐
        │ useVnc.doConnect()                                                      │
        │ 1. rfbRef.current?.disconnect()                                         │
        │ 2. prevTransport = lastTransportRef.current                             │
        │ 3. if prevTransport !== t → prevTransport.close()  ← OLD TRANSPORT     │
        │ 4. if t.readyState !== OPEN → skip (already closed)                     │
        │ 5. lastTransportRef = t                                                 │
        │ 6. new RFB(container, t)                                                │
        └───────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ prevTransport.close() │
        │ → _evictFromCache()   │
        │ → transportCache.delete(key)                                            │
        └───────────────────────┘
```

---

## 5. Potential Race Conditions & Instability

### R1: createVncTransport in-flight when switching again
- **Scenario**: User switches A→B→C quickly.
- **Behavior**: `requestIdRef` ensures only the latest result is applied; older promises are ignored.
- **Risk**: Low — stale results are discarded.

### R2: Old transport close vs new transport connect
- **Scenario**: New transport connects while old one is still closing.
- **Behavior**: `doConnect` closes `prevTransport` before using the new one; `close()` is synchronous (invoke + cleanup).
- **Risk**: Low — ordering is explicit.

### R3: useVnc effect cleanup vs doConnect
- **Scenario**: Effect re-runs (e.g. `transport` changes) while `doConnect` is running.
- **Behavior**: Cleanup only clears `retryTimerRef`; `disconnect` is done by the mount effect on unmount, not by this effect.
- **Risk**: Low — avoids closing transport on effect re-run.

### R4: transport closed before doConnect uses it
- **Scenario**: Unmount happens right after `setTransport(newT)`; mount effect runs `disconnect()` and closes the new transport.
- **Behavior**: `doConnect` checks `bridge.readyState !== OPEN` and skips if already closed.
- **Risk**: Low — guarded.

### R5: createVncTransport orphan / cache leak
- **Scenario**: User switches away before `createVncTransport` resolves; component unmounts or target changes.
- **Behavior**: Promise resolves, `setTransport` is either ignored (reqId) or runs on unmounted component. New transport may be cached but unused.
- **Risk**: Medium — orphan transport stays in cache until someone requests the same key (then evicted as stale) or it is closed. No explicit cleanup for abandoned in-flight requests.

### R6: Main ↔ vm_user switch (unmount/remount)
- **Scenario**: User switches from main to vm_user (or vice versa) for the same device.
- **Behavior**: `DeviceVNCView` unmounts, `DeviceDesktopView` mounts (or the reverse). Unmount runs `disconnect()` → `close()`.
- **Risk**: Low — normal lifecycle.

### R7: Tab switch (devices → chat)
- **Scenario**: User is viewing a device VNC and switches to chat.
- **Behavior**: `DeviceManagerPage` unmounts → `DeviceDesktopView`/`DeviceVNCView` unmount → `useVnc` unmount → `disconnect()` → `close()`.
- **Risk**: Low — normal lifecycle.

### R8: DeviceDesktopView maindesk — deviceStatus race
- **Scenario**: `deviceStatus` flips `stopped`↔`running` while `createVncTransport` is in progress.
- **Behavior**: Effect depends on `[vncTarget, isMaindesk, deviceStatus]`; when `deviceStatus !== 'running'`, effect sets `transport=null` and returns early. A previously started `createVncTransport` can still resolve and call `setTransport`.
- **Risk**: Medium — possible brief mismatch (transport for a target that is no longer considered running).

### R9: useAgentDevice / useDeviceVncTarget async race
- **Scenario**: `agentId` or `deviceId` changes while `getAgentBinding` or `devices.get` is in flight.
- **Behavior**: `agentIdRef.current !== requestFor` (or `deviceIdRef.current !== id`) guards; stale results are not applied.
- **Risk**: Low — guarded.

---

## 6. Summary

| Question | Answer |
|----------|--------|
| **Transport cache invalidation on switch** | Via `close()` → `_evictFromCache()`, or as stale entry when `createVncTransport` runs for same key. No proactive invalidation. |
| **AgentDesktopView/DeviceDesktopView unmount** | Agent switch: no. Device switch same type: no. Main↔vm_user or tab change: yes. |
| **createVncTransport old vs new** | New target triggers new `createVncTransport`; old in-flight calls ignored via `requestIdRef`. |
| **Old close vs new connect** | `doConnect` closes `prevTransport` before using new transport; ordering is explicit. |

### Main instability points
1. **R5**: Orphan transports from abandoned `createVncTransport` can remain in cache.
2. **R8**: `deviceStatus` changes can briefly leave `DeviceDesktopView` with a transport for a target that is no longer considered running.
