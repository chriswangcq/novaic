# useVnc Effect 与 Disconnect 逻辑分析

## 问题现象

- transport 建立后很快被 close
- `send_count=0`（RFB 握手前即关闭）

## 代码路径概览

```
DeviceDesktopView
  └─ createVncTransport() → setTransport(t)
  └─ VncCanvas(transport={t})
       └─ useVnc(transport, containerRef, { containerReady })
            └─ useEffect([transport, containerReady, doConnect, disconnect])
```

---

## 1. containerReady 时序与 effect 首次运行

### 1.1 VncCanvas 的 containerReady 初始化

```29:34:novaic-app/src/components/Visual/VncCanvas.tsx
  const [containerReady, setContainerReady] = useState(false);
  const setContainerRef = useCallback((el: HTMLDivElement | null) => {
    (containerRef as React.MutableRefObject<HTMLDivElement | null>).current = el;
    setContainerReady(!!el);
  }, []);
  const { status, errorMsg, connect } = useVnc(transport, containerRef, { ...options, containerReady });
```

- 初始 `containerReady = false`
- `setContainerRef` 在 DOM 挂载后由 ref callback 调用，此时才 `setContainerReady(true)`
- ref callback 在 commit 阶段执行，会触发一次新的 state 更新

### 1.2 React 执行顺序

1. 首次 render：`containerReady=false`，`transport` 可能已有值
2. commit：ref callback 执行 → `setContainerReady(true)` 入队
3. **useEffect 在 commit 之后执行，仍使用当前 render 的 state**
4. 因此 effect 第一次运行时的 `containerReady` 是 `false`

### 1.3 结论

**首次 effect 运行时，`containerReady` 几乎一定是 `false`，即使 DOM 已挂载。**

---

## 2. 问题根因：else 分支中的 disconnect() 误关 transport

### 2.1 连接 effect 逻辑

```184:201:novaic-app/src/hooks/useVnc.ts
  useEffect(() => {
    const hasTransport = !!transport;
    const hasContainer = !!containerRef.current;
    const canConnect = hasTransport && containerReady && hasContainer;
    console.log(`${VNC_FLOW} [3-useVnc] effect 运行 transport=${hasTransport} containerReady=${containerReady} containerRef=${hasContainer} canConnect=${canConnect}`);
    if (canConnect) {
      doConnect();
    } else {
      if (!hasTransport) console.log(`${VNC_FLOW} [3-useVnc] effect 跳过：无 transport`);
      else if (!containerReady) console.log(`${VNC_FLOW} [3-useVnc] effect 跳过：containerReady=false`);
      else if (!hasContainer) console.log(`${VNC_FLOW} [3-useVnc] effect 跳过：无 containerRef`);
      disconnect();   // ← 问题点
    }
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
      // 仅清理定时器；disconnect 由 mount effect 的 unmount 负责，避免 effect 因 doConnect 依赖重跑时误关 transport
    };
  }, [transport, containerReady, doConnect, disconnect]);
```

### 2.2 disconnect 实现

```58:77:novaic-app/src/hooks/useVnc.ts
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
    const t = lastTransportRef.current ?? transportRef.current;
    if (t && typeof t !== 'string' && 'close' in t) {
      (t as VncBridgeTransport).close();
    }
    lastTransportRef.current = null;
    setStatus('disconnected');
    setErrorMsg('');
  }, []);
```

- `t = lastTransportRef.current ?? transportRef.current`
- 若从未执行过 `doConnect`，`lastTransportRef.current` 为 `null`，则 `t = transportRef.current`
- `transportRef.current` 在每次 render 时同步更新：`transportRef.current = transport`

### 2.3 致命时序

| 步骤 | 状态 | 行为 |
|-----|------|------|
| 1 | `transport=T`，`containerReady=false` | effect 运行，`canConnect=false` |
| 2 | else 分支执行 | `disconnect()` |
| 3 | `lastTransportRef=null`，`transportRef=T` | `t=T`，调用 `T.close()` |
| 4 | 后续 `setContainerReady(true)` | 触发第二次 effect |
| 5 | `canConnect=true` | `doConnect()` |
| 6 | doConnect 内检查 | `bridge.readyState !== OPEN`，transport 已被关闭，直接 return |

**结论：在 `containerReady` 仍为 `false` 的首次 effect 中，`disconnect()` 会关闭尚未被 RFB 使用的 transport。**

---

## 3. React StrictMode 双 mount 的叠加影响

### 3.1 StrictMode 已启用

```60:64:novaic-app/src/main.tsx
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      {needsTauriFallback ? <TauriRequiredFallback /> : <App />}
    </React.StrictMode>
  );
```

### 3.2 mount effect 的 cleanup

```167:174:novaic-app/src/hooks/useVnc.ts
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [disconnect]);
```

### 3.3 StrictMode 下的时间线

| 阶段 | 事件 |
|------|------|
| Mount 1 | VncCanvas 挂载，effect 运行 |
| | 若 `containerReady=false` → `disconnect()` 关闭 transport（问题 2） |
| | 若 `containerReady=true` 且 `doConnect()` 已执行 → `lastTransportRef=T` |
| Unmount 1 | StrictMode 触发 unmount |
| | mount effect cleanup → `disconnect()` → 关闭 `lastTransportRef` / `transportRef` |
| Remount 2 | VncCanvas 再次挂载 |
| | `transport` 引用不变（DeviceDesktopView 未 unmount） |
| | `doConnect()` 再次执行 |
| | `bridge.readyState !== OPEN`（已被 cleanup 关闭）→ 直接 return，status='failed' |

