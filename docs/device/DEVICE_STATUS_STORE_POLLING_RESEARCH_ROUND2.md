# Device 状态更新链路调研（第二轮·中层）

> 调研范围：DeviceStatusStore、useDeviceStatusPolling、useDeviceStatus、listForUser 的 status 覆盖关系及潜在竞态点。

---

## 1. DeviceStatusStore 数据结构与更新方式

### 1.1 数据结构

**文件**：`novaic-app/src/stores/deviceStatusStore.ts`

```ts
// 状态值类型
export type DeviceStatusValue = 'created' | 'setup' | 'ready' | 'running' | 'stopped' | 'error';

// 单条记录
export interface DeviceStatusEntry {
  deviceId: string;
  status: DeviceStatusValue;
  updatedAt: number;
}

// Store 状态
interface DeviceStatusState {
  statuses: Map<string, DeviceStatusEntry>;   // key = deviceId
  subscriberCount: number;                    // 未使用（设计预留）
  vncConnectionCount: number;                 // VNC 连接数，>0 时轮询降为 3s
  setStatus: (deviceId, status) => void;
  setStatuses: (entries: DeviceStatusEntry[]) => void;
  getStatus: (deviceId: string) => DeviceStatusValue | undefined;
  subscribeDevice: (deviceId: string) => () => void;
  incrementVncConnectionCount: () => void;
  decrementVncConnectionCount: () => void;
}
```

### 1.2 更新方式

| 方法 | 调用方 | 行为 |
|------|--------|------|
| `setStatus(deviceId, status)` | 未使用 | 单设备更新，合并到 Map |
| `setStatuses(entries)` | useDeviceStatusPolling | 批量更新，按 deviceId 覆盖 Map |
| `incrementVncConnectionCount` | useVnc、vncStream | VNC 连接成功时 +1 |
| `decrementVncConnectionCount` | useVnc、vncStream | VNC 断开时 -1 |

**注意**：`statuses` 的 key 仅为 `deviceId`，**不包含 pc_client_id**。多 PC 场景下，同一 device 的不同 pc_client_id 会互相覆盖（见 §4 竞态点）。

---

## 2. useDeviceStatusPolling 触发条件与轮询间隔

### 2.1 触发条件

**文件**：`novaic-app/src/hooks/useDeviceStatusPolling.ts`

```ts
export function useDeviceStatusPolling(devices: Device[], enabled = true)
```

| 条件 | 说明 |
|------|------|
| `enabled === true` | 由调用方传入 |
| `devices.length > 0` | 有设备才启动轮询 |

**Effect 依赖**：`[deviceKey, enabled, setStatuses, intervalMs]`

- `deviceKey` = `devices.map(d => \`${d.id}:${d.pc_client_id ?? ''}\`).join(',')`
- `intervalMs` 随 `vncConnectionCount` 变化（见下）

### 2.2 轮询间隔

| 场景 | 间隔 | 配置 |
|------|------|------|
| 无 VNC 连接 | 5s | `POLL_CONFIG.VM_STATUS_NORMAL_INTERVAL` |
| 有 VNC 连接 (vncConnectionCount > 0) | 3s | `POLL_CONFIG.VM_STATUS_FAST_INTERVAL` |

**配置位置**：`novaic-app/src/config/index.ts` L83-94

### 2.3 调用方一览

| 组件 | 调用方式 | enabled 条件 |
|------|----------|-------------|
| **AgentDrawer** | `useDeviceStatusPolling(devices, isOpen && devices.length > 0)` | 抽屉打开且 devices 非空 |
| **DeviceFloatingPanel** | `useDeviceStatusPolling(device ? [device] : [], !!device)` | 有 device 时 |

**DeviceManagerPage 未调用 useDeviceStatusPolling**，依赖 AgentDrawer 或 DeviceFloatingPanel 驱动轮询。

---

## 3. useDeviceStatus 与 listForUser 的 status 覆盖关系

### 3.1 覆盖规则

**原则**：`useDeviceStatus` 优先，`device.status` 为 fallback。

