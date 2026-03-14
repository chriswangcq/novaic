# Phase 4 VNC 收敛代码审核报告

**审核范围**：novaic-app Phase 4 VNC 相关文件  
**审核日期**：2025-03-12  
**审核重点**：职责分离、依赖关系、状态管理、React 最佳实践、类型设计

---

## 一、架构概览

```
AgentDesktopView / DeviceDesktopView
    ↓ useAgentDevice / buildVncTarget
    ↓ createVncTransport (vncTransport.ts)
    ↓ VncCanvas (transport, options)
        ↓ useVnc (transport, containerRef, options)
            ↓ RFB + deviceStatusStore
```

**分层**：
- **传输层**：`vncTransport.ts`、`vncBridge.ts`
- **会话层**：`useVnc.ts`
- **展示层**：`VncCanvas`、`AgentDesktopView`、`DeviceDesktopView`、`DeviceVNCView`

---

## 二、问题列表

### Critical（严重）

#### C1. useVnc：transport 切换时 VncBridgeTransport 可能未正确关闭

**文件**：`novaic-app/src/hooks/useVnc.ts`

**描述**：当 `transport` 从 A 切换到 B 时，effect 会调用 `doConnect()` 创建新 RFB。`doConnect` 会 `rfbRef.current.disconnect()` 断开旧 RFB，但 `disconnect()` 仅在组件 unmount 时调用。若 A 是 `VncBridgeTransport`，其 `close()` 只在 `disconnect()` 中执行；transport 切换时不会调用 `disconnect()`，导致旧 Bridge 连接可能泄漏。

**影响**：OTA 模式下多次切换 Agent/设备时，Tauri 侧 bridge 连接累积，可能导致资源耗尽或连接数超限。

**建议**：在 `doConnect` 开头、断开旧 RFB 之后，显式关闭旧的 `VncBridgeTransport`：

```ts
// doConnect 开头，在 rfbRef.current.disconnect() 之后
const oldTransport = transportRef.current;
if (oldTransport && typeof oldTransport !== 'string' && 'close' in oldTransport) {
  (oldTransport as VncBridgeTransport).close();
}
```

注意：需在创建新 RFB 前执行，且要避免关闭即将使用的新 transport（通过比较引用或时序处理）。

---

#### C2. useVnc：doConnect 依赖缺失 containerRef，首次渲染可能不连接

**文件**：`novaic-app/src/hooks/useVnc.ts`（约 149–158 行）

**描述**：effect 依赖为 `[transport, doConnect]`，条件为 `transport && containerRef.current`。首次挂载时，effect 在 commit 后执行，`containerRef.current` 通常已有值；但若父组件用 `display:none` 或条件渲染延迟挂载容器，`containerRef.current` 可能仍为 null，导致不连接。且 effect 不依赖 `containerRef`，ref 从 null 变为有值时不会重新执行。

**影响**：部分布局下 VNC 可能永远不连接，或连接时机不可靠。

**建议**：
1. 使用 `useLayoutEffect` 或增加对容器挂载的监听（如 ResizeObserver / 简单轮询），在容器就绪时重试；
2. 或使用 `containerRef` 作为依赖（需用 state 触发 ref 更新后的重跑），例如：

```ts
const [containerReady, setContainerReady] = useState(false);
useEffect(() => {
  if (containerRef.current && !containerReady) setContainerReady(true);
}, []);
// effect 依赖 [transport, doConnect, containerReady]
```

---

### Major（重要）

#### M1. AgentDesktopView / DeviceDesktopView：renderOverlay 重复实现

**文件**：`AgentDesktopView.tsx`（48–91 行）、`DeviceDesktopView.tsx`（135–181 行）

**描述**：两处 `renderOverlay` 逻辑几乎相同（connecting / failed / reconnecting / disconnected 的 UI），仅文案略有差异，存在明显重复。

**影响**：修改 overlay 行为需改两处，易遗漏，维护成本高。

**建议**：抽取公共组件，例如 `VncConnectionOverlay`：

```tsx
// components/Visual/VncConnectionOverlay.tsx
export function VncConnectionOverlay({ status, errorMsg, onRetry }: {...}) {
  // 统一 UI 逻辑
}
```

两处改为传入 `renderOverlay={(ctx) => <VncConnectionOverlay {...ctx} onRetry={ctx.connect} />}`。

---

#### M2. useVnc：doConnect 的 useCallback 依赖不完整

**文件**：`novaic-app/src/hooks/useVnc.ts`（71–131 行）

**描述**：`doConnect` 依赖 `[scaleViewport, clipViewport, viewOnly]`，但内部使用了 `containerRef`。ref 变化不会触发回调更新，通常可接受；但 `doConnect` 作为 effect 依赖，当 `scaleViewport` 等变化时，会触发「断开并重连」，可能造成不必要的重连。

