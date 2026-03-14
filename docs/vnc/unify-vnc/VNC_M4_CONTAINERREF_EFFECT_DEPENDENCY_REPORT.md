# M4：containerRef 时序与 effect 依赖 — VNC 稳定性研究报告

> 对照 `docs/unify-vnc/10-phase4-vnc-10-agent-review-summary.md` M4，研究组件挂载与 effect 依赖问题。

---

## 一、问题概览

| 问题 | 严重度 | 结论 |
|------|--------|------|
| useVnc effect 不依赖 containerRef | 高 | 若 containerRef.current 首次为 null，effect 不会重跑，**永不连接** |
| VncCanvas containerRef 传递时机 | 中 | 同步渲染下通常就绪；Suspense/lazy 下可能延迟 |
| transport 为 null 时 AgentDesktopView 渲染 | 中 | 会 render VncCanvas，containerRef 来自当前 mount，非上一轮 |
| createVncTransport 无超时 | 高 | 卡住时用户一直看到 "Preparing transport…"，无超时 |

---

## 二、useVnc effect 依赖分析

### 2.1 当前实现

```159:169:novaic-app/src/hooks/useVnc.ts
  useEffect(() => {
    if (transport && containerRef.current) {
      doConnect();
    } else {
      // C1: transport 为 null 时也调用 disconnect，确保旧 VncBridgeTransport 被关闭
      disconnect();
    }
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, [transport, doConnect, disconnect]);
```

**依赖数组**：`[transport, doConnect, disconnect]`，**不包含** `containerRef`。

### 2.2 时序问题

| 阶段 | containerRef.current | transport | effect 行为 |
|------|----------------------|-----------|-------------|
| 首次 render | null（ref 在 commit 后设置） | 非 null | `!containerRef.current` → 不 doConnect，走 disconnect |
| DOM 挂载后 | 非 null | 非 null | **effect 不重跑**（依赖未变）→ **永不连接** |

**根因**：`containerRef` 是 `RefObject`，其 `.current` 变化不会触发 React 重渲染，也不会触发依赖该 ref 的 effect 重新执行。

### 2.3 何时 containerRef.current 会为 null？

1. **首次 render**：`useRef(null)` 初始为 null，`ref={containerRef}` 在 commit 阶段才赋值。若 effect 与 ref 回调执行顺序存在边界情况，可能先执行 effect。
2. **条件渲染 / 延迟挂载**：VncCanvas 的 div 在 `display:none`、`visibility:hidden` 或父级未挂载时，ref 可能延迟设置。
3. **React 18 StrictMode**：双 mount 下，首次 unmount 时 ref 会清空，可能产生竞态。
4. **Suspense / lazy**：若 VncCanvas 或其父级被 `React.lazy` 包裹，首次 paint 前 containerRef 可能尚未就绪。

---

## 三、VncCanvas 与 containerRef 传递

### 3.1 实现

```27:33:novaic-app/src/components/Visual/VncCanvas.tsx
export function VncCanvas({ transport, options, className, renderOverlay }: VncCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { status, errorMsg, connect } = useVnc(transport, containerRef, options ?? {});

  return (
    <div className={className} style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={containerRef} className="absolute inset-0" />
```

- `containerRef` 在 VncCanvas 内部创建，直接传给 `useVnc`。
- `ref={containerRef}` 的 div 与 VncCanvas 同树、同步渲染，无 `lazy`/`Suspense` 包裹。

### 3.2 项目中的使用路径

- **VisualPanel**：`{activeView === 'linux' && <AgentDesktopView agentId={...} />}` → 条件渲染，切换 tab 时 AgentDesktopView 会 unmount/mount。
- **AgentDesktopView**：通过 loading/error 等分支后，最终 render `<VncCanvas transport={transport} ... />`。
- **DeviceFloatingPanel**：直接 render `<DeviceDesktopView ... />`。

当前代码中未发现 `React.lazy` 或 `Suspense` 包裹 VncCanvas。若未来引入 lazy 加载，`containerRef.current` 可能在首帧为 null 的时间更长。

---

## 四、AgentDesktopView 渲染分支与 transport 为 null

### 4.1 渲染分支顺序

```53:96:novaic-app/src/components/Visual/AgentDesktopView.tsx
  if (!agentId) { return ...; }
  if (isLoading) { return ...; }      // "Loading agent device…"
  if (error) { return ...; }
  if (!vncTarget) { return ...; }
  if (transportError) { return ...; }
  return (
    ...
    <VncCanvas transport={transport} ... />
  );
```

### 4.2 transport 为 null 时的行为

| 场景 | 是否 render VncCanvas | containerRef 来源 |
|------|------------------------|-------------------|
| isLoading | 否 | - |
| vncTarget 存在，createVncTransport pending | 是 | 当前 VncCanvas mount 的 containerRef |
| createVncTransport 已 resolve | 是 | 同上 |

**结论**：当 `transport` 为 null 时，VncCanvas 仍会被 render（只要通过前面的条件）。此时 `containerRef` 来自**当前** VncCanvas 的 mount，不是「上一轮」的 ref。effect 会执行 `disconnect()`，不会调用 `doConnect()`。

### 4.3 loading 期间

`isLoading` 时直接 return，**不 render VncCanvas**。因此 loading 期间不存在 VncCanvas 的 containerRef 问题。

---

