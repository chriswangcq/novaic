# Device 状态管理与多 PC 场景调研（Round 2）

**调研日期**：2026-03-12  
**输入**：`DEVICE_MANAGEMENT_ROUND1.md`、`deviceStatusStore.ts`、`useDeviceStatusPolling`、`useDeviceStatus`  
**目标**：深入分析 DeviceStatusStore 复合 key、轮询调用方、多 PC 状态隔离、轮询依赖、listForUser 缓存影响

---

## 1. DeviceStatusStore 复合 key 实现：statusKey(deviceId, pcClientId)

### 1.1 实现位置与逻辑

**文件**：`novaic-app/src/stores/deviceStatusStore.ts`

```typescript
/** 复合 key：多 PC 时避免同一 device 不同 pc_client_id 互相覆盖 */
function statusKey(deviceId: string, pcClientId?: string | null): string {
  return pcClientId ? `${deviceId}:${pcClientId}` : deviceId;
}
```

| 场景 | 输入 | 输出 key |
|------|------|----------|
| 单 PC / 无 pc_client_id | `deviceId="abc"`, `pcClientId=undefined` | `"abc"` |
| 多 PC | `deviceId="abc"`, `pcClientId="pc-xyz"` | `"abc:pc-xyz"` |

### 1.2 使用点

| 方法 | 用途 |
|------|------|
| `setStatus(deviceId, status, pcClientId)` | 单条写入，key = statusKey(deviceId, pcClientId) |
| `setStatuses(entries)` | 批量写入，对每条 entry 用 statusKey(e.deviceId, e.pcClientId) |
| `getStatus(deviceId, pcClientId)` | 读取，key = statusKey(deviceId, pcClientId) |

### 1.3 useDeviceStatus 中的 key 一致性

`useDeviceStatus.ts` 内定义了**相同逻辑**的 `statusKey`（局部函数），与 store 保持一致：

```typescript
function statusKey(deviceId: string, pcClientId?: string | null): string {
  return pcClientId ? `${deviceId}:${pcClientId}` : deviceId;
}
```

**风险**：两处重复实现，若未来修改需同步，建议抽到共享 util。

---

## 2. useDeviceStatusPolling 调用方与触发条件

### 2.1 调用方一览

| 调用方 | 传入 devices | enabled 条件 | 触发时机 |
|--------|--------------|--------------|----------|
| **DeviceManagerPage** | `devices`（来自 listForUser） | `devices.length > 0` | 页面挂载且列表非空 |
| **DeviceFloatingPanel** | `device ? [device] : []` | `!!device` | 有 device 时（Agent 模式或 deviceMode） |
| **AgentDrawer** | `devices`（来自 listForUser） | `isOpen && devices.length > 0` | Drawer 打开且列表非空 |

### 2.2 触发条件详解

```
DeviceManagerPage:
  enabled = devices.length > 0
  → 自驱动，不依赖 AgentDrawer；drawer 关闭时仍轮询

DeviceFloatingPanel:
  enabled = !!device
  → device 来自 useAgentBinding 或 useDeviceVncTarget
  → 浮窗有设备时启动轮询，无设备时不轮询

AgentDrawer:
  enabled = isOpen && devices.length > 0
  → Drawer 关闭时停止轮询，减少无效请求
```

### 2.3 deviceKey 与 effect 依赖

```typescript
const deviceKey = useMemo(
  () => devices.map((d) => `${d.id}:${d.pc_client_id ?? ''}`).join(','),
  [devices]
);

useEffect(() => {
  // ...
}, [deviceKey, enabled, setStatuses, intervalMs]);
```

- **deviceKey**：`devices` 的稳定字符串表示，`id` 与 `pc_client_id` 变化会触发 effect 重建轮询
- **intervalMs**：依赖 `vncConnectionCount`，VNC 连接时 3s，否则 5s

### 2.4 轮询行为

- 对每个 device 调用 `api.devices.status(d.id, d.pc_client_id)`
- 结果批量写入 `DeviceStatusStore.setStatuses`
- 首次立即执行 `poll()`，之后按 `intervalMs` 定时执行

---

