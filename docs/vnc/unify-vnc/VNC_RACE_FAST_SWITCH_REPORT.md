# VNC 前端竞态与快速切换研究报告

> 对照 `docs/unify-vnc/10-phase4-vnc-10-agent-review-summary.md` M1，研究 AgentDesktopView、DeviceDesktopView、useVnc、vncStream 在快速切换场景下的竞态与边界情况。

---

## 一、AgentDesktopView：vncTarget 快速切换与 requestIdRef

### 1.1 当前实现

```31:46:novaic-app/src/components/Visual/AgentDesktopView.tsx
  // M1: requestId 避免 vncTarget 快速切换时竞态
  const requestIdRef = useRef(0);
  useEffect(() => {
    if (!vncTarget) {
      setTransport(null);
      setTransportError(null);
      return;
    }
    const reqId = ++requestIdRef.current;
    setTransportError(null);
    createVncTransport(vncTarget)
      .then((t) => {
        if (reqId === requestIdRef.current) setTransport(t);
      })
      .catch((e) => {
        if (reqId === requestIdRef.current) setTransportError(e instanceof Error ? e.message : 'Failed to create transport');
      });
  }, [vncTarget]);
```

### 1.2 竞态场景分析

| 场景 | 时序 | requestId 能否正确拒绝？ |
|------|------|--------------------------|
| A→B→A 快速切换 | A: reqId=1 发起；B: reqId=2 发起；A: reqId=3 发起；B 先 resolve | ✅ 能。B resolve 时 `reqId(2) === requestIdRef.current(3)` 为 false，不应用 |
| A→B 切换，B 后发先至 | A: reqId=1；B: reqId=2；B 先 resolve | ✅ 能。B 应用；A resolve 时 1≠2，拒绝 |
| A→null | A: reqId=1 发起；vncTarget=null 提前 return | ❌ **边界问题**：return 前未 `++requestIdRef`，A resolve 时 `reqId(1) === requestIdRef.current(1)` 仍成立，会错误 `setTransport(t)` |
| A→null→A | null 时未递增，A 的旧 promise 可能覆盖 | ❌ 同上，旧结果可能覆盖 |

### 1.3 边界情况

1. **vncTarget 为 null 时未递增 requestId**：effect 提前 return，`requestIdRef` 未更新，上一个 `createVncTransport` 的 resolve 仍会执行 `setTransport`，导致已清空时再次写入。
2. **createVncTransport 不可取消**：`VncBridgeTransport.connect()` 无 AbortSignal，即使 effect cleanup 也无法中止正在进行的连接，只能依赖 requestId 丢弃结果。

### 1.4 修复建议

```ts
useEffect(() => {
  const reqId = ++requestIdRef.current;  // 先递增，再 early return
  if (!vncTarget) {
    setTransport(null);
    setTransportError(null);
    return;
  }
  setTransportError(null);
  createVncTransport(vncTarget)
    .then((t) => {
      if (reqId === requestIdRef.current) setTransport(t);
    })
    .catch((e) => {
      if (reqId === requestIdRef.current) setTransportError(...);
    });
}, [vncTarget]);
```

---

## 二、DeviceDesktopView：startDevice 2s 延迟与 AbortController

### 2.1 当前实现

```115:146:novaic-app/src/components/Visual/DeviceDesktopView.tsx
  // M5: 可取消的 startDevice delay
  const startAbortRef = useRef<AbortController | null>(null);
  const startDevice = useCallback(async () => {
    if (!deviceId) return;
    startAbortRef.current?.abort();
    startAbortRef.current = new AbortController();
    const signal = startAbortRef.current.signal;
    setDeviceStatus('starting');
    try {
      await api.devices.start(deviceId, pcClientId);
      await new Promise<void>((resolve, reject) => {
        const t = setTimeout(resolve, VNC_START_WAIT_MS);
        signal.addEventListener('abort', () => {
          clearTimeout(t);
          reject(new DOMException('Aborted', 'AbortError'));
        });
      });
      if (signal.aborted) return;
      setDeviceStatus('running');
    } catch (e) {
      if ((e as Error)?.name === 'AbortError') return;
      // ...
    }
  }, [deviceId, pcClientId]);
```

