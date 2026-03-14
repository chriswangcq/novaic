# VncBridgeTransport 与 noVNC RFB 时序分析

## 问题背景

`send_count=0` 表示 RFB 从未成功 send。本文分析 VncBridgeTransport 与 noVNC RFB 之间的时序问题，找出根因并给出修复建议。

---

## 1. 核心流程梳理

### 1.1 VncBridgeTransport.connect() 流程

```ts
// vncBridge.ts
async connect(): Promise<void> {
  this.readyState = this.CONNECTING;
  try {
    this.bridgeId = await invoke('vnc_stream_connect', {...});  // ①
    this.readyState = this.OPEN;                               // ②
    await this.setupListeners();                               // ③
    this.onopen?.();                                          // ④
  } catch (e) { ... }
}
```

**关键点**：
- ① `vnc_stream_connect` 返回后，后端已 spawn 任务，`route_vnc_to_channel` 开始运行
- ② `readyState = OPEN` 在 setupListeners **之前** 设置
- ③ `setupListeners` 会 `listen` 到 `vnc_stream:{id}:data` 和 `vnc_stream:{id}:close`
- ④ `onopen` 在 setupListeners **之后** 调用

### 1.2 noVNC RFB attach 流程

```js
// @novnc/novnc lib/rfb.js _connect()
if (this._url) {
  this._sock.open(this._url, ...);
} else {
  this._sock.attach(this._rawChannel);           // ① 覆盖 transport.onopen
  if (this._sock.readyState === 'closed') { ... }
  if (this._sock.readyState === 'open') {       // ② 若已 OPEN，立即 _socketOpen
    this._socketOpen();
  }
}
```

```js
// @novnc/novnc lib/websock.js attach()
this._websocket = rawChannel;
this._websocket.onmessage = this._recvMessage.bind(this);
this._websocket.onopen = function () {          // 覆盖 raw channel 的 onopen
  _this._eventHandlers.open();                  // 触发 RFB 的 _socketOpen
};
```

**关键点**：
- RFB 在 attach 时**覆盖** transport 的 `onopen`
- 若 transport 已 `readyState === OPEN`，RFB 会**立即**调用 `_socketOpen()`，不等待 onopen
- `_socketOpen()` 中会发送 RFB 版本等握手数据

### 1.3 useVnc effect 与 disconnect

```ts
// useVnc.ts
useEffect(() => {
  const hasTransport = !!transport;
  const hasContainer = !!containerRef.current;
  const canConnect = hasTransport && containerReady && hasContainer;
  if (canConnect) {
    doConnect();
  } else {
    disconnect();   // ⚠️ canConnect=false 时总是 disconnect
  }
  ...
}, [transport, containerReady, doConnect, disconnect]);
```

### 1.4 VncCanvas 与 containerReady

```tsx
// VncCanvas.tsx
const [containerReady, setContainerReady] = useState(false);  // 初始 false
const setContainerRef = useCallback((el) => {
  containerRef.current = el;
  setContainerReady(!!el);   // ref callback 中才设为 true
}, []);
// ...
<div ref={setContainerRef} />
```

---

## 2. 时序图

### 2.1 理想时序（无竞态）

```
createVncTransport     VncBridgeTransport     useVnc effect        noVNC RFB
       |                       |                     |                  |
       |--connect()------------>|                     |                  |
       |                       |--invoke()----------->|                  |
       |                       |<--bridgeId-----------|                  |
       |                       |--readyState=OPEN     |                  |
       |                       |--setupListeners()   |                  |
       |                       |   listen(data)      |                  |
       |                       |   listen(close)      |                  |
       |                       |--onopen()            |                  |
       |<--return transport-----|                     |                  |
       |                       |                     |                  |
       |--setTransport(t)------>|                     |                  |
       |                       |                     |--effect runs     |
       |                       |                     |  canConnect?     |
       |                       |                     |--doConnect()----->|
       |                       |                     |                  |--new RFB(transport)
       |                       |                     |                  |--attach(transport)
       |                       |                     |                  |  readyState=OPEN
       |                       |                     |                  |--_socketOpen()
       |                       |                     |                  |--send(version)
       |                       |<--vnc_stream_send---|                  |
       |                       |                     |                  |
```

### 2.2 实际竞态：containerReady 滞后导致误关 transport

```
React render 1 (transport 刚 set)
  VncCanvas: containerReady=false (useState 初始值)
  ref callback: 尚未执行（或已执行但 setState 未 flush）

useVnc effect 运行:
  hasTransport=true, containerReady=false, hasContainer=true
  canConnect = true && false && true = false
  disconnect() 被调用  <-- ⚠️ 关闭了刚创建的 transport！

React render 2 (setContainerReady(true) 触发)
  containerReady=true

useVnc effect 再次运行:
  canConnect=true
  doConnect() 执行
  bridge.readyState !== OPEN  <-- transport 已被关闭！
  跳过连接，setStatus('failed')
```

