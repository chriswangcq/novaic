# Device 状态竞态与多 PC 场景调研（第三轮·深层）

> 调研范围：同一 device_id 多 pc_client_id 时 DeviceStatusStore 覆盖、DeviceManagerPage 无轮询时的状态滞后、listForUser 与 devices.status 缓存不一致。

---

## 一、同一 device_id 多 pc_client_id 时 DeviceStatusStore 的覆盖

### 1.1 现状

**DeviceStatusStore 数据结构**（`novaic-app/src/stores/deviceStatusStore.ts`）：

```ts
statuses: Map<string, DeviceStatusEntry>  // key = deviceId 仅此
interface DeviceStatusEntry {
  deviceId: string;
  status: DeviceStatusValue;
  updatedAt: number;
}
```

**useDeviceStatusPolling 写入逻辑**（`novaic-app/src/hooks/useDeviceStatusPolling.ts` L31-44）：

```ts
const entries = await Promise.all(
  devices.map(async (d) => {
    const r = await api.devices.status(d.id, d.pc_client_id);  // 按 (id, pc_client_id) 请求
    return { deviceId: d.id, status, updatedAt: Date.now() };   // 写入时仅用 deviceId
  })
);
setStatuses(entries);  // next.set(e.deviceId, e) — 按 deviceId 覆盖
```

**useDeviceStatus 读取逻辑**（`novaic-app/src/hooks/useDeviceStatus.ts`）：

```ts
return useDeviceStatusStore((s) =>
  deviceId ? s.statuses.get(deviceId)?.status : undefined  // 仅按 deviceId 查
);
```

### 1.2 竞态分析

| 场景 | 说明 | 影响 |
|------|------|------|
| **当前后端** | `listForUser` 每设备一行，每行一个 `pc_client_id`，device_id 唯一 | 无覆盖（每设备一个 pc_client_id） |
| **未来扩展** | 若后端支持「同一 device 部署于多 PC」并返回多行（同 id 不同 pc_client_id） | **后写入覆盖先写入**，展示错误 PC 的状态 |
| **Promise.all 竞态** | 多设备并行请求，完成顺序不定；`setStatuses` 批量写入，同 deviceId 后者覆盖前者 | 同一 device 多实例时必现 |

### 1.3 根因

- Store 的 key 仅为 `deviceId`，未包含 `pc_client_id`
- 轮询时按 `(deviceId, pc_client_id)` 请求，但写入时丢弃 `pc_client_id`
- `useDeviceStatus(deviceId)` 无法区分同一 device 在不同 PC 上的状态

---

## 二、DeviceManagerPage 无 useDeviceStatusPolling 时 drawer 关闭后的状态滞后

### 2.1 轮询驱动方

| 组件 | 是否调用 useDeviceStatusPolling | enabled 条件 |
|------|--------------------------------|-------------|
| **AgentDrawer** | ✅ | `isOpen && devices.length > 0` |
| **DeviceFloatingPanel** | ✅ | `!!device` |
| **DeviceManagerPage** | ❌ | — |

### 2.2 布局与挂载关系

**PC 布局**（`LayoutContainer.tsx` L176-246）：

```
PrimaryNav | AgentDrawer (isOpen=drawerOpen) | Main
                                    ↓
                          activeView=devices 时
                                    ↓
                          DeviceManagerPage（第三栏）
```

- AgentDrawer 常驻挂载，`drawerOpen` 控制展开/收起
- `useDeviceStatusPolling(devices, isOpen && devices.length > 0)`：drawer 关闭时 `enabled=false`，轮询停止

**手机布局**（`LayoutContainer.tsx` L127-173）：

- `isThirdColumn` 且 `activeView=devices` 时：**仅渲染 DeviceManagerPage**，AgentDrawer 不在当前树中
- AgentDrawer 在 `isSecondColumn` 分支，与第三栏互斥 → **DeviceManagerPage 可见时 AgentDrawer 未挂载**

### 2.3 滞后场景