## 3. 多 PC 场景：同一 device 不同 pc_client_id 的状态隔离

### 3.1 数据流

```
Device (from listForUser / devices.get)
  └─ device.pc_client_id 表示该设备实例所在物理 PC

useDeviceStatusPolling(devices)
  └─ 对每个 device 调用 api.devices.status(id, pc_client_id)
  └─ 写入 Store: key = statusKey(deviceId, pcClientId)

useDeviceStatus(deviceId, pcClientId)
  └─ 从 Store 读取 key = statusKey(deviceId, pcClientId)
```

### 3.2 隔离保证

| 场景 | 说明 |
|------|------|
| 同一 device 在 PC-A | key=`deviceId:pcA`，状态独立 |
| 同一 device 在 PC-B | key=`deviceId:pcB`，状态独立 |
| 单 PC / 无 pc_client_id | key=`deviceId`，与多 PC key 不冲突 |

### 3.3 pc_client_id 来源

| 来源 | 说明 |
|------|------|
| `listForUser` 返回的 device | `device.pc_client_id` 由后端 DB 填充（devices.pc_client_id） |
| `devices.get(id)` 返回的 device | 同上 |
| `useDeviceVncTarget` | 从 `devices.get` 的 device 取 `pc_client_id` |
| `useAgentDevice` | 从 `devices.get` 的 device 取 `pc_client_id`，用于 VncTarget |

### 3.4 潜在问题

- **listForUser 返回的 device**：若后端未正确填充 `pc_client_id`，多 PC 场景下可能用 `deviceId` 作为 key，导致不同 PC 的状态互相覆盖
- **DeviceManagerPage 的 devices**：来自 listForUser，依赖后端返回的 `pc_client_id`
- **DeviceFloatingPanel 的 device**：来自 `useAgentBinding` 或 `useDeviceVncTarget`，均经 `devices.get`，通常有 `pc_client_id`

---

## 4. DeviceManagerPage 与 DeviceFloatingPanel 的轮询依赖

### 4.1 轮询入口关系

```
                    ┌─────────────────────────────────────────┐
                    │           DeviceStatusStore              │
                    │  statuses Map / setStatuses / getStatus   │
                    └─────────────────────────────────────────┘
                                         ▲
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
         useDeviceStatusPolling          │          useDeviceStatusPolling
         (DeviceManagerPage)             │          (DeviceFloatingPanel)
                    │                    │                    │
         devices from listForUser        │          device from binding/VncTarget
         enabled = devices.length>0      │          enabled = !!device
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │     useDeviceStatusPolling (AgentDrawer)  │
                    │  devices from listForUser                │
                    │  enabled = isOpen && devices.length>0    │
                    └─────────────────────────────────────────┘
```

### 4.2 DeviceManagerPage 轮询

- **数据源**：`devices` 来自 `api.devices.listForUser()`，写入 `deviceManagerDevices`（AppStore）
- **轮询**：`useDeviceStatusPolling(devices, devices.length > 0)`
- **状态展示**：`useDeviceStatus(deviceId, pcClientId)` 覆盖 `device.status`
- **特点**：自驱动，不依赖 AgentDrawer；Drawer 关闭时仍轮询

### 4.3 DeviceFloatingPanel 轮询

- **数据源**：
  - Agent 模式：`useAgentBinding` → `devices.get(binding.device_id)`
  - deviceMode：`useDeviceVncTarget(deviceId, subjectType, subjectId)` → `devices.get(id)`
- **轮询**：`useDeviceStatusPolling(device ? [device] : [], !!device)`
- **状态展示**：`useDeviceStatus(device?.id, device?.pc_client_id)`，用于 `isRunning` 判断
- **特点**：仅轮询当前浮窗展示的单个 device

### 4.4 依赖关系小结

| 组件 | 轮询依赖 | 数据依赖 |
|------|----------|----------|
| DeviceManagerPage | 独立，devices 来自自身 load | listForUser → deviceManagerDevices |
| DeviceFloatingPanel | 独立，仅轮询当前 device | useAgentBinding / useDeviceVncTarget |
| AgentDrawer | 依赖 isOpen | listForUser → deviceManagerDevices（与 Page 共享） |

