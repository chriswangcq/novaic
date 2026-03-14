# VNC 连接问题分析 — 第三轮：根因与修复方案

## 1. 根因归纳

综合前三轮分析，根因可归纳为三点：

### 1.1 createVncTransport 被多次触发

- **现象**：同一 vncTarget 下，createVncTransport 在 ~150ms 内被调用 6–7 次
- **可能原因**：
  - React Strict Mode 双挂载
  - 父组件条件渲染导致 AgentDesktopView 多次 mount/unmount
  - vncTargetKey 在 `undefined` / `null` 等边界情况下产生多余变化
- **结果**：每次调用都新建 VncBridgeTransport 和 stream，产生大量冗余连接

### 1.2 每次 createVncTransport 返回新实例

- `createVncTransport` 内部 `new VncBridgeTransport(resourceId, pcClientId)`，无复用
- 即使 vncTarget 语义相同，也会得到不同实例
- useVnc 的 `transport` 依赖变化，effect 重新执行，触发 doConnect

### 1.3 doConnect 的「关旧开新」策略过于激进

- 只要 `prevTransport !== t` 就关闭 prevTransport
- 在新 transport 不断到来的情况下，会反复关闭已建立或正在建立的连接
- 导致 RFB 在握手完成前后被断开，出现 "Disconnection timed out"

## 2. 修复方案

### 方案 A：Transport 按 key 缓存复用（推荐）

**思路**：同一 vncTargetKey 只创建一次 transport，后续复用。

```ts
// 模块级缓存：vncTargetKey -> VncBridgeTransport
const transportCache = new Map<string, VncBridgeTransport>();

export async function createVncTransport(target: VncTarget): Promise<VncTransport> {
  const key = `${target.resourceId}|${target.pcClientId ?? ''}`;
  const cached = transportCache.get(key);
  if (cached && cached.readyState === cached.OPEN) {
    return cached;  // 复用
  }
  const transport = new VncBridgeTransport(target.resourceId, target.pcClientId);
  await transport.connect();
  transportCache.set(key, transport);
  // 监听 close，从缓存移除
  const origClose = transport.close.bind(transport);
  transport.close = () => {
    transportCache.delete(key);
    origClose();
  };
  return transport;
}
```

**优点**：从源头避免重复创建，transport 引用稳定，useVnc 不会频繁关旧开新。  
**注意**：需处理 agent 切换、pcClientId 变化时的缓存失效。

---

### 方案 B：AgentDesktopView 内防抖 + 请求取消

**思路**：对 createVncTransport 做防抖，并取消过期的请求。

```ts
// AgentDesktopView
const createAbortRef = useRef<AbortController | null>(null);

useEffect(() => {
  if (!vncTargetKey || !vncTarget) {
    setTransport(null);
    return;
  }
  createAbortRef.current?.abort();
  createAbortRef.current = new AbortController();
  const signal = createAbortRef.current.signal;

  const timer = setTimeout(() => {
    createVncTransport(vncTargetRef.current!)
      .then((t) => {
        if (!signal.aborted) setTransport(t);
      })
      .catch(...);
  }, 100);  // 防抖 100ms

  return () => {
    clearTimeout(timer);
    createAbortRef.current?.abort();
  };
}, [vncTargetKey]);
```

**优点**：实现简单，能减少短时间内的重复调用。  
**缺点**：无法解决 Strict Mode 双挂载带来的两次调用。

---

### 方案 C：useVnc 中「同 key 不关旧」

**思路**：在 doConnect 中，若新旧 transport 对应同一 vncTargetKey，则不关闭旧 transport。

```ts
// 需要 VncBridgeTransport 暴露 resourceId 或 key
if (prevTransport && prevTransport !== t) {
  const prevKey = (prevTransport as VncBridgeTransport).getKey?.();
  const currKey = (t as VncBridgeTransport).getKey?.();
  if (prevKey !== currKey) {
    (prevTransport as VncBridgeTransport).close();
  }
  // 同 key 时保留 prevTransport，不创建新 RFB？逻辑复杂...
}
```

**缺点**：需要改 transport 接口，且「同 key 时是否替换 RFB」逻辑复杂，不推荐。

---

### 方案 D：禁用 Strict Mode 双挂载（仅作验证）

**思路**：在开发环境临时去掉 Strict Mode，验证是否由双挂载引起。

```tsx
// main.tsx
ReactDOM.createRoot(rootEl).render(
  // <React.StrictMode>
  <App />
  // </React.StrictMode>
);
```

**用途**：仅用于排查，不作为正式修复。

## 3. 推荐实施顺序

1. **方案 A（Transport 缓存）**：从源头减少 createVncTransport 调用和 transport 实例数量
2. **方案 B（防抖 + 取消）**：作为补充，进一步平滑短时间内的重复请求
3. **可选**：在 vncBridge 中为 VncBridgeTransport 增加 `getKey()`，便于调试和后续扩展

## 4. 验证要点

修复后需确认：

- [ ] 同一 agent 下，createVncTransport 仅调用 1 次（或 2 次，若 Strict Mode 双挂载）
- [ ] RFB connect 成功后不再被意外关闭
- [ ] 后端日志中 send_count > 0，且无大量 send_count=0 的 stream
- [ ] 切换 agent 时，旧 transport 正确关闭，新 transport 正常建立