## 五、VncConnectionOverlay 与 createVncTransport 超时

### 5.1 transportReady 为 false 时的展示

```18:46:novaic-app/src/components/Visual/VncConnectionOverlay.tsx
export function VncConnectionOverlay({ status, errorMsg, connect, transportReady = true }: VncConnectionOverlayProps) {
  ...
  if (status === 'failed' || status === 'reconnecting') {
    ...
    {!transportReady && (
      <span className="text-xs text-nb-text-secondary mt-1">Preparing transport…</span>
    )}
  }
  if (status === 'disconnected') {
    ...
    {!transportReady && (
      <span className="text-xs text-nb-text-secondary mt-1">Waiting for transport…</span>
    )}
  }
```

当 `transportReady === false`（即 `transport === null`）时，显示 "Preparing transport…" 或 "Waiting for transport…"。

### 5.2 createVncTransport 无超时

```21:33:novaic-app/src/services/vncTransport.ts
export async function createVncTransport(target: VncTarget): Promise<VncTransport> {
  const { resourceId, pcClientId } = target;
  if (shouldUseVncBridge()) {
    const transport = new VncBridgeTransport(resourceId, pcClientId);
    await transport.connect();  // 无超时
    return transport;
  }
  const url = await invoke<string>('get_vnc_proxy_url', {...});  // 无超时
  return url;
}
```

- `VncBridgeTransport.connect()` 和 `invoke('get_vnc_proxy_url')` 均无超时控制。
- 网络慢或后端无响应时，Promise 会一直 pending。
- 用户会持续看到 "Preparing transport…" 或 "Waiting for transport…"，无法区分「进行中」与「已卡住」。

---

## 六、修复建议

### 6.1 containerRef 就绪后触发连接（P0）

**方案 A：ref callback 触发 state 更新**

```tsx
// useVnc.ts
const [containerReady, setContainerReady] = useState(false);
const containerCallbackRef = useCallback((el: HTMLDivElement | null) => {
  (containerRef as React.MutableRefObject<HTMLDivElement | null>).current = el;
  setContainerReady(!!el);
}, []);

useEffect(() => {
  if (transport && containerRef.current) {
    doConnect();
  } else {
    disconnect();
  }
  ...
}, [transport, containerReady, doConnect, disconnect]);  // 增加 containerReady
```

需要 `useVnc` 同时返回 `containerCallbackRef`，由 VncCanvas 使用 `ref={containerCallbackRef}` 替代 `ref={containerRef}`。

**方案 B：ResizeObserver / MutationObserver 监听挂载**

在 effect 内用 `ResizeObserver` 或 `MutationObserver` 监听 containerRef 对应 DOM 的挂载，挂载后调用 `doConnect()`。实现较复杂，一般不推荐。

**方案 C：轮询 + 重试（权宜之计）**

在 effect 中若 `transport && !containerRef.current`，启动短间隔轮询，直到 `containerRef.current` 非 null 再 `doConnect()`。不优雅，但可快速缓解问题。

**推荐**：方案 A，用 ref callback 驱动 `containerReady`，将 `containerReady` 加入 effect 依赖。

---

### 6.2 doConnect 依赖 containerRef（P1）

`doConnect` 的 `useCallback` 依赖为 `[scaleViewport, clipViewport, viewOnly]`，未包含 `containerRef`。由于 `doConnect` 内部读取 `containerRef.current`，闭包可能持有旧 ref。建议：

- 将 `containerRef` 加入 `doConnect` 的依赖，或
- 通过 `containerRef.current` 的「就绪」状态（如方案 A 的 `containerReady`）间接驱动，避免直接依赖 ref。

---

### 6.3 createVncTransport 超时（P0）

```ts
// vncTransport.ts
const TRANSPORT_TIMEOUT_MS = 30000;  // 与 WS_CONFIG.CONNECTION_TIMEOUT 对齐

export async function createVncTransport(target: VncTarget): Promise<VncTransport> {
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('VNC transport timeout')), TRANSPORT_TIMEOUT_MS)
  );
  const connectPromise = (async () => {
    // ... 原有逻辑
  })();
  return Promise.race([connectPromise, timeoutPromise]);
}
```

超时后应 `reject`，由 AgentDesktopView/DeviceDesktopView 的 `transportError` 展示错误，并允许用户重试。

---

### 6.4 VncConnectionOverlay 超时提示（P2）

当 `transportReady === false` 超过 N 秒时，可显示「建立连接较慢，请检查网络」等提示，并可选提供「取消」按钮。需在 AgentDesktopView/DeviceDesktopView 中增加计时逻辑。

---

## 七、总结

| 项目 | 现状 | 风险 |
|------|------|------|
| effect 依赖 | 不包含 containerRef | containerRef 延迟就绪时永不连接 |
| containerRef 传递 | VncCanvas 内部创建，同步传给 useVnc | 当前无 lazy/Suspense，风险较低 |
| transport 为 null | 会 render VncCanvas，effect 调用 disconnect | containerRef 来自当前 mount，无「上一轮」问题 |
| createVncTransport | 无超时 | 卡住时用户一直看到 "Preparing transport…" |

**优先修复**：  
1. 增加 containerRef 就绪监听（ref callback + containerReady），并加入 effect 依赖。  
2. 为 createVncTransport 增加超时（如 30s），超时后 reject 并展示可重试的错误。