三者均写入同一 DeviceStatusStore，通过 `useDeviceStatus` 读取，无直接调用链依赖。

---

## 5. listForUser 缓存与 30s TTL 的影响

### 5.1 listForUser 本身

- **API**：`GET /api/devices`，无前端显式缓存
- **调用方**：DeviceManagerPage（load）、AgentDrawer（loadDevices）
- **后端**：`repo.list_by_user(user_id)`，直接查 DB，无 30s 缓存

### 5.2 30s TTL 来源：useAgentDevice 的 deviceCache

**文件**：`novaic-app/src/hooks/useAgentDevice.ts`

```typescript
const deviceCache = new Map<string, { device: Device; ts: number }>();
const CACHE_TTL_MS = 30_000;

async function getDeviceCached(deviceId: string): Promise<Device> {
  const cached = deviceCache.get(deviceId);
  if (cached && Date.now() - cached.ts < CACHE_TTL_MS) {
    return cached.device;
  }
  const device = await api.devices.get(deviceId);
  deviceCache.set(deviceId, { device, ts: Date.now() });
  return device;
}
```

- **作用对象**：`devices.get(deviceId)`，**不是** listForUser
- **使用方**：`useAgentDevice`（AgentDrawer 高亮、AgentDesktopView 等）
- **影响**：同一 device 在 30s 内多次 `devices.get` 会命中缓存，`pc_client_id`、`status` 可能滞后

### 5.3 listForUser 与 status 滞后的关系

| 数据源 | 刷新频率 | status 新鲜度 |
|--------|----------|---------------|
| listForUser | DeviceManagerPage：仅 load 时；AgentDrawer：每 5s | 依赖后端 DB，可能滞后 |
| DeviceStatusStore | 5s（或 VNC 时 3s）轮询 | 实时 |

**设计**：组件用 `useDeviceStatus(deviceId, pcClientId)` 覆盖 `device.status`，避免 listForUser 返回的 status 滞后影响 UI。

### 5.4 影响小结

| 项目 | 影响 |
|------|------|
| listForUser 无 30s 缓存 | 列表本身无 TTL，但调用频率由各组件决定 |
| useAgentDevice 30s 缓存 | `devices.get` 的 device（含 pc_client_id）可能滞后 30s |
| status 覆盖策略 | useDeviceStatus 覆盖 device.status，减轻 listForUser 滞后影响 |
| 多 PC | useAgentDevice 的 cache key 仅 deviceId，未区分 pc_client_id，多 PC 同 device 可能读到错误缓存 |

### 5.5 多 PC 下的 useAgentDevice 缓存风险

```typescript
// useAgentDevice 的 getDeviceCached 仅用 deviceId 作为 key
deviceCache.get(deviceId)  // 未考虑 pc_client_id
```

若同一 device 在不同 PC 上有不同 `pc_client_id`，缓存会返回第一次请求的 device，可能导致 `pc_client_id` 错误。当前 useAgentDevice 主要用于 Agent 绑定设备，通常一个 Agent 绑定一个 device 实例，风险有限，但多 PC 场景下需注意。

---

## 6. 相关文件索引

| 文件 | 说明 |
|------|------|
| `novaic-app/src/stores/deviceStatusStore.ts` | statusKey、setStatus、setStatuses、getStatus |
| `novaic-app/src/hooks/useDeviceStatusPolling.ts` | 轮询逻辑、deviceKey、intervalMs |
| `novaic-app/src/hooks/useDeviceStatus.ts` | 从 Store 读取状态 |
| `novaic-app/src/hooks/useAgentDevice.ts` | 30s deviceCache、getDeviceCached |
| `novaic-app/src/components/VM/DeviceManagerPage.tsx` | useDeviceStatusPolling(devices) |
| `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | useDeviceStatusPolling([device]) |
| `novaic-app/src/components/Layout/AgentDrawer.tsx` | useDeviceStatusPolling(devices) |
| `novaic-app/src/config/index.ts` | POLL_CONFIG.VM_STATUS_FAST/NORMAL_INTERVAL |
