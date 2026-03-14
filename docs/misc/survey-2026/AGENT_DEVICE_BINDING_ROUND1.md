# NovAIC Agent-Device Binding 调研（浅层）

> 调研范围：api.ts getAgentBinding、useAgentDevice、useAgentBinding、DeviceFloatingPanel、AgentDesktopView、VisualPanel、SettingsModal

---

## 1. 数据流：agentId → getAgentBinding → devices.get → VncTarget

### 1.1 核心链路

```
agentId
   │
   ▼
┌─────────────────────┐     GET /api/agents/{agentId}/binding
│ api.getAgentBinding │ ─────────────────────────────────────► AgentDeviceBinding
└─────────────────────┘                                              │
   │                                                                  │ device_id
   │                                                                  │ subject_type
   │                                                                  │ subject_id
   ▼                                                                  ▼
┌─────────────────────┐     GET /api/devices/{device_id}      ┌──────────────┐
│ api.devices.get     │ ◄─────────────────────────────────────│   Device     │
└─────────────────────┘                                       │ pc_client_id │
   │                                                             └──────────────┘
   │                                                                  │
   ▼                                                                  │
┌─────────────────────┐     binding + device                         │
│ bindingToVncTarget  │ ─────────────────────────────────────────► VncTarget
└─────────────────────┘                                              │
   │                                                                  │ resourceId
   │                                                                  │ pcClientId
   ▼                                                                  ▼
┌─────────────────────┐     createVncTransport(target)         VNC 连接
│ VncProxy / VNC      │ ◄────────────────────────────────────
└─────────────────────┘
```

### 1.2 API 定义

| API | 文件 | 说明 |
|-----|------|------|
| `api.getAgentBinding(agentId)` | `novaic-app/src/services/api.ts` L506-510 | `GET /api/agents/{agentId}/binding` → `AgentDeviceBinding \| null` |
| `api.devices.get(deviceId)` | `novaic-app/src/services/api.ts` L1075-1077 | `GET /api/devices/{deviceId}` → `Device` |

### 1.3 Hooks 封装

| Hook | 文件 | 数据流 | 返回 |
|------|------|--------|------|
| **useAgentDevice** | `novaic-app/src/hooks/useAgentDevice.ts` | `getAgentBinding` → `devices.get`（带 deviceCache 30s TTL）→ `bindingToVncTarget` | `{ binding, device, vncTarget, isLoading, error, refetch }` |
| **useAgentBinding** | `novaic-app/src/hooks/useAgentBinding.ts` | `initialBinding ?? getAgentBinding` → `devices.get` | `{ binding, device, loading, error, refetch }` |

- **useAgentDevice**：返回 `vncTarget`，供 VNC 组件直接使用；内部有 `deviceCache` 减少重复请求。
- **useAgentBinding**：支持 `initialBinding`（来自 Agent 列表的 `currentAgent?.binding`），可跳过 `getAgentBinding` 请求；不返回 `vncTarget`。

### 1.4 VncTarget 派生

`bindingToVncTarget`（useAgentDevice.ts L36-53）：

| subject_type | resourceId | deviceId | username |
|--------------|------------|----------|----------|
| main / default | `device_id` | `device_id` | - |
| vm_user | `${device_id}:${subject_id}` | `device_id` | `subject_id` |

`pcClientId` 来自 `device.pc_client_id`。

---

## 2. 依赖组件

### 2.1 AgentDesktopView

**文件**：`novaic-app/src/components/Visual/AgentDesktopView.tsx`

- **数据源**：`useAgentDevice(agentId)` → `vncTarget`
- **用途**：Agent 绑定设备的主桌面 VNC 视图
- **流程**：`useAgentDevice` → `createVncTransport(vncTarget)` → `useVnc` → `VncCanvas`
- **渲染条件**：`agentId` 存在、无 error、`vncTarget` 存在

### 2.2 VisualPanel

**文件**：`novaic-app/src/components/Visual/VisualPanel.tsx`