```ts
// DeviceManagerPage DeviceRow (L69-70)
const storeStatus = useDeviceStatus(device.id);
const status = (storeStatus ?? device.status) as DeviceStatus;

// AgentDrawer DeviceListItem (L218-219)
const storeStatus = useDeviceStatus(device.id);
const status = storeStatus ?? device.status;

// DeviceManagerPage 选中设备 (L696-698)
const selectedDeviceStatus = useDeviceStatus(selectedDevice?.id ?? null);
const effectiveSelectedDevice = selectedDevice
  ? { ...selectedDevice, status: (selectedDeviceStatus ?? selectedDevice.status) as DeviceStatus }
  : null;
```

### 3.2 数据来源对比

| 来源 | 更新频率 | 说明 |
|------|----------|------|
| **listForUser** | 挂载时 + 5s 轮询（AgentDrawer） | 返回设备列表，含 `status`；后端可能有 30s 缓存 |
| **DeviceStatusStore** | 5s/3s 轮询（useDeviceStatusPolling） | 调用 `api.devices.status(deviceId, pcClientId)` 实时获取 |

### 3.3 覆盖关系示意

```
listForUser()  →  device.status  (可能滞后 30s)
                        │
                        │  fallback
                        ▼
useDeviceStatusPolling  →  api.devices.status()  →  DeviceStatusStore  →  useDeviceStatus()
                        │
                        └─────────────────────────────────────────────────────────────────┐
                                                                                            │
最终展示: status = storeStatus ?? device.status   (优先 Store，无则用 listForUser 的 status)  │
```

---

## 4. Device 状态更新链路

### 4.1 完整链路图

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              Gateway API                                                    │
│  GET /api/devices (listForUser)     GET /api/devices/{id}/status (轮询)                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
         │                                          │
         │ 5s (AgentDrawer loadDevices)              │ 5s / 3s (VNC 连接时)
         ▼                                          ▼
┌─────────────────────┐                  ┌─────────────────────────────────────────────────────────────────┐
│ listForUser()       │                  │ useDeviceStatusPolling                                          │
│ → device.status     │                  │ ┌─────────────────────────────────────────────────────────────┐ │
│ (可能 30s 缓存滞后)  │                  │ │ AgentDrawer: devices, isOpen && devices.length > 0            │ │
└─────────────────────┘                  │ │ DeviceFloatingPanel: [device], !!device                        │ │
         │                                │ └─────────────────────────────────────────────────────────────┘ │
         │                                │         ↓ api.devices.status()                                 │
         │                                │         ↓ setStatuses(entries)                                 │
         │                                └─────────────────────────────────────────────────────────────────┘
         │                                          │
         │                                          ▼
         │                                ┌─────────────────────────────────────────────────────────────────┐
         │                                │ DeviceStatusStore (statuses: Map<deviceId, DeviceStatusEntry>)  │
         │                                │ vncConnectionCount ← useVnc / vncStream increment/decrement     │
         │                                └─────────────────────────────────────────────────────────────────┘
         │                                          │
         │                                          │ useDeviceStatusStore(selector)
         │                                          ▼
         │                                ┌─────────────────────────────────────────────────────────────────┐
         │                                │ useDeviceStatus(deviceId)                                       │
         │                                │ → s.statuses.get(deviceId)?.status                               │
         │                                └─────────────────────────────────────────────────────────────────┘
         │                                          │
         └──────────────────────────────────────────┼──────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                              status = storeStatus ?? device.status
                              (DeviceRow, DeviceListItem, effectiveSelectedDevice)