**影响**：用户调整 viewOnly 等选项时，会触发完整重连，体验不佳。

**建议**：区分「必须重连」与「可热更新」的选项。对 `scaleViewport`、`clipViewport`、`viewOnly`，若 RFB 支持运行时更新，则直接改属性而不重连；否则在文档中明确「这些选项变更会触发重连」。

---

#### M3. useAgentDevice：deviceCache 为模块级可变单例

**文件**：`novaic-app/src/hooks/useAgentDevice.ts`（23–33 行）

**描述**：`deviceCache` 是模块级 `Map`，多实例、多 Agent 共享，且无大小限制，只有 TTL。

**影响**：长时间使用会积累大量缓存；SSR/测试时可能跨请求共享；无淘汰策略，内存可能持续增长。

**建议**：
1. 限制 cache 大小（如 LRU，最多 N 条）；
2. 或将 cache 放入 Context/Store，便于测试与隔离；
3. 至少增加 `maxSize` 与淘汰逻辑。

---

#### M4. DeviceDesktopView：vncTarget 变化时 transport 未及时清理

**文件**：`novaic-app/src/components/Visual/DeviceDesktopView.tsx`（87–108 行）

**描述**：当 `vncTarget` 变化（如从 maindesk 切到 vm_user）时，effect 会 `setTransport(null)` 并重新 `createVncTransport`。但在 `createVncTransport` resolve 之前，旧 `transport` 仍会传给 `VncCanvas`，`useVnc` 会继续使用旧连接直到新 transport 就绪。

**影响**：切换目标时会有短暂「旧画面 + 新目标」重叠，或旧连接未及时释放。

**建议**：在 effect 开头立即 `setTransport(null)`，再发起 `createVncTransport`，确保切换时先断开旧连接：

```ts
useEffect(() => {
  if (!vncTarget) {
    setTransport(null);
    setTransportError(null);
    return;
  }
  if (isMaindesk && deviceStatus !== 'running') {
    setTransport(null);
    setTransportError(null);
    return;
  }
  setTransport(null);  // 立即清空，触发 useVnc 断开
  let cancelled = false;
  setTransportError(null);
  createVncTransport(vncTarget)...
```

---

#### M5. useVnc：incrementVnc/decrementVnc 的 effect 可能重复执行

**文件**：`novaic-app/src/hooks/useVnc.ts`（142–147 行）

**描述**：effect 依赖 `[status, incrementVnc, decrementVnc]`。Zustand 的 selector 返回函数时，每次可能返回新引用，导致 effect 多次执行，从而多次 `incrementVnc`/`decrementVnc`。

**影响**：`vncConnectionCount` 可能偏大，轮询间隔长期处于「高活跃」状态。

**建议**：用 `useDeviceStatusStore.getState()` 在 effect 内直接调用，或确保 selector 返回稳定引用：

```ts
const store = useDeviceStatusStore.getState();
useEffect(() => {
  if (status === 'connected') {
    store.incrementVncConnectionCount();
    return () => store.decrementVncConnectionCount();
  }
}, [status]);
```

或使用 Zustand 的 `useShallow` 等保证引用稳定。

---

### Minor（轻微）

#### m1. VncCanvas：未使用 React.memo

**文件**：`novaic-app/src/components/Visual/VncCanvas.tsx`

**描述**：`VncCanvas` 为展示组件，父组件重渲染时会连带重渲染，而 `renderOverlay` 常为内联函数，易导致不必要更新。

**影响**：轻微性能影响，在复杂布局下可能放大。

**建议**：对 `VncCanvas` 使用 `memo`，并让父组件用 `useCallback` 稳定 `renderOverlay`。

---

#### m2. useVnc：初始 status 为 'connecting' 可能不准确

**文件**：`novaic-app/src/hooks/useVnc.ts`（41 行）

**描述**：`status` 初始为 `'connecting'`，但若 `transport` 为 null，实际应为 `'disconnected'`。

**影响**：短暂显示「Connecting…」后变为「Disconnected」，体验略差。

**建议**：根据 `transport` 初始化：

```ts
const [status, setStatus] = useState<VncSessionStatus>(
  () => (transport ? 'connecting' : 'disconnected')
);
```

或保持现状，在首次 effect 中根据 `transport` 再设一次。

---

#### m3. AgentDesktopView：vncTarget 存在时仍可能渲染「No device bound」

**文件**：`novaic-app/src/components/Visual/AgentDesktopView.tsx`（119–126 行）

**描述**：`!vncTarget` 的分支在 `!agentId`、`isLoading`、`error` 之后。若 `vncTarget` 为 null 但 `binding` 存在且 `device` 未加载完，可能显示「No device bound」，语义略模糊。