- **数据源**：`useAgentDevice(currentAgentId)` → `device`
- **用途**：根据设备类型（`hasLinux` / `hasAndroid`）决定展示 Linux 或 Android 视图；渲染 `AgentDesktopView` 或 `ScrcpyView`
- **关键逻辑**：`device?.type === 'linux'` / `device?.type === 'android'`，替代已废弃的 `agent.devices`

### 2.3 DeviceFloatingPanel

**文件**：`novaic-app/src/components/Layout/DeviceFloatingPanel.tsx`

- **数据源**：
  - **Agent 模式**：`useAgentBinding(currentAgentId, currentAgent?.binding)` → `binding` + `device`
  - **deviceMode**：`useDeviceVncTarget(deviceMode.deviceId, subjectType, subjectId)` → `device` + `vncTarget`
- **用途**：设备浮层（预览/展开），按 subject_type 渲染 main → VNCViewShared、vm_user → DeviceDesktopView、default → ScrcpyView
- **渲染位置**：`ChatPanel` 内 `<DeviceFloatingPanel compact />`（未传 deviceMode，即 Agent 模式）

### 2.4 SettingsModal

**文件**：`novaic-app/src/components/Settings/SettingsModal.tsx`

- **数据源**：`api.getAgentBinding(selectedAgentId)`、`api.setAgentBinding(selectedAgentId, {...})`
- **用途**：设置 → Agents  tab 中配置 Agent 的设备绑定（选择设备、subject）
- **流程**：loadData 时并行 `api.getAgentBinding`；保存时 `api.setAgentBinding` 更新 binding

---

## 3. Agent 模式 vs deviceMode 的区别

### 3.1 对比表

| 维度 | Agent 模式 | deviceMode |
|------|------------|------------|
| **触发条件** | `currentAgentId` 存在，且未传 `deviceMode` | 传入 `deviceMode: { deviceId, subjectType?, subjectId? }` |
| **数据源** | `useAgentBinding(agentId, initialBinding)` | `useDeviceVncTarget(deviceId, subjectType, subjectId)` |
| **API 调用** | `getAgentBinding` + `devices.get(binding.device_id)` | 仅 `devices.get(deviceId)` |
| **binding 来源** | `getAgentBinding` 或 Agent 列表的 `binding` | 无；构造 `syntheticBinding` 供 UI 展示 |
| **依赖 Agent** | 强依赖，无 Agent 不渲染 | 不依赖 Agent |
| **典型场景** | Chat 旁展示当前 Agent 绑定设备 | 脱离 Agent 直接查看指定设备（如 DeviceManagerPage 点击设备） |

### 3.2 DeviceFloatingPanel 切换逻辑

```typescript
// DeviceFloatingPanel.tsx L555-581
const isDeviceMode = !!deviceMode;
const device = isDeviceMode ? deviceVncTarget.device : agentBinding.device;
const loading = isDeviceMode ? deviceVncTarget.isLoading : agentBinding.loading;
const error = isDeviceMode ? deviceVncTarget.error : agentBinding.error;
const binding = isDeviceMode ? null : agentBinding.binding;

// 无 deviceMode 且无 currentAgentId 时直接 return null
if (!isDeviceMode && !currentAgentId) return null;
```

- **Agent 模式**：`DeviceFloatingPanel` 在 ChatPanel 中渲染，不传 `deviceMode`，依赖 `currentAgentId`。
- **deviceMode**：当前 `DeviceFloatingPanel` 的调用方（如 ChatPanel）未传入 `deviceMode`；`useDeviceVncTarget` 设计用于 DeviceManagerPage 等场景，但 DeviceManagerPage 尚未接入 DeviceFloatingPanel 的 deviceMode。

### 3.3 小结

- **Agent 模式**：以 Agent 为中心，通过 binding 获取设备，适用于 Chat 主流程。
- **deviceMode**：以 Device 为中心，直接指定 deviceId + subject，适用于设备管理、脱离 Agent 的预览场景。
