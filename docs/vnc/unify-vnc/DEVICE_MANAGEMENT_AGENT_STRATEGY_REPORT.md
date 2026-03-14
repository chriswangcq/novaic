# Device 管理流程中 Agent 策略研究报告

**研究范围**：DeviceManagerPage、DeviceFloatingPanel、DeviceDrawer（AgentDrawer 的 Devices 区）、Agent 依赖与设计意图  
**日期**：2025-03-12

---

## 一、Device 管理流程概览

### 1.1 入口组件与数据流

| 组件 | 数据来源 | 渲染位置 | 状态 |
|------|----------|----------|------|
| **DeviceManagerPage** | `api.devices.listForUser()` + store | LayoutContainer Main 区（activeView=devices 时） | ✅ 已接入 |
| **AgentDrawer（Devices tab）** | `api.devices.listForUser()` + store | 左侧抽屉，与 Agents 并列 | ✅ 已接入 |
| **DeviceFloatingPanel** | `useAgentBinding(currentAgentId)` | 设计为 ChatPanel 内右上角浮层 | ⚠️ 已实现但未渲染 |
| **DeviceManagerModal** | `api.devices.listForUser()` | 模态弹窗 | ✅ 已接入 |

### 1.2 设备选择流程

```
用户点击 AgentDrawer → Devices tab
    ↓
AgentDrawer 展示 api.devices.listForUser() 的设备列表
    ↓
用户点击某设备 → openDevice(deviceId) → setSelectedDeviceId(id) 写入 store
    ↓
DeviceManagerPage 读取 selectedDeviceId，从 devices 或 agentDevice 解析 effectiveSelectedDevice
    ↓
渲染 DeviceVNCView（main）或 DeviceDesktopView（vm_user）
```

### 1.3 共享状态（store）

| 字段 | 用途 |
|------|------|
| `selectedDeviceId` | AgentDrawer 与 DeviceManagerPage 共享，表示当前选中的设备 |
| `selectedVmUser` | 子用户桌面选择（main vs vm_user） |
| `deviceManagerDevices` | listForUser 结果缓存，DeviceManagerPage 加载失败时从 AgentDrawer 回退 |

---

## 二、Agent 依赖点

### 2.1 依赖矩阵

| 组件 | currentAgentId | useAgent | useAgentDevice | useAgentBinding |
|------|----------------|----------|----------------|-----------------|
| **DeviceManagerPage** | ✓ | ✓ | ✓ | - |
| **AgentDrawer** | ✓ | ✓ | ✓ | - |
| **DeviceFloatingPanel** | ✓ | ✓ | - | ✓ |
| **VisualPanel** | ✓ | ✓ | ✓ | - |
| **DeviceManagerModal** | - | - | - | - |

### 2.2 各组件 Agent 依赖详情

#### DeviceManagerPage

```tsx
// novaic-app/src/components/VM/DeviceManagerPage.tsx:627-629
const { currentAgentId } = useAgent();
const { device: agentDevice } = useAgentDevice(currentAgentId ?? null);
```

- **用途**：当 `selectedDeviceId === agentDevice?.id` 时，优先使用 `agentDevice` 作为 `selectedDevice` 的数据源。
- **原因**：`agentDevice` 来自 `getAgentBinding` + `devices.get`，比 `listForUser` 的列表项更新（避免 30s 缓存滞后）。注释 P1-11 明确说明。

#### AgentDrawer

```tsx
// novaic-app/src/components/Layout/AgentDrawer.tsx:51, 106
const { agents, currentAgentId, loadAgents } = useAgent();
const { device: agentDevice } = useAgentDevice(primaryTab === 'devices' ? currentAgentId : null);
```

- **用途**：
  1. 设备列表项高亮：`isAgentDevice={agentDevice?.id === device.id}`，标识「当前 Agent 绑定的设备」。
  2. 仅在 `primaryTab === 'devices'` 时请求 `useAgentDevice`，减少无关请求。

#### DeviceFloatingPanel

```tsx
// novaic-app/src/components/Layout/DeviceFloatingPanel.tsx:537-539
const { currentAgentId, currentAgent } = useAgent();
const { binding, device, loading, error } = useAgentBinding(currentAgentId, currentAgent?.binding ?? undefined);
```

- **用途**：**完全依赖 Agent 绑定**。无 `currentAgentId` 或 `!binding` 时 `return null`。只展示当前 Agent 绑定的那一个设备，按 `subject_type` 渲染 main / vm_user / android。

#### VisualPanel