---

## 3. 根因分析

### 3.1 问题 1：containerReady 滞后导致误关 transport（最可能）

| 项目 | 说明 |
|------|------|
| **现象** | `send_count=0`，RFB 从未 send |
| **根因** | transport 首次 set 时，`containerReady` 仍为 `false`（ref callback 的 setState 尚未生效），effect 执行 `disconnect()`，关闭了刚建好的 transport |
| **后果** | 下一轮 effect 时 `doConnect` 检测到 `readyState !== OPEN`，直接跳过 |

### 3.2 问题 2：onopen 与 attach 的时序（当前无影响）

| 项目 | 说明 |
|------|------|
| **分析** | VncBridgeTransport 的 `onopen` 在 connect 内调用时，RFB 尚未 attach，此时 `onopen` 为 null，调用无效果 |
| **结论** | RFB 在 attach 后通过 `readyState === 'open'` 分支**立即**调用 `_socketOpen()`，不依赖 onopen，因此此处无实际影响 |

### 3.3 问题 3：setupListeners 与 data 丢失（当前无影响）

| 项目 | 说明 |
|------|------|
| **分析** | `await setupListeners()` 在 `onopen` 之前完成，listen 已注册 |
| **数据流** | 后端 emit data 发生在 `route_vnc_to_channel` 收到 QEMU 数据之后，此时前端 listen 已就绪 |
| **结论** | 不会因 listen 未注册而丢数据 |

### 3.4 问题 4：Tauri listen 与 emit 的时序

| 项目 | 说明 |
|------|------|
| **分析** | Tauri 的 `listen` 是订阅制，emit 之后才 listen 会错过该次事件 |
| **结论** | 当前顺序为 connect 返回 → setupListeners → listen 注册，早于后端首次 emit，无问题 |

---

## 4. 修复建议

### 4.1 修复 1：containerReady 滞后时不要 disconnect（推荐）

**思路**：当 `hasTransport && !containerReady` 时，视为「等待容器就绪」，不调用 `disconnect()`，避免误关新建的 transport。

```ts
// useVnc.ts - 修改 effect
useEffect(() => {
  const hasTransport = !!transport;
  const hasContainer = !!containerRef.current;
  const canConnect = hasTransport && containerReady && hasContainer;
  if (canConnect) {
    doConnect();
  } else {
    // 仅当确定不会连接时才 disconnect
    // hasTransport && !containerReady 时可能是 ref 尚未回调，不要关 transport
    if (!hasTransport || (hasTransport && containerReady && !hasContainer)) {
      disconnect();
    }
  }
  ...
}, [transport, containerReady, doConnect, disconnect]);
```

或更清晰：

```ts
if (canConnect) {
  doConnect();
} else if (!hasTransport) {
  disconnect();  // 无 transport，清理旧连接
} else if (containerReady && !hasContainer) {
  disconnect();  // 有 transport 且 containerReady 但无容器，异常态
}
// hasTransport && !containerReady：等待 ref，不 disconnect
```

### 4.2 修复 2：用 flushSync 或 layoutEffect 提前 containerReady（备选）

通过 `useLayoutEffect` 在 paint 前同步设置 containerReady，减少 effect 与 ref 的时序差，但无法完全消除竞态，不如修复 1 稳妥。

### 4.3 修复 3：延迟 disconnect 到「真正不需要连接」时

将「可以连接」与「需要断开」分开处理：只有在 transport 从有变无、或容器被卸载时，才执行 disconnect，而不是在 `canConnect=false` 时一律 disconnect。

---

## 5. 验证建议

1. **加日志**：在 `disconnect()` 和 `doConnect()` 中打印 `transport?.readyState`、`containerReady`、`canConnect`，确认是否出现「先 disconnect 再 doConnect 且 transport 已关闭」的序列。
2. **临时修改**：按修复 1 调整 effect，观察 `send_count` 是否大于 0、RFB 是否能正常握手。
3. **回归**：验证 transport 为 null 时（如切换设备、关闭面板）仍能正确断开并清理。

---

## 6. 小结

| 可能原因 | 是否根因 | 说明 |
|----------|----------|------|
| onopen 在 setupListeners 之前 | ❌ | onopen 在 setupListeners 之后，且 RFB 不依赖此次 onopen |
| RFB 在 transport 未 OPEN 时 attach | ❌ | 正常流程下 transport 在 create 时已 OPEN |
| setupListeners 是 async，onopen 先执行 | ❌ | 代码中 `await setupListeners()` 保证 listen 先完成 |
| 前端 disconnect 过早关闭 transport | ✅ | containerReady 滞后导致 effect 误调 disconnect，关闭新建 transport |

**结论**：最可能的根因是 useVnc 的 effect 在 `containerReady=false` 时调用 `disconnect()`，提前关闭了 transport。建议采用修复 1，在「有 transport 但 containerReady 为 false」时不执行 disconnect。