createVncTransport 的 effect 与 startDevice 独立：

```92:112:novaic-app/src/components/Visual/DeviceDesktopView.tsx
  const requestIdRef = useRef(0);
  useEffect(() => {
    if (!vncTarget) { ... return; }
    if (isMaindesk && deviceStatus !== 'running') { ... return; }
    const reqId = ++requestIdRef.current;
    createVncTransport(vncTarget)
      .then((t) => { if (reqId === requestIdRef.current) setTransport(t); })
      .catch(...);
  }, [vncTarget, isMaindesk, deviceStatus]);
```

### 2.2 竞态场景分析

| 场景 | 行为 | 问题 |
|------|------|------|
| 2s 内切换设备 | 用户点击 Start，2s 内切到另一设备 | startDevice 的 AbortController 会 reject，`setDeviceStatus('running')` 不会执行 ✅ |
| abort 后 transport 是否仍在创建 | deviceStatus 从 starting→stopped（或未变），effect 依赖 `deviceStatus !== 'running'` 会 early return | 不会发起新的 createVncTransport ✅ |
| 竞态：Start A，2s 内切到 B，B 的 maindesk 也点 Start | A 的 startDevice abort；B 的 startDevice 开始 | 各自 AbortController 独立，无交叉 ✅ |
| Start A，2s 内 unmount | cleanup 中 `startAbortRef.current?.abort()` | 2s 后不会 setState ✅ |

### 2.3 潜在问题

1. **api.devices.start 不可取消**：`await api.devices.start(...)` 无 AbortSignal，abort 只影响后面的 2s delay。若 start 本身很慢，abort 后仍会等到 start 完成才进入 delay，但 delay 会被 abort 取消。
2. **deviceStatus 与 createVncTransport 的时序**：`setDeviceStatus('running')` 在 2s 后执行，effect 依赖 `deviceStatus`，会触发 createVncTransport。若 2s 内 abort，deviceStatus 不会变为 running，effect 不会创建 transport，逻辑正确。

### 2.4 结论

AbortController 能正确取消 2s 延迟；abort 后不会创建 transport；竞态处理合理。建议：若 `api.devices.start` 支持 AbortSignal，可传入以支持更早取消。

---

## 三、useVnc：transport 切换与 effect cleanup

### 3.1 当前实现

```161:169:novaic-app/src/hooks/useVnc.ts
  useEffect(() => {
    if (transport && containerRef.current) {
      doConnect();
    } else {
      disconnect();
    }
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, [transport, doConnect, disconnect]);
```

```55:73:novaic-app/src/hooks/useVnc.ts
  const disconnect = useCallback(() => {
    if (retryTimerRef.current) { clearTimeout(retryTimerRef.current); ... }
    if (rfbRef.current) { rfbRef.current.disconnect(); ... }
    const t = lastTransportRef.current ?? transportRef.current;
    if (t && typeof t !== 'string' && 'close' in t) {
      (t as VncBridgeTransport).close();
    }
    lastTransportRef.current = null;
    setStatus('disconnected');
    setErrorMsg('');
  }, []);
```

```144:149:novaic-app/src/hooks/useVnc.ts
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [disconnect]);
```

### 3.2 竞态场景分析

| 问题 | 分析 |
|------|------|
| transport A→B 时，effect cleanup 会 disconnect 吗？ | 会。新 effect 运行前，旧 effect 的 cleanup 先执行，会 `clearTimeout(retryTimerRef)`，但**不会**调用 `disconnect()`。cleanup 只清 retry timer，没有显式 disconnect。 |
| 谁负责 disconnect？ | 新 effect 体：`if (transport && containerRef.current) { doConnect(); } else { disconnect(); }`。transport 从 A 切到 B 时，transport 非 null，会执行 `doConnect()`，不会走 `disconnect()`。 |
| doConnect 内的旧 transport 关闭 | `doConnect` 开头会关闭 `lastTransportRef.current`（旧 transport），然后 `lastTransportRef.current = t`。因此旧 VncBridgeTransport 会被 close ✅ |
| doConnect 正在 await 时，新 effect 的 cleanup 何时运行？ | 当 transport 从 A 变为 B 时：1) 旧 effect cleanup 运行（只清 retry timer）；2) 新 effect 运行，调用 `doConnect()`。`doConnect` 是 async，内部无 await 到外部 promise，是同步到 `new RFB(...)` 的。关键：`doConnect` 内 `transportRef.current` 在每次 render 时更新为当前 transport，所以进入 doConnect 时已是 B。 |
| lastTransportRef 是否可能覆盖错误？ | `lastTransportRef.current = t` 在 doConnect 开头、关闭旧 transport 之后设置。若 transport 从 A→B→null 快速切换：1) A: doConnect 开始，lastTransportRef=A；2) B: doConnect 开始，关闭 A，lastTransportRef=B；3) null: 走 `disconnect()`，`t = lastTransportRef.current ?? transportRef.current`，会 close B。正确 ✅ |