```

### 4.2 轮询驱动依赖关系

| 组件 | 是否驱动轮询 | 是否消费 status |
|------|-------------|-----------------|
| AgentDrawer | ✅ | ✅ DeviceListItem |
| DeviceFloatingPanel | ✅ | ✅ |
| DeviceManagerPage | ❌ | ✅ DeviceRow, VmUsersSection, effectiveSelectedDevice |

**结论**：DeviceManagerPage 依赖 AgentDrawer 或 DeviceFloatingPanel 先启动轮询；若两者均未挂载/未启用，Store 无更新，`useDeviceStatus` 返回 `undefined`，退化为 `device.status`。

---

## 5. 潜在竞态点

### 5.1 轮询驱动缺失（DeviceManagerPage 无轮询）

**场景**：activeView=devices，但 AgentDrawer 的 drawer 被关闭（drawerOpen=false）。

- AgentDrawer 的 `useDeviceStatusPolling(devices, isOpen && devices.length > 0)` 中 `enabled=false`
- DeviceManagerPage 不调用 useDeviceStatusPolling
- Store 无新数据，`useDeviceStatus` 可能一直为 `undefined`，仅显示 listForUser 的旧 status

**影响**：低（PC 布局下 drawer 通常打开；手机式第三栏时 DeviceManagerPage 独立显示，但 AgentDrawer 可能在第二栏已加载过 devices）

---

### 5.2 多 PC 场景下 Store 碰撞

**场景**：同一 device 有多个 pc_client_id（多物理机）。

- `setStatuses` 的 key 仅为 `deviceId`，不含 `pc_client_id`
- 轮询时 `deviceKey` 区分 `id:pc_client_id`，但写入 Store 时只按 `deviceId` 覆盖
- 后写入的 PC 状态会覆盖先写入的

**代码**：`useDeviceStatusPolling.ts` L36-37

```ts
return { deviceId: d.id, status, updatedAt: Date.now() };
// 缺少 pc_client_id，多 PC 会互相覆盖
```

**影响**：中（多 PC 部署时，设备状态可能显示错误 PC 的状态）

---

### 5.3 listForUser 与 Store 的时序

**场景**：listForUser 刚返回（status=stopped），用户点击 Start，设备实际已 running，但 listForUser 有 30s 缓存。

- Store 轮询 5s 一次，可能在 listForUser 刷新前就拿到 running
- `status = storeStatus ?? device.status` 优先 Store，可缓解
- 若 Store 尚未有该 device 的轮询结果（轮询未覆盖到），则仍显示 device.status（stopped）

**影响**：低（设计上已用 Store 覆盖 listForUser 的 status）

---

### 5.4 多实例重复轮询

**场景**：多 tab 或同一页面多个 useDeviceStatusPolling 实例（如 AgentDrawer + DeviceFloatingPanel 同时展示）。

- 每个实例独立 setInterval，会重复请求 `api.devices.status`
- Store 为单例，写入会合并，最终状态一致
- 仅增加请求量，无逻辑错误

**影响**：低（可优化为全局单一轮询，按订阅 device 集合合并）

---

### 5.5 vncConnectionCount 与轮询间隔不同步

**场景**：vncStream 路径未调用 `incrementVncConnectionCount`（文档称已修复，需确认）。

- useVnc 路径：连接时 increment，断开时 decrement ✅
- vncStream 路径：`vncStream.ts` L193-194、L226、L282 已调用 increment/decrement ✅

**结论**：vncStream 已接入，main 与 vm_user 路径轮询间隔应一致。

---

### 5.6 deviceKey 的 useMemo 依赖

**代码**：`useDeviceStatusPolling.ts` L23-26

```ts
const deviceKey = useMemo(
  () => devices.map((d) => `${d.id}:${d.pc_client_id ?? ''}`).join(','),
  [devices]
);
```

- `devices` 引用变化会触发 useMemo 重算
- 若父组件每次渲染传入新数组引用（即使内容相同），会导致 effect 频繁重启
- 建议：父组件用 `useMemo` 稳定 devices 引用，或 deviceKey 用深度比较

**影响**：低

---

## 6. 小结

| 维度 | 结论 |
|------|------|
| **DeviceStatusStore** | Map<deviceId, Entry>，setStatuses 批量更新，vncConnectionCount 控制轮询间隔 |
| **useDeviceStatusPolling** | enabled + devices.length > 0 时启动；5s/3s 间隔；AgentDrawer、DeviceFloatingPanel 调用 |
| **useDeviceStatus vs listForUser** | status = storeStatus ?? device.status，Store 优先 |
| **DeviceManagerPage** | 不驱动轮询，依赖 AgentDrawer/DeviceFloatingPanel |
| **主要竞态** | 多 PC 碰撞、DeviceManagerPage 无轮询时 Store 可能为空 |
