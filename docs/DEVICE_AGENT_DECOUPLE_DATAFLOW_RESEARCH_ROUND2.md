# 第二轮调研（中层）：P1/P2 改造后 Device 与 Agent 解耦数据流

> 调研范围：DeviceManagerPage、DeviceFloatingPanel、useDeviceVncTarget、useAgentBinding

---

## 一、DeviceManagerPage 当前数据源（listForUser + devices.get）

### 1.1 数据源概览

| 数据项 | 来源 | 说明 |
|--------|------|------|
| **设备列表** | `api.devices.listForUser()` | 主数据源，挂载时 `load()` 调用 |
| **设备列表 fallback** | `useAppStore.deviceManagerDevices` | load 失败时使用（可能由 AgentDrawer 已加载） |
| **选中设备 ID** | `useAppStore.selectedDeviceId` | 由 AgentDrawer Devices tab 选择时写入 |
| **选中设备详情** | `devices.find()` + `api.devices.get()` | P1 已解耦 Agent，见下 |
| **设备状态** | `useDeviceStatus(selectedDevice?.id)` | 来自 DeviceStatusStore（5s 轮询） |
| **VM 子用户** | `useAppStore.selectedVmUser` | 主桌面 vs 子用户选择 |

### 1.2 设备详情获取逻辑（P1 改造后）

```ts
// DeviceManagerPage.tsx L498-513
useEffect(() => {
  if (!selectedDeviceId) {
    setSelectedDevice(null);
    return;
  }
  const fromList = devices.find(d => d.id === selectedDeviceId);
  if (fromList) {
    setSelectedDevice(fromList);
    return;
  }
  api.devices.get(selectedDeviceId).then(d => {
    if (selectedDeviceId === useAppStore.getState().selectedDeviceId) {
      setSelectedDevice(d);
    }
  }).catch(() => setSelectedDevice(null));
}, [devices, selectedDeviceId]);
```

- **优先级**：`devices.find(selectedDeviceId)` → 未找到则 `api.devices.get(selectedDeviceId)`
- **已解耦**：不再依赖 `useAgentDevice` / `agentDevice`，纯 Device 体系

### 1.3 数据流

```
api.devices.listForUser()
    → devices (local state)
    → patchState(deviceManagerDevices)

useAppStore.selectedDeviceId (来自 AgentDrawer 选择)
    → useEffect 同步 selectedDevice
    → devices.find(id) || api.devices.get(id)

useDeviceStatus(selectedDevice?.id)
    → effectiveSelectedDevice（status 覆盖）

effectiveSelectedDevice
    → DeviceVNCView | DeviceDesktopView
```

### 1.4 小结

- **DeviceManagerPage 已按 P1 完成解耦**：设备详情以 `listForUser` + `devices.get` 为主，不依赖 Agent binding
- **设备列表**：不在 DeviceManagerPage 内，在 AgentDrawer 的 Devices tab 中；DeviceManagerPage 只负责右侧主区域

---

## 二、DeviceFloatingPanel deviceMode 与 useAgentBinding 的切换逻辑

### 2.1 双数据源并行

```ts
// DeviceFloatingPanel.tsx L555-581
export function DeviceFloatingPanel({ ..., deviceMode }: DeviceFloatingPanelProps) {
  const { currentAgentId, currentAgent } = useAgent();
  const agentBinding = useAgentBinding(currentAgentId, currentAgent?.binding ?? undefined);
  const deviceVncTarget = useDeviceVncTarget(
    deviceMode?.deviceId ?? null,
    deviceMode?.subjectType ?? 'main',
    deviceMode?.subjectId
  );

  // deviceMode 优先：使用 useDeviceVncTarget
  const isDeviceMode = !!deviceMode;
  const device = isDeviceMode ? deviceVncTarget.device : agentBinding.device;
  const loading = isDeviceMode ? deviceVncTarget.isLoading : agentBinding.loading;
  const error = isDeviceMode ? deviceVncTarget.error : agentBinding.error;

  const binding = isDeviceMode ? null : agentBinding.binding;
  const subjectType = isDeviceMode ? (deviceMode?.subjectType ?? 'main') : binding?.subject_type;
  const subjectId = isDeviceMode ? (deviceMode?.subjectId ?? '') : binding?.subject_id;
  // ...
}
```

### 2.2 切换逻辑

| 条件 | 数据源 | device | binding | subjectType/subjectId |
|------|--------|--------|---------|------------------------|
| **deviceMode 存在** | `useDeviceVncTarget` | deviceVncTarget.device | 构造 syntheticBinding | 来自 deviceMode |
| **deviceMode 不存在** | `useAgentBinding` | agentBinding.device | agentBinding.binding | 来自 binding |

### 2.3 渲染条件

```ts
// L403-409
if (!isDeviceMode && !currentAgentId) return null;  // 无 Agent 且非 deviceMode 不渲染
if (loading) return null;
if (error) { console.warn(...); return null; }
if (!device) return null;
```

- **deviceMode 时**：无 Agent 也可渲染（纯 Device 流）
- **非 deviceMode 时**：必须有 `currentAgentId` 才渲染

### 2.4 syntheticBinding 构造（deviceMode 时）

```ts
// L411-422
const syntheticBinding: AgentDeviceBinding = isDeviceMode
  ? {
      agent_id: '',
      device_id: device.id,
      subject_type: subjectType ?? 'main',
      subject_id: subjectId ?? '',
      mounted_tools: {},
      created_at: '',
      updated_at: '',
      device_name: device.name,
      subject_label: subjectType === 'vm_user' ? subjectId : undefined,
    }
  : binding!;
```

