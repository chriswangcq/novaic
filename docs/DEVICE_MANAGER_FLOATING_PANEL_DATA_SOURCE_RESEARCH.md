# DeviceManagerPage 与 DeviceFloatingPanel 数据源调研

> 为 P1 改造准备，目标目录：`novaic-app/src`

---

## 一、DeviceManagerPage

### 1.1 数据源概览

| 数据项 | 来源 | 说明 |
|--------|------|------|
| **设备列表** | `api.devices.listForUser()` | 主数据源，挂载时 load() 调用 |
| **设备列表 fallback** | `useAppStore.deviceManagerDevices` | load 失败时使用（可能由 AgentDrawer 已加载） |
| **选中设备 ID** | `useAppStore.selectedDeviceId` | 由 AgentDrawer Devices tab 选择时写入 |
| **选中设备详情** | `useAgentDevice` + `devices.find()` | 见下 |
| **设备状态** | `useDeviceStatus(deviceId)` | 来自 DeviceStatusStore（5s 轮询） |
| **VM 子用户** | `useAppStore.selectedVmUser` | 主桌面 vs 子用户选择 |

### 1.2 设备详情获取逻辑（P1-11）

```ts
// 当 selectedDeviceId 对应当前 Agent 绑定设备时，优先用 useAgentDevice 的 device（devices.get 数据源）
useEffect(() => {
  if (!selectedDeviceId) {
    setSelectedDevice(null);
    return;
  }
  const fromAgent = agentDevice?.id === selectedDeviceId ? agentDevice : null;
  const next = fromAgent ?? devices.find(d => d.id === selectedDeviceId) ?? null;
  setSelectedDevice(next);
}, [devices, selectedDeviceId, agentDevice]);
```

- **agentDevice**：`useAgentDevice(currentAgentId)` → `getAgentBinding` + `devices.get(device_id)`
- **devices**：`api.devices.listForUser()` 返回的列表
- **优先级**：选中设备 = 当前 Agent 绑定设备时，用 `agentDevice`（get 数据源）；否则用 `devices.find()`

### 1.3 Props

```ts
interface DeviceManagerPageProps {
  isPageMode?: boolean;   // 窄屏模式，显示返回按钮
  onBackToChat?: () => void;
}
```

### 1.4 Hooks 依赖

| Hook | 用途 |
|------|------|
| `useAgent()` | `currentAgentId` |
| `useAgentDevice(currentAgentId)` | `agentDevice`，用于选中设备为 Agent 绑定设备时的详情 |
| `useAppStore` | `selectedDeviceId`, `selectedVmUser`, `deviceManagerDevices`, `addLinuxDeviceModalOpen`, `addAndroidDeviceModalOpen`, `addVmSubuserDeviceId`, `patchState` |
| `useDeviceStatus(selectedDevice?.id)` | 选中设备实时状态（覆盖 listForUser 的 30s 缓存） |
| `useState` | `devices`, `loading`, `error`, `selectedDevice`, `selectedVmUser` |

### 1.5 数据流

```
api.devices.listForUser()
    → devices (local state)
    → patchState(deviceManagerDevices)

useAppStore.selectedDeviceId (来自 AgentDrawer 选择)
    → useEffect 同步 selectedDevice
    → 若 selectedDeviceId === agentDevice.id：用 agentDevice（devices.get）
    → 否则：devices.find(id)

useDeviceStatus(selectedDevice?.id)
    → effectiveSelectedDevice（status 覆盖）

effectiveSelectedDevice
    → DeviceVNCView | DeviceDesktopView
```

### 1.6 布局说明

- **渲染位置**：`LayoutContainer` 中，当 `activeView === 'devices'` 时
- **设备列表**：不在 DeviceManagerPage 内，在 **AgentDrawer** 的 Devices tab 中
- **DeviceManagerPage**：只负责右侧主区域（选中设备的 VNC/Desktop 视图或空状态）

---

## 二、DeviceFloatingPanel

### 2.1 数据源概览

| 数据项 | 来源 | 说明 |
|--------|------|------|
| **Binding** | `useAgentBinding(currentAgentId, currentAgent?.binding)` | getAgentBinding 或 agent 列表中的 binding |
| **Device** | `api.devices.get(binding.device_id)` | 由 useAgentBinding 内部调用 |
| **displayNum** | `api.vmUsers.list(device.id)` | vm_user 时解析 subject_id 对应 display_num |
| **设备状态** | `useDeviceStatus(device?.id)` | DeviceStatusStore |
| **轮询** | `useDeviceStatusPolling(device ? [device] : [], !!device)` | 驱动 DeviceStatusStore 更新 |

### 2.2 是否依赖 useAgentBinding / useAgentDevice

- **依赖**：`useAgentBinding`（不是 useAgentDevice）
- **区别**：useAgentBinding 返回 `binding` + `device`；useAgentDevice 返回 `binding` + `device` + `vncTarget`
- **数据流**：`getAgentBinding(agentId)` → `devices.get(binding.device_id)`

### 2.3 无 Agent 时是否渲染

```ts
if (!currentAgentId) return null;
if (loading) return null;
if (error) {
  console.warn('[DeviceFloatingPanel] Error:', error);
  return null;
}
if (!binding || !device) return null;
```

- **无 currentAgentId**：不渲染
- **loading**：不渲染
- **error**：不渲染
- **无 binding 或 device**：不渲染

结论：**完全依赖 Agent**，无 Agent 或绑定设备时不会渲染。