### 3.3 边界情况

1. **cleanup 不调用 disconnect**：transport 从 A 到 B 时，旧 effect 的 cleanup 只清 retry timer，不断开 RFB。新 effect 的 `doConnect` 会先断开旧 RFB 并 close 旧 transport，再创建新 RFB，逻辑正确。
2. **doConnect 执行中 transport 变为 null**：`doConnect` 开始时 `transportRef.current` 为 A，执行过程中 transport 变为 null。`transportRef.current` 会同步更新为 null，但 `doConnect` 已用 `const t = transportRef.current` 取到 A，会继续用 A 建连。此时新 effect 会执行 `disconnect()`（因为 transport 为 null），disconnect 会 clear retry、断开 rfb、close lastTransportRef。`doConnect` 完成后会 `rfbRef.current = rfb`，但 disconnect 可能已把 rfbRef 置 null。若 disconnect 先执行，doConnect 的 `rfbRef.current = rfb` 会覆盖，可能留下未 disconnect 的 RFB。需确认执行顺序。
3. **React 18 Strict Mode 双挂载**：mount→unmount→mount 时，第一次 unmount 的 cleanup 会 disconnect，第二次 mount 会重新 doConnect，一般可接受。

### 3.4 修复建议

1. **effect cleanup 中显式 disconnect**：transport 变化时，cleanup 也断开当前连接，避免依赖“下次 doConnect 会清理”的隐式逻辑：

```ts
useEffect(() => {
  if (transport && containerRef.current) {
    doConnect();
  } else {
    disconnect();
  }
  return () => {
    if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    disconnect();  // 显式断开，确保 transport 切换时旧连接被清理
  };
}, [transport, doConnect, disconnect]);
```

2. **doConnect 入口校验**：在 `doConnect` 开头再次检查 `transportRef.current === t`，若 transport 已变则直接返回，避免用过期 transport 建连。

---

## 四、vncStream：同一 agentId 下快速切换 pcClientId

### 4.1 当前实现

```316:328:novaic-app/src/services/vncStream.ts
export function subscribeToVNCStream(agentId: string, subscriber: StreamSubscriber, deviceId?: string): () => void {
  // ...
  if (state.status === 'disconnected' || state.status === 'error') {
    connectStream(agentId, deviceId);
  }
  return () => {
    state.subscribers.delete(subscriber);
    if (state.subscribers.size === 0) {
      disconnectStream(agentId);
    }
  };
}
```

```116:140:novaic-app/src/services/vncStream.ts
async function connectStream(agentId: string, deviceId?: string) {
  // ...
  if (state.status === 'connected' || state.status === 'connecting') {
    return;
  }
  state.status = 'connecting';
  try {
    if (!state.transportOrUrl) {
      state.transportOrUrl = await vmService.getVncTransport(agentId, deviceId).catch(...);
    }
    // ... 创建 RFB 等
  }
}
```

StreamState 未保存 deviceId：

```24:35:novaic-app/src/services/vncStream.ts
interface StreamState {
  rfb: RFB | null;
  // ...
  transportOrUrl: string | VncBridgeTransport | null;
  retryCount: number;
  // 无 deviceId 字段
}
```

重连时使用闭包中的 deviceId：

