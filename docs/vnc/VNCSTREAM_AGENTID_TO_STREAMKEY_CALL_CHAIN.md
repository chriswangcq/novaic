# vncStream.ts 调用链调研报告

> 为 P0 重命名 agentId→streamKey 做准备  
> 目标目录：novaic-app/src

---

## 1. vncStream.ts 导出的所有函数及其参数（agentId 相关）

| 函数名 | 第一参数（当前名 agentId） | 其他参数 | 说明 |
|--------|---------------------------|----------|------|
| `subscribeToVNCStream` | `agentId: string` | `subscriber: StreamSubscriber`, `deviceId?: string` | 订阅 VNC 流 |
| `getVNCStreamCanvas` | `agentId: string` | - | 获取共享 Canvas |
| `getVNCStreamStatus` | `agentId: string` | - | 获取流状态 |
| `setVNCViewOnly` | `agentId: string` | `viewOnly: boolean` | 设置 viewOnly 模式 |
| `sendVNCKey` | `agentId: string` | `keysym`, `code`, `down` | 发送按键事件 |
| `getVNCCanvasSize` | `agentId: string` | - | 获取 canvas 尺寸 |
| `sendVNCMouseDown` | `agentId: string` | `x`, `y`, `button` | 鼠标按下 |
| `sendVNCMouseUp` | `agentId: string` | `x`, `y`, `button` | 鼠标抬起 |
| `sendVNCMouseMove` | `agentId: string` | `x`, `y` | 鼠标移动 |
| `reconnectVNCStream` | `agentId: string` | `deviceId?: string` | 重新连接 |
| `getVNCRFB` | `agentId: string` | - | 获取 RFB 实例 |
| `attachVNCContainer` | `agentId: string` | `parent: HTMLElement` | 附加 RFB 容器 |
| `detachVNCContainer` | `agentId: string` | - | 分离 RFB 容器 |

**内部函数（非导出，也使用 agentId）：**
- `connectStream(agentId: string, deviceId?: string)`
- `disconnectStream(agentId: string)`

**内部存储：**
- `streams = new Map<string, StreamState>()`，key 为 agentId（实际语义为 stream key）

---

## 2. 所有 import 或调用 vncStream 的文件

| 文件路径 | 导入内容 |
|----------|----------|
| `src/components/Visual/VNCViewShared.tsx` | `subscribeToVNCStream`, `setVNCViewOnly`, `reconnectVNCStream`, `attachVNCContainer`, `detachVNCContainer`, `StreamStatus` |
| `src/components/Layout/DeviceFloatingPanel.tsx` | `setVNCViewOnly` |

**未在 novaic-app/src 中使用的导出函数：**
- `getVNCStreamCanvas`
- `getVNCStreamStatus`
- `sendVNCKey`
- `getVNCCanvasSize`
- `sendVNCMouseDown`
- `sendVNCMouseUp`
- `sendVNCMouseMove`
- `getVNCRFB`

---

## 3. 调用点清单（文件路径、行号、传入参数来源）

### 3.1 VNCViewShared.tsx

| 行号 | 调用函数 | 传入的 agentId 实际来源 | 说明 |
|------|----------|-------------------------|------|
| 94 | `subscribeToVNCStream(streamKey, {...}, propPcClientId)` | **streamKey** = `propDeviceId \|\| agentId \|\| ''` | 主桌面用 `propDeviceId`（device.id），否则用 `agentId` |
| 119 | `setVNCViewOnly(streamKey, vncLocked)` | **streamKey**（同上） | |
| 133 | `reconnectVNCStream(streamKey, propPcClientId)` | **streamKey**（同上） | startVm 成功后重连 |
| 139 | `reconnectVNCStream(streamKey, propPcClientId)` | **streamKey**（同上） | startVm 已运行时的重连 |
| 154 | `attachVNCContainer(streamKey, container)` | **streamKey**（同上） | |
| 158 | `detachVNCContainer(streamKey)` | **streamKey**（同上） | cleanup |

**VNCViewShared 中 streamKey 的来源链：**
```
streamKey = propDeviceId || agentId || ''
  - propDeviceId: 来自 props.deviceId（主桌面时传入 device.id）
  - agentId: propAgentId || storeAgentId
    - propAgentId: props.agentId
    - storeAgentId: useAppStore(state => state.currentAgentId)
```

**VNCViewShared 的 props 传入（来自 DeviceFloatingPanel 第 303 行）：**
```tsx
<VNCViewShared agentId={agentId} deviceId={device.id} pcClientId={device.pc_client_id} isThumbnail={!expanded} />
```
- `agentId` = DeviceCard 的 `agentId` = `currentAgentId`（来自 useAgent）
- `deviceId` = `device.id`（主桌面时与 VNC socket `novaic-vnc-{deviceId}.sock` 一致）

---

### 3.2 DeviceFloatingPanel.tsx

| 行号 | 调用函数 | 传入的 agentId 实际来源 | 说明 |
|------|----------|-------------------------|------|
| 209 | `setVNCViewOnly(device.id, !operating)` | **device.id** | 主桌面时，device.id 即 stream key |
| 214 | `setVNCViewOnly(device.id, true)` | **device.id** | cleanup 时恢复 viewOnly |

**说明：** DeviceFloatingPanel 中 `device` 来自 `useAgentBinding`，`device.id` 为 vmcontrol_device_id，主桌面时与 VNC 流 key 一致。

---

## 4. 下游依赖：vmService.getVncTransport

vncStream 内部 `connectStream` 调用：
```ts
vmService.getVncTransport(agentId, deviceId)
```

- 第一个参数：与 streams Map 的 key 一致，即当前语义下的「stream key」
- 第二个参数：`deviceId`（pc_client_id，多 PC 路由用）

---

## 5. 重命名影响范围总结

| 层级 | 文件 | 需修改项 |
|------|------|----------|
| 核心 | `vncStream.ts` | 所有导出/内部函数的 `agentId` 参数 → `streamKey`；Map key 注释；JSDoc |
| 调用方 | `VNCViewShared.tsx` | 已使用 `streamKey` 变量名，仅需确认与 API 参数名一致 |
| 调用方 | `DeviceFloatingPanel.tsx` | 传入 `device.id`，语义正确，参数名变更无影响 |

**语义澄清：**
- 当前「agentId」在 vncStream 中实际表示 **VNC 流的唯一标识**，主桌面时为 `device.id`，非主桌面时可能为 `agentId`。
- 重命名为 `streamKey` 更准确，与 `reconnectVNCStream` 的 JSDoc（`@param agentId stream key`）一致。