| 场景 | 现象 |
|------|------|
| **PC：drawer 关闭** | AgentDrawer 仍在树中但 `isOpen=false`，轮询停止；DeviceManagerPage 仍显示，Store 不再更新，状态停留在关闭前最后一次轮询 |
| **手机：切到 Devices** | 第三栏只渲染 DeviceManagerPage，无 AgentDrawer，无任何 useDeviceStatusPolling；Store 无新数据，`useDeviceStatus` 多为 `undefined`，退化为 `device.status`（listForUser 的 30s 缓存） |

### 2.4 数据流

```
AgentDrawer isOpen=true  →  useDeviceStatusPolling enabled  →  Store 更新
        ↓
AgentDrawer isOpen=false 或 手机式第三栏
        ↓
无轮询  →  Store 停更  →  useDeviceStatus 返回旧值/undefined  →  status = storeStatus ?? device.status
```

---

## 三、listForUser 与 devices.status 的缓存不一致

### 3.1 数据源对比

| 来源 | API | 更新频率 | 缓存 |
|------|-----|----------|------|
| **listForUser** | `GET /api/devices` | AgentDrawer/DeviceManagerPage 挂载 + 5s 轮询 | 后端可能有 30s 缓存 |
| **devices.status** | `GET /api/devices/{id}/status?pc_client_id=xxx` | useDeviceStatusPolling 5s/3s | 实时查询 VmControl |

### 3.2 覆盖规则

```ts
// DeviceRow、DeviceListItem、effectiveSelectedDevice 等
const storeStatus = useDeviceStatus(device.id);
const status = (storeStatus ?? device.status) as DeviceStatus;
```

- 优先用 Store（来自 devices.status 轮询）
- Store 无数据时用 `device.status`（来自 listForUser）

### 3.3 不一致场景

| 场景 | listForUser | Store | 展示 |
|------|-------------|-------|------|
| 轮询正常 | status=stopped（30s 缓存） | status=running（5s 前） | running ✅ |
| 无轮询（drawer 关/手机） | status=stopped（30s 缓存） | undefined | stopped ❌ 可能已变 |
| Start 后 | status 仍 stopped（未刷新） | 5s 内可拿到 running | 有轮询时正确 |
| 多 PC 覆盖 | — | 后写入覆盖前者 | 可能显示错误 PC 的状态 |

### 3.4 deviceManagerDevices 与 listForUser

- `deviceManagerDevices`：AgentDrawer、DeviceManagerPage 的 listForUser 结果写入 AppStore
- 两处独立调用 listForUser，可能时序不同，但最终都写入同一 store
- 与 DeviceStatusStore 无直接关系；status 不一致来自 listForUser 的 status 与 devices.status 的差异

---

## 四、多 PC 竞态分析汇总

### 4.1 竞态矩阵

| 竞态点 | 触发条件 | 严重度 | 当前是否必现 |
|--------|----------|--------|--------------|
| Store 按 deviceId 覆盖 | 同一 device_id 多 pc_client_id | 高 | 否（当前后端每设备单 pc_client_id） |
| DeviceManagerPage 无轮询 | drawer 关闭 或 手机式 Devices 视图 | 中 | 是 |
| listForUser 与 status 不一致 | 无轮询 或 后端缓存未刷新 | 中 | 是（无轮询时） |
| deviceManagerDevices 与 listForUser | 两处独立调用 | 低 | 偶发（时序差异） |

### 4.2 时序示意

```
                    listForUser (5s)              devices.status (5s/3s)
                           │                              │
                           ▼                              ▼
                    device.status                   DeviceStatusStore
                    (可能 30s 缓存)                  (key=deviceId)
                           │                              │
                           └──────────┬───────────────────┘
                                      │
                                      ▼
                           status = storeStatus ?? device.status
```

---

## 五、修复建议

### 5.1 DeviceStatusStore 支持多 PC（P0，面向未来）

**目标**：同一 device_id 在不同 pc_client_id 下状态独立存储。

**方案 A：复合 key**