### 2.4 Props

```ts
interface DeviceFloatingPanelProps {
  inline?: boolean;    // 内联模式，嵌入布局
  placement?: 'top' | 'bottom';  // 内联时的位置
  compact?: boolean;   // 紧凑浮层模式
}
```

### 2.5 Hooks 依赖

| Hook | 用途 |
|------|------|
| `useAgent()` | `currentAgentId`, `currentAgent`（含 `binding` 预填充） |
| `useAgentBinding(currentAgentId, currentAgent?.binding)` | `binding`, `device`, `loading`, `error` |
| `useDeviceStatusPolling(device ? [device] : [], !!device)` | 驱动 DeviceStatusStore |
| `useDeviceStatus(device?.id)` | `isRunning` |
| `useState` | `vmUserDisplayNum` |
| `api.vmUsers.list(device.id)` | vm_user 的 displayNum |

### 2.6 数据流

```
useAgent() → currentAgentId, currentAgent?.binding

useAgentBinding(currentAgentId, currentAgent?.binding)
    → getAgentBinding(agentId) [或直接用 initialBinding]
    → devices.get(binding.device_id)
    → binding, device

useDeviceStatusPolling([device])
    → DeviceStatusStore 更新

useDeviceStatus(device?.id)
    → isRunning

vm_user 时：api.vmUsers.list(device.id) → displayNum

SubjectCardInfo { device, binding, deviceInfo }
    → DeviceCard (main → VNCViewShared, vm_user → DeviceDesktopView, android → ScrcpyView)
    → StoppedDeviceChip（非 running 时）
```

---

## 三、数据流对比

| 维度 | DeviceManagerPage | DeviceFloatingPanel |
|------|-------------------|---------------------|
| **设备列表** | listForUser | 无（单设备） |
| **设备详情** | listForUser.find + useAgentDevice（选中=绑定设备时） | useAgentBinding → devices.get |
| **选中来源** | AppStore.selectedDeviceId（AgentDrawer 选择） | 当前 Agent 的 binding |
| **Agent 依赖** | 仅用于 agentDevice 优化选中设备详情 | 强依赖，无 Agent 不渲染 |
| **状态** | useDeviceStatus | useDeviceStatus + useDeviceStatusPolling |

---

## 四、P1 改造点清单

### 4.1 DeviceManagerPage

| # | 改造点 | 说明 |
|---|--------|------|
| 1 | **解耦 Agent 依赖** | 当前 selectedDevice 在「选中=Agent 绑定设备」时用 agentDevice。P1 若设备与 Agent 解耦，需统一用 listForUser + devices.get，或新 hook |
| 2 | **设备列表数据源** | 保持 listForUser 为主，但需确认与 AgentDrawer 的 deviceManagerDevices 同步策略 |
| 3 | **selectedDeviceId 来源** | 当前由 AgentDrawer 设置。若 Devices 入口与 Agent 解耦，需新选中逻辑（如独立 Devices 页） |
| 4 | **DeviceListPanel 使用** | DeviceListPanel 已导出但未在 DeviceManagerPage 内使用，设备列表在 AgentDrawer。P1 是否需在 DeviceManagerPage 内集成左侧列表？ |
| 5 | **useDeviceStatus** | 已用 DeviceStatusStore，保持即可 |

### 4.2 DeviceFloatingPanel

| # | 改造点 | 说明 |
|---|--------|------|
| 1 | **无 Agent 时渲染** | 当前无 Agent 直接 return null。P1 若支持「无 Agent 的设备预览」，需新数据源（如 selectedDeviceId + devices.get） |
| 2 | **数据源切换** | 从 useAgentBinding 改为支持「设备 ID 模式」：当有 deviceId 时用 devices.get，无 Agent 时也能显示 |
| 3 | **binding 语义** | vm_user 的 subject_id、displayNum 来自 binding。无 Agent 时需从 selectedVmUser 等 store 推导 |
| 4 | **useDeviceStatusPolling** | 当前传 `[device]`，device 来自 binding。无 Agent 时需从 store 或 props 传入 device |

### 4.3 通用

| # | 改造点 | 说明 |
|---|--------|------|
| 1 | **统一设备详情获取** | 建议统一封装 `useDevice(deviceId)`：devices.get + 缓存，供两组件复用 |
| 2 | **DeviceStatusStore** | 两组件已用，保持轮询与订阅一致 |
| 3 | **selectedDeviceId / selectedVmUser** | AppStore 共享，需明确：无 Agent 时由谁设置、何时清除 |

---

## 五、附录：关键文件路径

| 文件 | 路径 |
|------|------|
| DeviceManagerPage | `novaic-app/src/components/VM/DeviceManagerPage.tsx` |
| DeviceFloatingPanel | `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` |
| useAgentDevice | `novaic-app/src/hooks/useAgentDevice.ts` |
| useAgentBinding | `novaic-app/src/hooks/useAgentBinding.ts` |
| useAgent | `novaic-app/src/components/hooks/useAgent.ts` |
| useDeviceStatus | `novaic-app/src/hooks/useDeviceStatus.ts` |
| useDeviceStatusPolling | `novaic-app/src/hooks/useDeviceStatusPolling.ts` |
| AppStore | `novaic-app/src/application/store.ts` |
| AgentDrawer | `novaic-app/src/components/Layout/AgentDrawer.tsx` |
| LayoutContainer | `novaic-app/src/components/Layout/LayoutContainer.tsx` |
