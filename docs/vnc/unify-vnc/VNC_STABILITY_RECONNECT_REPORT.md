# VNC 连接生命周期与重连策略 — 稳定性研究报告

> 对照 `docs/unify-vnc/02-expert-design.md` §3.2、`docs/unify-vnc/09-phase4-design-code-verification.md`，对 useVnc.ts、vncStream.ts 的深入分析。

---

## 一、发现的问题列表

### 问题 1：useVnc 依赖 `e.detail?.clean` 导致服务器端断开不重连（严重）

| 项目 | 内容 |
|------|------|
| **位置** | `novaic-app/src/hooks/useVnc.ts` 第 108–127 行 |
| **描述** | disconnect 事件中 `clean === true` 时直接 `setStatus('disconnected')` 且不重连；`clean === false` 时才重连。 |
| **根因** | noVNC 的 `detail.clean` 语义与预期不符。经 `@novnc/novnc/lib/rfb.js` 源码确认：<br>• `_rfbCleanDisconnect` 初始为 `true`（约第 151 行）<br>• 仅 `_fail()` 会将其设为 `false`（约第 1011 行）<br>• **服务器端断开**（网络中断、VM 停止等）走 `_socketClose` case `'connected'`，直接 `disconnecting → disconnected`，**不调用 `_fail()`**，因此 `clean` 仍为 `true` |
| **影响** | 服务器端断开时 `clean === true`，useVnc 误判为「用户主动断开」而不重连，导致 AgentDesktopView / DeviceDesktopView 在断网、VM 重启等场景下无法自动恢复。 |
| **设计偏差** | 02-expert-design §3.2 要求「连接断开后等待 2s 重试，最多 5 次，指数退避」，当前实现因 clean 误判导致部分断开场景不重连。 |

---

### 问题 2：vncStream 与 useVnc 重连策略不一致，main vs vm_user 表现不同

| 项目 | 内容 |
|------|------|
| **位置** | `vncStream.ts` 第 217–224、250–256 行；`useVnc.ts` 第 18–19、116–120 行 |
| **描述** | 双轨重连参数不一致：<br>• **vncStream**：固定 2s 延迟、最多 3 次；catch 中为 3s<br>• **useVnc**：2s 起、指数退避、最多 5 次 |
| **影响** | DeviceFloatingPanel main 使用 VNCViewShared（vncStream），vm_user 使用 DeviceDesktopView（useVnc）。main 重连更少、更慢，vm_user 重连更积极，同一设备在不同入口表现不一致。 |
| **设计偏差** | 02-expert-design §3.2 明确「2s 起、5 次、指数退避」；09-phase4 指出 vncStream 未重构为 createVncTransport 共享模式，导致双轨并存。 |

---

### 问题 3：vncStream 的 `status` 与 `connectStream` 守卫导致重连被阻止

| 项目 | 内容 |
|------|------|
| **位置** | `vncStream.ts` 第 124–126、203、205–209、329 行 |
| **描述** | 1) disconnect 时 `state.status = wasConnected ? 'disconnected' : 'error'`；error 时清除 `transportOrUrl`<br>2) `connectStream` 开头：`if (state.status === 'connected' \|\| state.status === 'connecting') return`<br>3) 重连由 `setTimeout` 回调调用 `connectStream(agentId, deviceId)` |
| **分析** | • 正常重连：disconnect → status='disconnected' → 2s 后 connectStream → status 已非 connected/connecting → 可进入<br>• 异常路径：disconnect 时若 `wasConnected === false`（例如连接中即断开），status='error'，transportOrUrl 被清空。2s 后 connectStream 被调用，status 为 'error'，守卫通过，可重连 ✓<br>• **潜在问题**：若 disconnect 与 connectStream 存在竞态，例如 disconnect 事件尚未把 status 从 'connecting' 改为 'error'，而 retryTimer 已触发，此时 status 仍为 'connecting'，connectStream 会直接 return，重连被跳过。 |
| **影响** | 在连接建立过程中发生断开时，存在小概率竞态，导致一次重连被跳过。 |

---

### 问题 4：retryTimer 清理与 subscribe 取消的竞态

| 项目 | 内容 |
|------|------|
| **位置** | `vncStream.ts` 第 283–305、316–344 行 |
| **描述** | 1) 用户取消订阅 → `unsubscribe()` → `disconnectStream(agentId)` → 清理 retryTimer、rfb.disconnect()<br>2) `connectStream` 为 async，可能在 `await vmService.getVncTransport()` 或 `await testWebSocket()` 中挂起<br>3) disconnectStream 将 `state.status='disconnected'`、`transportOrUrl=null`，但**不会取消正在进行的 connectStream** |
| **竞态** | • connectStream 在 await 中挂起 → 用户取消订阅 → disconnectStream 清空 state → connectStream 恢复后继续执行，会再次调用 `getVncTransport`（因 transportOrUrl 已清空），建立新连接<br>• 即使用户已取消订阅，仍可能建立新连接，造成资源浪费和潜在状态错乱 |
| **影响** | 取消订阅后仍可能触发新连接，违反「无订阅者则断开」的语义。 |

---

### 问题 5：vncStream 未使用 `clean` 区分用户断开，可能过度重连