```ts
// deviceStatusStore.ts
type StatusKey = string;  // `${deviceId}:${pcClientId ?? ''}`

interface DeviceStatusEntry {
  deviceId: string;
  pcClientId?: string;
  status: DeviceStatusValue;
  updatedAt: number;
}

statuses: Map<StatusKey, DeviceStatusEntry>;

// useDeviceStatus 需传入 pcClientId
export function useDeviceStatus(deviceId: string | null, pcClientId?: string) {
  const key = deviceId ? `${deviceId}:${pcClientId ?? ''}` : '';
  return useDeviceStatusStore((s) => (key ? s.statuses.get(key)?.status : undefined));
}
```

**方案 B：嵌套结构**

```ts
statuses: Map<string, Map<string, DeviceStatusEntry>>;  // deviceId -> pcClientId -> entry
```

**影响**：所有 `useDeviceStatus(device.id)` 需改为 `useDeviceStatus(device.id, device.pc_client_id)`。

---

### 5.2 DeviceManagerPage 自驱动轮询（P0）

**目标**：不依赖 AgentDrawer 的轮询，drawer 关闭或手机式布局时状态仍更新。

**修改**（`DeviceManagerPage.tsx`）：

```ts
// 在 DeviceManagerPage 内增加
const devicesToPoll = devices.length > 0 ? devices : (deviceManagerDevices ?? []);
useDeviceStatusPolling(devicesToPoll, devicesToPoll.length > 0);
```

- 使用自身 `devices` 或回退到 `deviceManagerDevices`
- 只要 DeviceManagerPage 挂载且有设备列表就启动轮询，与 drawer 开关无关

---

### 5.3 listForUser 与 Store 一致性（P1）

**目标**：减少 listForUser 的 status 与 Store 的差异。

1. **后端**：确认 listForUser 的 status 来源与缓存策略，必要时缩短缓存或改为实时查询。
2. **前端**：保持 `status = storeStatus ?? device.status`，确保有轮询时 Store 优先。
3. **DeviceManagerPage 自驱动轮询**（见 5.2）可显著减少「无轮询」导致的滞后。

---

### 5.4 deviceManagerDevices 与 listForUser 去重（P2）

**目标**：避免多处重复调用 listForUser。

- 可引入 `useDeviceList()` 等 hook，统一拉取并写入 store，DeviceManagerPage 与 AgentDrawer 共用。
- 或保留现状，在文档中明确两处都会写入 `deviceManagerDevices`，以最后写入为准。

---

## 六、实施优先级

| 优先级 | 项 | 工作量 | 收益 |
|--------|-----|--------|------|
| P0 | DeviceManagerPage 自驱动 useDeviceStatusPolling | 小 | 解决 drawer 关闭/手机式状态滞后 |
| P0 | DeviceStatusStore 支持 (deviceId, pcClientId) 复合 key | 中 | 为多 PC 扩展做准备，避免未来覆盖 |
| P1 | 后端 listForUser status 缓存策略审查 | 小 | 降低 listForUser 与 status 不一致 |
| P2 | 统一 listForUser 调用（useDeviceList） | 中 | 减少重复请求与时序问题 |

---

## 七、附录：相关代码路径

| 模块 | 路径 |
|------|------|
| DeviceStatusStore | `novaic-app/src/stores/deviceStatusStore.ts` |
| useDeviceStatusPolling | `novaic-app/src/hooks/useDeviceStatusPolling.ts` |
| useDeviceStatus | `novaic-app/src/hooks/useDeviceStatus.ts` |
| AgentDrawer | `novaic-app/src/components/Layout/AgentDrawer.tsx` L102-103 |
| DeviceManagerPage | `novaic-app/src/components/VM/DeviceManagerPage.tsx` |
| LayoutContainer | `novaic-app/src/components/Layout/LayoutContainer.tsx` |
| listForUser | `novaic-app/src/services/api.ts` L1044 |
| devices.status | `novaic-app/src/services/api.ts` L1154 |