```218:223:novaic-app/src/services/vncStream.ts
          state.retryTimer = setTimeout(() => {
            if (state && state.subscribers.size > 0) {
              connectStream(agentId, deviceId);  // deviceId 来自 connectStream 调用时的闭包
            }
          }, 2000);
```

### 4.2 竞态场景分析

| 场景 | 时序 | 问题 |
|------|------|------|
| 同一 agentId，pcClientId 从 P1 快速切到 P2 | subscribe(P1)→connectStream(agentId,P1) 进行中→unsubscribe→subscribe(P2)→connectStream(agentId,P2) | unsubscribe 会 disconnectStream；若 P1 的 connectStream 仍在 await getVncTransport，disconnectStream 会清空 state，但 **connectStream(P1) 的后续逻辑仍会继续**，最终用 P1 的 transport 覆盖 state |
| connectStream 已在进行，deviceId 变化 | connectStream(agentId, P1) 在 await；用户切到 P2，subscribe(P2) 触发 connectStream(agentId, P2) | `state.status === 'connecting'` 会阻止 P2 的 connectStream 进入。P1 完成后 state 是 P1 的 transport，但用户期望 P2 |
| 重连用旧 deviceId | 连接 P1 后断开，retry 用 `connectStream(agentId, deviceId)`，deviceId 来自闭包 | 若已从 P1 切到 P2，闭包仍是 P1，重连会连到错误 PC |

### 4.3 根因

1. **connectStream 不可取消**：无 requestId/AbortController，进行中的 connectStream 无法被“作废”。
2. **StreamState 不存 deviceId**：无法在重连或状态恢复时使用“当前期望”的 deviceId。
3. **disconnect 与 connectStream 的竞态**：disconnectStream 清空 state，但进行中的 connectStream 仍会用旧 deviceId 的结果写回 state。

### 4.4 修复建议

1. **在 StreamState 中保存 deviceId**：

```ts
interface StreamState {
  // ...
  currentDeviceId?: string;  // 当前期望的 deviceId/pcClientId
}
```

2. **connectStream 使用 requestId 校验**：

```ts
let connectRequestId = 0;
async function connectStream(agentId: string, deviceId?: string) {
  const reqId = ++connectRequestId;
  // ...
  const transport = await vmService.getVncTransport(agentId, deviceId);
  if (reqId !== connectRequestId) return;  // 已过时，丢弃
  // ...
}
```

3. **重连时使用 state 中的 currentDeviceId**：

```ts
// 在 subscribe 时更新 state.currentDeviceId = deviceId
// 重连时: connectStream(agentId, state.currentDeviceId)
```

4. **subscribe 时若 deviceId 变化，先 disconnect 再 connect**：若 `state.currentDeviceId !== deviceId` 且 `state.status !== 'disconnected'`，先 `disconnectStream(agentId)`，再 `connectStream(agentId, deviceId)`，并更新 `state.currentDeviceId`。

---

## 五、汇总表

| 模块 | 竞态场景 | requestId/AbortController 覆盖 | 修复建议 |
|------|----------|--------------------------------|----------|
| AgentDesktopView | A→null 时旧 promise 仍应用 | vncTarget=null 时未递增 requestId | 先 `++requestIdRef` 再 early return |
| DeviceDesktopView | 2s 内切换/abort | AbortController 正确取消 delay | 无需大改；可考虑 api.devices.start 支持 AbortSignal |
| useVnc | transport 切换时 cleanup 不断开 | cleanup 只清 retry，不断开连接 | cleanup 中显式 disconnect；doConnect 入口校验 transport |
| vncStream | 快速切换 pcClientId 时旧 connectStream 覆盖 | 无 requestId；StreamState 无 deviceId | 增加 requestId；StreamState 存 deviceId；重连用 state 中的 deviceId |

---

## 六、优先级建议

| 优先级 | 项 | 说明 |
|--------|-----|------|
| P0 | AgentDesktopView vncTarget=null | 会导致已清空后再次 setTransport，必须修复 |
| P0 | DeviceDesktopView 同上 | 与 AgentDesktopView 相同逻辑，需同步修复 |
| P1 | vncStream requestId + deviceId | 多 PC 快速切换时连错设备 |
| P2 | useVnc cleanup 显式 disconnect | 提升可读性与健壮性 |