| 项目 | 内容 |
|------|------|
| **位置** | `vncStream.ts` 第 189–226 行 |
| **描述** | vncStream 的 disconnect 处理**不检查** `e.detail?.clean`，只要有订阅者且 retryCount < 3 就重连。 |
| **分析** | 在 vncStream 场景下，用户「关闭」通常通过取消订阅实现，会先调用 disconnectStream，此时 subscribers.size=0，不会进入重连逻辑，因此当前实现是安全的。<br>但若未来有「程序化断开」且希望不重连的路径，vncStream 缺少对 clean 的区分。 |
| **影响** | 当前影响较小，但若扩展 disconnect 场景，可能产生过度重连。 |

---

## 二、与设计文档的偏差汇总

| 偏差 | 设计要求 | 当前实现 | 严重程度 |
|------|----------|----------|----------|
| D1 | §3.2 统一重连：2s 起、5 次、指数退避 | useVnc 符合；vncStream 为 2s 固定、3 次 | 中 |
| D2 | §3.2 连接断开后应重连 | useVnc 在 clean=true 时不重连，而服务器端断开也为 clean=true | **高** |
| D3 | §4.2 P4-17 vncStream 重构为 createVncTransport 共享模式 | 未完成，main 仍走 vncStream | 中 |
| D4 | 09-phase4 状态：connecting→connected→disconnected→reconnecting→failed | useVnc 有 reconnecting；vncStream 无 reconnecting，仅 disconnected/error | 低 |

---

## 三、修复建议（按优先级）

### P0：修复 useVnc 的 clean 误判（问题 1）

**方案**：不再用 `clean` 决定是否重连，改为用「是否由本端发起断开」判断。

```typescript
// useVnc.ts 增加 ref
const userInitiatedDisconnectRef = useRef(false);

// disconnect 中
const disconnect = useCallback(() => {
  userInitiatedDisconnectRef.current = true;
  // ... 原有逻辑
}, []);

// doConnect 开始时
userInitiatedDisconnectRef.current = false;

// disconnect 事件处理
rfb.addEventListener('disconnect', ((e: Event & { detail?: { clean?: boolean } }) => {
  if (!mountedRef.current) return;
  rfbRef.current = null;
  const weInitiated = userInitiatedDisconnectRef.current;
  if (weInitiated) {
    setStatus('disconnected');
    return;
  }
  // 非本端发起的断开 → 一律重连（服务器断开、网络中断等）
  setStatus('reconnecting');
  // ... 原有重连逻辑
}) as EventListener);
```

---

### P1：统一 vncStream 与 useVnc 的重连策略（问题 2）

将 vncStream 的重连参数与设计对齐：

```typescript
// vncStream.ts 使用与 useVnc 一致的常量
const RETRY_DELAY_MS = WS_CONFIG.VNC_RETRY_DELAY_MS ?? 2000;
const MAX_RETRIES = WS_CONFIG.VNC_MAX_RETRIES ?? 5;

// disconnect 与 catch 中的重连
const delay = RETRY_DELAY_MS * Math.pow(2, state.retryCount - 1);
if (state.subscribers.size > 0 && state.retryCount < MAX_RETRIES) {
  state.retryCount++;
  state.retryTimer = setTimeout(() => { ... }, delay);
}
```

---

### P2：connectStream 中增加订阅者检查，消除竞态（问题 4）

在 connectStream 的异步恢复点检查是否仍有订阅者：

```typescript
// connectStream 中，在 await 之后立即检查
const transport = await vmService.getVncTransport(agentId, deviceId).catch(...);
if (!state || state.subscribers.size === 0) return;  // 已取消订阅，放弃连接

if (typeof transport === 'string') {
  const wsAvailable = await testWebSocket(transport);
  if (!state || state.subscribers.size === 0) return;
  // ...
}
```

---

### P3：connectStream 守卫与 status 竞态缓解（问题 3）

在重连定时器回调中，重连前将 status 置为可进入状态，避免与 disconnect 事件竞态：

```typescript
state.retryTimer = setTimeout(() => {
  if (state && state.subscribers.size > 0) {
    state.status = 'disconnected';  // 确保非 connecting，允许 connectStream 进入
    connectStream(agentId, deviceId);
  }
}, delay);
```

---

### P4：长期 — 完成 P4-17，统一到 createVncTransport

将 vncStream 重构为 createVncTransport 的共享模式，使 main 与 vm_user 共用同一套连接与重连逻辑，从根本上消除双轨差异。

---

## 四、noVNC `detail.clean` 语义总结

| 场景 | noVNC 行为 | `detail.clean` |
|------|------------|----------------|
| 用户调用 `rfb.disconnect()` | 正常 disconnecting → disconnected | `true` |
| 服务器关闭连接（网络中断、VM 停止等） | _socketClose case 'connected'，不调用 _fail | `true` |
| 连接阶段失败（握手前断开） | _fail() | `false` |
| 认证/安全失败 | _fail() | `false` |
| 协议错误等 | _fail() | `false` |

**结论**：`clean === true` 无法区分「用户主动断开」与「服务器端断开」，不能作为是否重连的依据。应通过「本端是否发起 disconnect」来判断。