### 2.5 小结

- **deviceMode**：纯 Device 流，`useDeviceVncTarget` → `devices.get(deviceId)`，不查 AgentBinding
- **非 deviceMode**：Agent 流，`useAgentBinding` → `getAgentBinding` + `devices.get(binding.device_id)`
- **DeviceFloatingPanel 当前未被任何父组件渲染**（orphaned），deviceMode 传入方暂无

---

## 三、useDeviceVncTarget 的调用方

### 3.1 调用方

| 调用方 | 文件 | 调用方式 |
|--------|------|----------|
| **DeviceFloatingPanel** | `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` L558-562 | `useDeviceVncTarget(deviceMode?.deviceId, deviceMode?.subjectType, deviceMode?.subjectId)` |

### 3.2 实际使用情况

- **唯一调用方**：DeviceFloatingPanel（仅在传入 `deviceMode` 时生效）
- **DeviceManagerPage**：未使用 useDeviceVncTarget，仍用 `listForUser` + `devices.get` 直接获取
- **useDeviceVncTarget 注释**：写「用于 DeviceManagerPage、DeviceFloatingPanel 的 deviceMode」——DeviceManagerPage 部分尚未接入

### 3.3 useDeviceVncTarget 实现

```ts
// useDeviceVncTarget.ts
export function useDeviceVncTarget(
  deviceId: string | null,
  subjectType: 'main' | 'vm_user' | 'default',
  subjectId?: string | null
): UseDeviceVncTargetResult {
  // deviceId 为 null 时返回空
  // 否则：api.devices.get(deviceId) → device + vncTarget
}
```

---

## 四、解耦后的 Device/Agent 数据流对比

### 4.1 数据流对比表

| 维度 | DeviceManagerPage | DeviceFloatingPanel (Agent 模式) | DeviceFloatingPanel (deviceMode) |
|------|-------------------|----------------------------------|----------------------------------|
| **设备列表** | listForUser | 无（单设备） | 无（单设备） |
| **设备详情** | listForUser.find + devices.get | useAgentBinding → devices.get | useDeviceVncTarget → devices.get |
| **选中/目标来源** | AppStore.selectedDeviceId | 当前 Agent 的 binding | props.deviceMode.deviceId |
| **Agent 依赖** | 无 | 强依赖，无 Agent 不渲染 | 无 |
| **binding 来源** | 无（不需要） | getAgentBinding | 构造 syntheticBinding |
| **subjectType/subjectId** | selectedVmUser（主/子用户） | binding | deviceMode |
| **状态** | useDeviceStatus | useDeviceStatus + useDeviceStatusPolling | 同上 |

### 4.2 解耦前 vs 解耦后

#### DeviceManagerPage

| 改造前 | 改造后（P1） |
|--------|--------------|
| selectedDeviceId === agentDevice.id 时用 agentDevice | 统一用 devices.find + devices.get |
| 依赖 useAgentDevice | 已移除，纯 Device 流 |

#### DeviceFloatingPanel

| 改造前 | 改造后（P1/P2） |
|--------|-----------------|
| 仅 useAgentBinding，无 Agent 不渲染 | 新增 deviceMode：useDeviceVncTarget，无 Agent 也可渲染 |
| 单一路径 | 双路径：Agent 模式 / deviceMode |

### 4.3 数据流示意图（解耦后）

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          纯 Device 流（解耦后）                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  listForUser()                    devices.get(deviceId)                          │
│       │                                  │                                       │
│       ▼                                  ▼                                       │
│  DeviceManagerPage              DeviceFloatingPanel(deviceMode)                   │
│  AgentDrawer Devices tab        useDeviceVncTarget(deviceId, subjectType, ...)   │
│       │                                  │                                       │
│       └──────── selectedDeviceId ────────┘                                       │
│                    (AppStore)                                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Agent 绑定流（未解耦）                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  getAgentBinding(agentId)  →  devices.get(binding.device_id)                      │
│       │                                  │                                       │
│       ▼                                  ▼                                       │
│  DeviceFloatingPanel(无 deviceMode)     useAgentBinding(agentId)                  │
│       │                                                                          │
│       └── 依赖 currentAgentId，无 Agent 不渲染                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 待办与建议

| 项目 | 说明 |
|------|------|
| **DeviceManagerPage 接入 useDeviceVncTarget** | 可选：当前 listForUser + devices.get 已满足需求；若需统一封装可引入 useDeviceVncTarget 或 useDevice(deviceId) |
| **DeviceFloatingPanel 接入** | 组件已实现 deviceMode，但未被渲染；需确定父组件及 deviceMode 传入场景 |
| **useDeviceVncTarget 注释** | 建议更新：移除「用于 DeviceManagerPage」，或注明「DeviceManagerPage 可选接入」 |

---

## 五、附录：关键文件路径

| 文件 | 路径 |
|------|------|
| DeviceManagerPage | `novaic-app/src/components/VM/DeviceManagerPage.tsx` |
| DeviceFloatingPanel | `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` |
| useDeviceVncTarget | `novaic-app/src/hooks/useDeviceVncTarget.ts` |
| useAgentBinding | `novaic-app/src/hooks/useAgentBinding.ts` |
| useAgent | `novaic-app/src/components/hooks/useAgent.ts` |
| useDeviceStatus | `novaic-app/src/hooks/useDeviceStatus.ts` |
| AgentDrawer | `novaic-app/src/components/Layout/AgentDrawer.tsx` |
