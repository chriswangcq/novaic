# VNC disconnect 误关新 transport 分析

## 1. DeviceDesktopView → useVnc 的 transport 传递链

```
DeviceDesktopView
  ├── useMemo: vncTarget = buildVncTarget(props)
  ├── useEffect [vncTarget, isMaindesk, deviceStatus]:
  │     createVncTransport(vncTarget) → setTransport(t)
  └── VncCanvas transport={transport}
        └── useVnc(transport, containerRef, { containerReady })
```

- **DeviceDesktopView** 在 effect 中根据 `vncTarget`、`isMaindesk`、`deviceStatus` 调用 `createVncTransport`，得到 transport 后 `setTransport(t)`。
- **VncCanvas** 接收 `transport`，通过 ref callback 维护 `containerReady`，将 `transport` 和 `containerReady` 传给 `useVnc`。
- **useVnc** 在 effect 中根据 `canConnect = hasTransport && containerReady && hasContainer` 决定 `doConnect()` 或 `disconnect()`。

---

## 2. 两次 vnc_stream_connect 的可能来源

| 来源 | 说明 |
|------|------|
| 1. effect 依赖变化 | `[vncTarget, isMaindesk, deviceStatus]` 变化 → 重新 `createVncTransport`，requestId 竞态下可能产生 T1、T2 |
| 2. 组件重新挂载 | 路由切换、Agent 切换导致 DeviceDesktopView 卸载再挂载 |
| 3. deviceStatus 变化 | `starting` → `running` 触发 effect 重跑，从 `setTransport(null)` 变为 `createVncTransport` |
| 4. vncTarget 引用变化 | `useMemo` 依赖 `[props]`，props 引用变化导致 vncTarget 变，effect 重跑 |

---

## 3. Bug：disconnect 误关新 transport

### 3.1 disconnect 当前逻辑

```typescript
// useVnc.ts:71-74
const t = lastTransportRef.current ?? transportRef.current;
if (t && typeof t !== 'string' && 'close' in t) {
  (t as VncBridgeTransport).close();
}
lastTransportRef.current = null;
```

- `lastTransportRef`：在 `doConnect` 中赋值为当前正在使用的 transport。
- `transportRef`：每次 render 赋值为当前 props 传入的 transport。

当 `lastTransportRef.current` 为 `null` 时，会回退到 `transportRef.current` 并对其调用 `close()`。

### 3.2 问题场景

**场景：首次拿到新 transport T2，但 `canConnect` 为 false**

1. VncCanvas 首次渲染：`transport=null`，`containerReady=false`（useState 初始值）
2. useVnc effect：`transport=null` → `canConnect=false` → `disconnect()`，此时无 transport，无问题
3. 父组件 `createVncTransport` 完成，`setTransport(T2)`
4. VncCanvas 再次渲染：`transport=T2`
5. **时序关键点**：ref callback `setContainerRef(el)` 会同步设置 `containerRef.current = el`，但 `setContainerReady(!!el)` 是异步 state 更新
6. 因此存在一帧：`transport=T2`、`containerRef.current` 已有值，但 `containerReady` 仍为 `false`
7. useVnc effect：`hasTransport=true`，`containerReady=false` → `canConnect=false` → `disconnect()`
8. 此时：`lastTransportRef.current = null`（从未对 T2 执行过 `doConnect`），`transportRef.current = T2`
9. `t = lastTransportRef.current ?? transportRef.current = T2`
10. 对 T2 调用 `close()` → **误关尚未使用的新 transport**

### 3.3 后果

- 新 transport T2 被提前关闭，触发 `vnc_stream_close`
- 后续 `containerReady` 变为 true 时，effect 再跑 `doConnect`，但 T2 已 closed，`readyState !== OPEN`，连接失败
- 表现为：两次 `vnc_stream_connect`，第一个（T1）在切换时被正确关闭，第二个（T2）被 `disconnect` 误关

---

## 4. 修复方案

**原则**：`disconnect` 只应关闭**已经通过 doConnect 使用过的** transport，即 `lastTransportRef`。未使用过的 transport（`lastTransportRef === null`）不应被关闭。

### 4.1 修改 disconnect

```typescript
const disconnect = useCallback(() => {
  userInitiatedDisconnectRef.current = true;
  if (retryTimerRef.current) {
    clearTimeout(retryTimerRef.current);
    retryTimerRef.current = null;
  }
  if (rfbRef.current) {
    try {
      rfbRef.current.disconnect();
    } catch { /* ignore */ }
    rfbRef.current = null;
  }
  // 仅关闭已使用的 transport，不关闭尚未 doConnect 的新 transport
  const t = lastTransportRef.current;
  if (t && typeof t !== 'string' && 'close' in t) {
    (t as VncBridgeTransport).close();
  }
  lastTransportRef.current = null;
  setStatus('disconnected');
  setErrorMsg('');
}, []);
```

**改动**：`const t = lastTransportRef.current ?? transportRef.current` → `const t = lastTransportRef.current`

### 4.2 行为对比

| 场景 | 修改前 | 修改后 |
|------|--------|--------|
| 已用 T1，现无 transport | 关 T1 ✓ | 关 T1 ✓ |
| 已用 T1，现为 T2 且 canConnect | doConnect 关 T1、用 T2 ✓ | 同左 ✓ |
| 已用 T1，现为 T2 且 canConnect=false | disconnect 关 T1 ✓ | 关 T1 ✓ |
| **从未用过，现为 T2 且 canConnect=false** | **误关 T2 ✗** | **不关 T2 ✓** |
| 组件卸载 | mount effect cleanup 调 disconnect，关 lastTransportRef ✓ | 同左 ✓ |

---

## 5. 结论

- **Bug 确认**：当 `canConnect=false` 时调用 `disconnect`，若 `lastTransportRef` 为 null 而 `transportRef` 为新 transport，会错误关闭该新 transport。
- **根因**：`disconnect` 使用 `lastTransportRef ?? transportRef`，在「尚未 doConnect 的新 transport」场景下误关。
- **修复**：`disconnect` 只关闭 `lastTransportRef.current`，不再回退到 `transportRef.current`。