**影响**：边界情况下提示不够准确。

**建议**：区分「无 binding」与「binding 存在但 device 加载中」，给出更精确的提示。

---

#### m4. DeviceDesktopView：buildVncTarget 对 vm_user 的 pcClientId 处理

**文件**：`novaic-app/src/components/Visual/DeviceDesktopView.tsx`（41–58 行）

**描述**：`vm_user` 的 `VncTarget` 中 `pcClientId` 来自 `props.pcClientId`，可选。若未传，后端会从 my-devices 解析，逻辑正确，但类型与文档未明确说明。

**影响**：后续维护者可能误以为 `pcClientId` 必填。

**建议**：在 `VncTarget` 或 `buildVncTarget` 处补充注释，说明 `pcClientId` 可选及 fallback 行为。

---

#### m5. 类型：VncTransport 为 string | VncBridgeTransport 的联合类型

**文件**：`novaic-app/src/services/vncTransport.ts`（14 行）

**描述**：`VncTransport` 为 `string | VncBridgeTransport`，使用时需类型守卫。`useVnc` 中已有 `typeof t !== 'string' && 'close' in t` 的判断，但分散在多处。

**影响**：类型不够精确，易在扩展时出错。

**建议**：定义 discriminated union 或类型守卫函数：

```ts
export type VncTransport = string | VncBridgeTransport;
export function isBridgeTransport(t: VncTransport): t is VncBridgeTransport {
  return typeof t !== 'string' && 'close' in t;
}
```

统一用 `isBridgeTransport(t)` 判断并调用 `close()`。

---

#### m6. DeviceVNCView：Android 与 Linux 分支结构不对称

**文件**：`novaic-app/src/components/Visual/DeviceVNCView.tsx`

**描述**：Linux 直接返回 `DeviceDesktopView`，Android 则在组件内维护 status、start/stop 等，两分支结构不一致。

**影响**：可读性一般，后续扩展需理解两套逻辑。

**建议**：若 Android 的 start/stop 与 DeviceDesktopView 的 maindesk 逻辑类似，可考虑抽成公共逻辑或子组件，减少重复。

---

## 三、依赖关系检查

| 依赖方向 | 是否合理 |
|----------|----------|
| VncCanvas → useVnc | ✓ |
| useVnc → vncTransport, vncBridge, deviceStatusStore | ✓ |
| AgentDesktopView → useAgentDevice, createVncTransport, VncCanvas | ✓ |
| DeviceDesktopView → createVncTransport, VncCanvas, api | ✓ |
| DeviceVNCView → DeviceDesktopView, ScrcpyView | ✓ |
| useAgentDevice → api | ✓ |

**结论**：未发现循环依赖。`vncTransport` → `vncBridge` 为单向依赖，结构清晰。

---

## 四、职责分离评估

| 层级 | 职责 | 评价 |
|------|------|------|
| 传输层 (vncTransport) | 根据 VncTarget 创建 WebSocket URL 或 VncBridgeTransport | ✓ 职责清晰 |
| 会话层 (useVnc) | RFB 生命周期、重连、状态、store 通知 | ⚠ 与 deviceStatusStore 耦合，可考虑通过回调解耦 |
| 展示层 (VncCanvas) | 挂载容器、调用 useVnc、渲染 overlay | ✓ 边界清晰 |
| 视图层 (AgentDesktopView 等) | 获取 target、创建 transport、布局与 overlay | ✓ 合理 |

---

## 五、React 实践评估

| 项目 | 评价 |
|------|------|
| Hooks 规则 | ✓ 无违规 |
| useCallback 依赖 | ⚠ M2：doConnect 依赖可能导致多余重连 |
| useMemo | 未使用，当前场景可接受 |
| memo | ⚠ m1：VncCanvas 可加 memo |
| 条件调用 Hooks | ✓ 无违规 |
| Ref 使用 | ✓ 合理，mountedRef 防止 unmount 后 setState |

---

## 六、总结与优先级建议

| 优先级 | 问题编号 | 建议处理顺序 |
|--------|----------|--------------|
| P0 | C1, C2 | 优先修复，影响正确性与稳定性 |
| P1 | M1, M4, M5 | 减少重复、修复资源与状态问题 |
| P2 | M2, M3 | 优化体验与可维护性 |
| P3 | m1–m6 | 按排期逐步改进 |

**整体评价**：Phase 4 的 VNC 分层和依赖关系设计合理，传输/会话/展示边界清晰。主要风险集中在 `useVnc` 的 transport 切换与容器就绪时机，以及部分重复逻辑和状态管理细节。建议优先处理 C1、C2，再按优先级逐步处理 Major 与 Minor 项。
