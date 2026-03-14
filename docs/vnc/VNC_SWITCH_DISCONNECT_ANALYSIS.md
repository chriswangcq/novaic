# VNC 切换后快速断开 — 问题定位报告

## 现象

切到新 VNC 后连接成功，但很快断开。日志顺序：

```
[1-Bridge] 收到 data #1..#3
[3-useVnc] RFB connect 成功
[3-useVnc] doConnect 开始
[1-Bridge] close 调用 streamId=0f379034（不调用后端，由连接池 30s 空闲或新连接驱逐）
[3-useVnc] RFB disconnect reason=(empty) userInitiated=false
[3-useVnc] transport 已关闭(readyState=3)，跳过
```

## 调用链

`close()` 的调用来源只有两处：

| 来源 | 文件 | 条件 |
|------|------|------|
| `disconnect()` | useVnc.ts:77 | 关闭 `lastTransportRef` |
| `doConnect()` | useVnc.ts:104 | 关闭 `prevTransport`（仅当 `prevTransport !== t` 时） |

日志中的 `close` 来自 **`disconnect()`**，因为：

- `doConnect` 里的 close 会打印 `"doConnect 关闭 prevTransport (transport 已切换)"`
- 实际日志是 `"close 调用 streamId=..."`，对应 `vncBridge.ts:133`，即 `disconnect()` 调用了 `br.close()`

## disconnect() 的触发条件

`disconnect()` 在以下情况被调用：

1. **组件卸载**：`useEffect` 的 cleanup（useVnc.ts:176-179）
2. **effect 中 canConnect=false 且无 transport**：`useVnc.ts:201`  
   - `hasTransport = !!transport`  
   - `canConnect = hasTransport && containerReady && hasContainer`  
   - 当 `!hasTransport` 时执行 `disconnect()`

因此，**`transport` 变为 `null` 会触发 `disconnect()`**。

## 根因推断

`setTransport(null)` 导致 `transport === null`，进而触发 `disconnect()` → `br.close()`。

`setTransport(null)` 的调用位置：

1. **DeviceDesktopView effect**（DeviceDesktopView.tsx:131）：当 `vncTarget` 为 `null` 时
2. **stopDevice**（DeviceDesktopView.tsx:194）：用户点击 Stop

## 最可能原因：vncTarget 短暂为 null

DeviceDesktopView 的 effect 依赖 `[vncTarget, deviceStatus]`：

```ts
useEffect(() => {
  if (!vncTarget) {
    setTransport(null);  // ← 这里
    return;
  }
  createVncTransport(vncTarget).then(t => setTransport(t));
}, [vncTarget, deviceStatus]);
```

当 `vncTarget` 变为 `null` 时，会执行 `setTransport(null)`。

可能场景：

1. **父组件重渲染**：切换 subject 时，`deviceMode` / `binding` 等异步数据尚未就绪，`vncTarget` 的 useMemo 短暂返回 `null`
2. **useDeviceVncTarget 的 fetch**：`deviceId` 变化触发 refetch，在请求完成前 `vncTarget` 可能为旧值或空
3. **React Strict Mode**：开发环境双挂载，第一次 unmount 会触发 `disconnect()`，但第二次 mount 会重新创建 transport，时序上可能与日志不完全一致

## 建议排查步骤

1. **加日志确认 vncTarget 变化**  
   在 DeviceDesktopView 的 effect 中打印：
   - `vncTarget` 是否为 `null`
   - `deviceStatus` 的值
   - 每次 effect 执行时的 `reqId`

2. **确认是否在 Strict Mode**  
   检查 `main.tsx` 是否被 `<React.StrictMode>` 包裹。

3. **确认父组件切换逻辑**  
   查看 DeviceFloatingPanel / DeviceManagerPage 在切换 main ↔ vm_user 时的渲染逻辑，是否会出现 `deviceId` 或 `subjectId` 短暂为 `undefined` 的情况。

4. **确认 effect 执行顺序**  
   在 useVnc 的 effect 中打印 `canConnect`、`hasTransport`、`transport`，确认 `disconnect()` 被调用时的具体条件。

## 相关代码位置

| 文件 | 行号 | 说明 |
|------|------|------|
| vncBridge.ts | 127-138 | `close()` 实现 |
| useVnc.ts | 59-81 | `disconnect()` |
| useVnc.ts | 191-212 | effect 中调用 `disconnect()` 的条件 |
| DeviceDesktopView.tsx | 128-134 | `vncTarget` 为 null 时 `setTransport(null)` |
