# VNC 连接问题分析 — 第一轮：createVncTransport 调用来源

## 1. 现象摘要

从前后端日志可见：

- **createVncTransport 被多次调用**：约 6–7 次，间隔 20–50ms
- **每次调用都会新建 stream**：610892fc → 9936ba4a → fd982c2c → be50b77e → 6299429e → 3b0c36ca → fa9c42ec → 35878066
- **每次新 transport 到来都会关闭上一个**：`doConnect` 中 `prevTransport !== t` 时关闭旧 transport
- **部分 stream 在 RFB 握手前就被关闭**：`send_count=0` 表示未发送任何数据即被关

## 2. createVncTransport 调用链

```
createVncTransport(target)
  ↑
AgentDesktopView useEffect
  deps: [vncTargetKey]
  vncTargetKey = `${vncTarget.resourceId}|${vncTarget.pcClientId ?? ''}`
```

**调用点**：
- `AgentDesktopView.tsx:47` — `useEffect` 中
- `AgentDesktopView.tsx:99` — `retryTransport` 中（用户点击 Retry）

## 3. vncTargetKey 与 effect 触发

```ts
const vncTargetKey = useMemo(
  () => (vncTarget ? `${vncTarget.resourceId}|${vncTarget.pcClientId ?? ''}` : null),
  [vncTarget?.resourceId, vncTarget?.pcClientId]
);
useEffect(() => { ... createVncTransport(target) ... }, [vncTargetKey]);
```

**vncTargetKey 变化场景**：
1. `vncTarget` 从 null → 有值：key 从 null 变为 `"666e2498...|"`
2. `resourceId` 变化：切换 agent
3. `pcClientId` 变化：`undefined` / `null` / `""` 在 key 中都会变成 `""`，一般不会变

**结论**：vncTargetKey 在单 agent 场景下应保持稳定，不应在几十毫秒内多次变化。

## 4. 可能的多重触发来源

### 4.1 React Strict Mode 双挂载

- 开发模式下 React 18 Strict Mode 会：mount → unmount → mount
- 每次 mount 都会重新执行 effect
- 预期：最多 2 次 createVncTransport，与 6–7 次不符

### 4.2 多个 AgentDesktopView 实例

- `VisualPanel` 中：
  - `isThumbnail`：`<AgentDesktopView embedded />`
  - 非 thumbnail：`{activeView === 'linux' && <AgentDesktopView />}`
- 两种模式互斥，通常不会同时渲染两个实例

### 4.3 useAgentDevice 多次更新 vncTarget

- `useAgentDevice` 的 `fetch` 会依次：`setBinding` → `setDevice` → `setVncTarget`
- 每次 `setState` 都会触发重渲染
- `bindingToVncTarget(b, d)` 每次返回新对象，但 `resourceId`、`pcClientId` 不变
- `vncTargetKey` 应不变，effect 不应重复执行

### 4.4 父组件多次挂载 AgentDesktopView

- 若父组件因布局/路由/条件渲染导致 AgentDesktopView 频繁 unmount/remount
- 每次 mount 都会执行 effect，产生新的 createVncTransport
- 需要检查：`LayoutContainer`、`ChatPanel`、`AgentDrawer` 等是否在短时间内多次挂载 VisualPanel/AgentDesktopView

## 5. 日志时间线（简化）

| 时间 (ms) | 事件 |
|-----------|------|
| 0 | createVncTransport 开始 |
| ~30 | vnc_stream_connect 成功 610892fc |
| ~50 | createVncTransport 开始（第二次） |
| ~80 | vnc_stream_connect 成功 9936ba4a |
| ~100 | close 610892fc（send_count=11，已握手） |
| ~120 | createVncTransport 开始（第三次） |
| ... | 持续重复 |

## 6. 第一轮结论

1. **vncTargetKey 稳定化未完全生效**：effect 仍被多次触发，说明存在 vncTargetKey 之外的因素。
2. **更可能的原因**：组件被多次 mount（Strict Mode 或父级条件渲染），每次 mount 都会重新跑 effect。
3. **下一步**：追踪 AgentDesktopView 的挂载/卸载时机，以及是否存在 transport 复用/缓存机制。