```tsx
// novaic-app/src/components/Visual/VisualPanel.tsx:49-50
const { currentAgentId } = useAgent();
const { device } = useAgentDevice(currentAgentId);
```

- **用途**：根据当前 Agent 绑定的设备类型（linux/android）切换 VNC / Scrcpy 视图。

---

## 三、设计意图分析

### 3.1 Device 是用户级还是 Agent 级资源？

**结论：Device 是用户级资源，Agent 通过 Binding 引用设备。**

| 维度 | 说明 |
|------|------|
| **归属** | `devices` 表主键 `device_id` 代表逻辑设备配置（Linux VM / Android AVD），归属于 **User**。 |
| **API** | `api.devices.listForUser()` 返回用户全部设备，无 agentId 参数。 |
| **废弃** | `api.devices.list(agentId)` 已废弃，Agent 不再拥有设备列表，仅通过 `getAgentBinding` 引用单个设备。 |

引用自 `docs/unify-vnc/02-expert-design.md`：

> **logical_device_id**（简称 `device_id`）：`devices` 表主键，代表一个逻辑设备配置（Linux VM 或 Android AVD），归属于 User。这是业务层面的「设备」概念，前端 AgentDrawer、DeviceFloatingPanel 等展示的都是它。

### 3.2 Agent-Device 绑定的业务含义

**AgentDeviceBinding** 表示「该 Agent 操作哪个设备的哪个桌面」：

```ts
// api.ts
interface AgentDeviceBinding {
  agent_id: string;
  device_id: string;
  subject_type: 'main' | 'vm_user' | 'default';  // 主桌面 / 子用户桌面 / Android 默认
  subject_id: string;   // vm_user 时为 username
  mounted_tools: MountedToolsByCategory;
  // ...
}
```

| subject_type | 含义 | VNC 目标 |
|--------------|------|----------|
| `main` | VM 主桌面 | `device_id` |
| `vm_user` | 子用户桌面 | `device_id:username` |
| `default` | Android 默认 | Scrcpy |

**业务语义**：一个 Agent 绑定一个设备的一个 subject，用于：
1. Agent 执行工具时操作的目标桌面；
2. VisualPanel / DeviceFloatingPanel 展示「当前 Agent 的工作环境」；
3. AgentDrawer 中高亮「该 Agent 正在使用的设备」。

### 3.3 为何 Device 管理需要 Agent？

| 场景 | 原因 |
|------|------|
| **AgentDrawer 设备列表** | 抽屉同时展示 Agents 与 Devices，需标识「当前 Agent 绑定的是哪台设备」，引导用户理解 Agent-Device 关系。 |
| **DeviceManagerPage 数据新鲜度** | 当选中设备 = Agent 绑定设备时，用 `useAgentDevice` 的 `devices.get` 结果替代 `listForUser` 列表项，避免缓存滞后。 |
| **DeviceFloatingPanel** | 设计为「Agent 上下文的设备预览」——只展示当前 Agent 绑定的设备，作为 Chat 旁的浮动窗口，无需用户再选设备。 |
| **VisualPanel** | Chat 主区的 VM/Scrcpy 视图，必须知道当前 Agent 绑定的是 Linux 还是 Android，才能正确渲染。 |

### 3.4 数据源对比

| 数据源 | 范围 | 使用场景 |
|--------|------|----------|
| `listForUser()` | 用户全部设备 | DeviceManagerPage、AgentDrawer、DeviceManagerModal 的设备列表 |
| `getAgentBinding` + `devices.get` | 当前 Agent 绑定的单设备 | DeviceFloatingPanel、DeviceManagerPage 的 agentDevice 回退、VisualPanel、AgentDrawer 的 isAgentDevice |

---

## 四、总结

1. **Device 归属**：Device 是用户级资源，`listForUser` 是设备列表的主数据源。
2. **Agent 角色**：Agent 通过 `AgentDeviceBinding` 引用单个设备的单个 subject，表示「该 Agent 操作哪台设备的哪个桌面」。
3. **Agent 在 Device 管理中的用途**：
   - **标识**：在设备列表中高亮当前 Agent 绑定的设备；
   - **数据新鲜度**：选中设备 = 绑定设备时，用 `getAgentBinding` + `devices.get` 获取更新数据；
   - **上下文预览**：DeviceFloatingPanel 仅展示当前 Agent 绑定设备，作为 Chat 旁的浮动预览。
4. **DeviceFloatingPanel 状态**：组件已实现且完整依赖 `useAgentBinding`，但当前未被任何父组件渲染，处于「已实现未接入」状态。