**结论：StrictMode 的 unmount 会通过 mount effect 的 cleanup 调用 `disconnect()`，关闭 transport；remount 时仍使用同一已关闭的 transport。**

---

## 4. Effect 依赖与重复运行

### 4.1 依赖数组

```202:202:novaic-app/src/hooks/useVnc.ts
  }, [transport, containerReady, doConnect, disconnect]);
```

- `doConnect`：`[scaleViewport, clipViewport, viewOnly]`，通常稳定
- `disconnect`：`[]`，稳定
- 实际会触发重跑的是：`transport`、`containerReady`

### 4.2 典型重跑序列

1. `containerReady: false → true`：先 `disconnect()`（误关），再 `doConnect()`
2. `transport: null → T`：先 `disconnect()`（无 transport 时无害），再 `doConnect()`
3. `transport: T → null`：`disconnect()` 关闭旧 transport，符合预期

问题集中在 `containerReady` 从 `false` 变为 `true` 时，第一次 effect 的 `disconnect()` 会关闭尚未使用的 transport。

---

## 5. disconnect 关闭的是新还是旧 transport？

```70:74:novaic-app/src/hooks/useVnc.ts
    const t = lastTransportRef.current ?? transportRef.current;
    if (t && typeof t !== 'string' && 'close' in t) {
      (t as VncBridgeTransport).close();
    }
```

- `transportRef.current` 在 render 时同步更新，始终是当前 props 的 `transport`
- `lastTransportRef.current` 仅在 `doConnect` 中设置，表示“正在使用”的 transport

| 场景 | lastTransportRef | transportRef | 实际关闭 |
|------|------------------|--------------|----------|
| 从未 doConnect | null | 当前 transport | 当前 transport |
| doConnect 已执行 | 当前 transport | 当前 transport | 当前 transport |
| transport 从 A 变为 B | A（旧） | B（新） | A（旧） |

在“首次 effect、containerReady=false”的场景下，`lastTransportRef=null`，`disconnect()` 会关闭 `transportRef.current`，即当前传入的 transport，这正是问题所在。

---

## 6. 修复建议

### 6.1 方案 A：else 分支仅在“已有连接”时 disconnect（推荐）

只在确实建立过连接时才在 else 分支中 disconnect，避免关闭尚未使用的 transport：

```ts
useEffect(() => {
  const hasTransport = !!transport;
  const hasContainer = !!containerRef.current;
  const canConnect = hasTransport && containerReady && hasContainer;
  if (canConnect) {
    doConnect();
  } else {
    // 仅在有已建立连接时 disconnect，避免关闭尚未使用的 transport
    if (rfbRef.current || lastTransportRef.current) {
      disconnect();
    }
  }
  return () => {
    if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
  };
}, [transport, containerReady, doConnect, disconnect]);
```

### 6.2 方案 B：用 ref 同步 containerReady，避免首次 effect 误判

在 VncCanvas 中用 ref 同步 DOM 挂载状态，让 effect 依赖更准确：

```ts
// VncCanvas
const containerReadyRef = useRef(false);
const setContainerRef = useCallback((el: HTMLDivElement | null) => {
  containerRef.current = el;
  containerReadyRef.current = !!el;
  setContainerReady(!!el);
}, []);
// 传入 useVnc 的 containerReady 可考虑用 ref 或延迟一帧
```

需要配合 useVnc 的 effect 逻辑调整，避免依赖“首次 render 时 containerReady 仍为 false”的时序。

### 6.3 方案 C：开发环境禁用 StrictMode（不推荐）

可临时验证 StrictMode 影响，但不应作为长期方案：

```ts
// main.tsx
<React.StrictMode>
  ↓
<App />  // 或条件性包裹
```

### 6.4 方案 D：mount effect 的 disconnect 使用“当前 transport”的副本

mount effect 的 cleanup 中，disconnect 会关闭 `lastTransportRef ?? transportRef`。在 StrictMode unmount 时，这是预期行为。问题主要来自连接 effect 的 else 分支，方案 A 即可缓解。

---

## 7. 总结

| 怀疑点 | 结论 |
|--------|------|
| 1. effect cleanup 在 doConnect 完成前运行 | 连接 effect 的 cleanup 只清定时器，不直接关 transport；但 mount effect 的 cleanup 会调用 disconnect，在 StrictMode 下会提前关闭 |
| 2. 依赖导致 effect 重复运行 | 是。`containerReady` 从 false→true 会触发两次 effect，第一次在 else 分支调用 disconnect |
| 3. disconnect 关闭新 transport | 在“从未 doConnect”时，disconnect 关闭的是当前 transportRef，即当前 props 的 transport，会误关尚未使用的 transport |
| 4. StrictMode 双 mount | 是。unmount 时 mount effect cleanup 调用 disconnect，remount 时 transport 已关闭 |

**根本原因**：连接 effect 的 else 分支在 `canConnect=false` 时无条件调用 `disconnect()`，而首次 effect 运行时 `containerReady` 仍为 `false`，导致在 RFB 使用前就关闭了 transport。

**推荐修复**：采用方案 A，在 else 分支中仅在 `rfbRef.current || lastTransportRef.current` 时调用 `disconnect()`。
