# DeviceFloatingPanel 接入现状与 deviceMode 调研（中层）

> 基于 R1 输出，深入分析 DeviceFloatingPanel 渲染位置、compact/inline 模式、deviceMode 传入方、Agent/deviceMode 切换逻辑、与 DeviceManagerPage 的协作关系。

**输入**：`AGENT_DEVICE_BINDING_ROUND1.md`、`DeviceFloatingPanel.tsx`、`ChatPanel.tsx`、`LayoutContainer.tsx`、`AgentDrawer.tsx`

---

## 1. DeviceFloatingPanel 当前渲染位置

### 1.1 调用关系

| 组件 | 是否直接渲染 DeviceFloatingPanel | 说明 |
|------|----------------------------------|------|
| **ChatPanel** | ✅ 是 | 唯一直接调用方：`<DeviceFloatingPanel compact />`（L59-61） |
| **LayoutContainer** | ❌ 否 | 通过 `ChatPanel` 间接包含：`LayoutContainer → ChatPanel → DeviceFloatingPanel` |
| **AgentDrawer** | ❌ 否 | 不渲染 DeviceFloatingPanel；仅负责 Agent 列表、Devices 列表、Settings 嵌入 |

### 1.2 渲染路径

```
LayoutContainer
   │
   ├─ activeView === 'chat' 时
   │     └─ ChatPanel
   │           └─ DeviceFloatingPanel compact  ← 唯一挂载点
   │
   └─ activeView === 'devices' 时
         └─ DeviceManagerPage  ← 不包含 DeviceFloatingPanel
```

### 1.3 结论

- **DeviceFloatingPanel 仅在 ChatPanel 内渲染**，且仅在 `activeView === 'chat'` 时可见。
- 当用户切换到 Devices 视图（DeviceManagerPage）时，**DeviceFloatingPanel 不会出现在该页面**。
- AgentDrawer 与 DeviceFloatingPanel 无直接父子关系；Drawer 负责选择 Agent/设备，主区域由 LayoutContainer 决定渲染 ChatPanel 或 DeviceManagerPage。

---

## 2. compact 模式与 inline 模式的区别

### 2.1 Props 定义

```typescript
// DeviceFloatingPanel.tsx L407-418
interface DeviceFloatingPanelProps {
  inline?: boolean;      // 内联模式：嵌入布局中（非浮动）
  placement?: 'top' | 'bottom';  // 内联时的位置
  compact?: boolean;     // 紧凑浮层模式：不占布局空间，纯浮动 overlay
  deviceMode?: DeviceModeConfig;  // 设备模式
}
```

### 2.2 compact 模式（当前 ChatPanel 使用）

| 维度 | 行为 |
|------|------|
| **布局** | `spacerWidth = 0`，不渲染 spacer div，不挤占主内容区宽度 |
| **定位** | 使用 `stackTop`（100px）从顶部向下堆叠；`topOffset` 由 `runningOffsets`/`stoppedOffsets` 计算 |
| **DOM** | `DeviceCard`、`StoppedDeviceChip` 使用 `position: fixed`，浮在视口右上角 |
| **遮罩** | 展开时遮罩右边界为 `right: 0`（无 spacer 偏移） |
| **典型场景** | Chat 旁展示 Agent 绑定设备，不挤压消息区 |

### 2.3 inline 模式（当前未使用）

| 维度 | 行为 |
|------|------|
| **布局** | 嵌入父容器，`inline && !compact` 时渲染为 `shrink-0 w-auto h-[96px]` 的 div |
| **定位** | `DeviceCard` 使用 `relative`，`width: 100%`、`height: 100%`；非 fixed |
| **placement** | `top` → `justify-center`；`bottom` → `justify-end border-l` |
| **spacerWidth** | `inline || compact` 时均为 0 |
| **典型场景** | 设备预览嵌入侧边栏或输入框旁，占固定布局空间 |

### 2.4 对比小结

| 模式 | 占布局空间 | 定位方式 | 当前使用 |
|------|------------|----------|----------|
| **compact** | 否 | fixed，右上角堆叠 | ✅ ChatPanel |
| **inline** | 是 | relative，嵌入容器 | ❌ 无 |
| **非 compact 非 inline** | 是（spacer） | fixed，右侧留 spacer | ❌ 无 |

---

## 3. deviceMode 传入方

### 3.1 DeviceModeConfig 接口

```typescript
// DeviceFloatingPanel.tsx L402-406
export interface DeviceModeConfig {
  deviceId: string;
  subjectType: 'main' | 'vm_user' | 'default';
  subjectId?: string;
}
```

### 3.2 当前传入方

| 调用方 | isDeviceMode | currentDeviceId | subjectType | subjectId | 说明 |
|--------|--------------|-----------------|-------------|-----------|------|
| **ChatPanel** | ❌ 未传 | - | - | - | 仅传 `compact`，无 `deviceMode` |
| **LayoutContainer** | - | - | - | - | 不直接渲染 DeviceFloatingPanel |
| **AgentDrawer** | - | - | - | - | 不渲染 DeviceFloatingPanel |
| **DeviceManagerPage** | - | - | - | - | 不渲染 DeviceFloatingPanel |

### 3.3 结论

- **当前没有任何调用方传入 `deviceMode`**。
- DeviceFloatingPanel 的 deviceMode 能力已实现（`useDeviceVncTarget`、`syntheticBinding`、`onStartVm` 等），但**未被使用**。
- 潜在传入方：DeviceManagerPage 在用户选中设备后，可将 `deviceMode={{ deviceId, subjectType, subjectId }}` 传给 DeviceFloatingPanel，实现设备浮层预览；当前未接入。

### 3.4 deviceMode 下的数据流

当 `deviceMode` 被传入时：

| 数据 | 来源 |
|------|------|
| `isDeviceMode` | `!!deviceMode` |
| `device` | `useDeviceVncTarget(deviceMode.deviceId, subjectType, subjectId).device` |
| `subjectType` | `deviceMode.subjectType ?? 'main'` |
| `subjectId` | `deviceMode.subjectId ?? ''` |
| `binding` | 构造 `syntheticBinding`（无 `agent_id`） |
| `agentId` | 不传（`DeviceCard` 的 `agentId` 为 `undefined`） |
| `onStartVm` | `() => api.devices.start(...)`（deviceMode 时替代 vmService） |

---

## 4. Agent 模式与 deviceMode 的切换逻辑

### 4.1 判定逻辑

```typescript
// DeviceFloatingPanel.tsx L424-432
const isDeviceMode = !!deviceMode;
const device = isDeviceMode ? deviceVncTarget.device : agentBinding.device;
const loading = isDeviceMode ? deviceVncTarget.isLoading : agentBinding.loading;
const error = isDeviceMode ? deviceVncTarget.error : agentBinding.error;
const binding = isDeviceMode ? null : agentBinding.binding;
const subjectType = isDeviceMode ? (deviceMode?.subjectType ?? 'main') : binding?.subject_type;
const subjectId = isDeviceMode ? (deviceMode?.subjectId ?? '') : binding?.subject_id;

// L439
if (!isDeviceMode && !currentAgentId) return null;
```

### 4.2 切换规则

| 条件 | 模式 | 数据源 | 渲染条件 |
|------|------|--------|----------|
| `deviceMode` 有值 | **deviceMode** | `useDeviceVncTarget` | `device` 存在、无 error |
| `deviceMode` 无值 且 `currentAgentId` 有值 | **Agent 模式** | `useAgentBinding` | `device` 存在、无 error |
| `deviceMode` 无值 且 `currentAgentId` 无值 | - | - | **return null**，不渲染 |

### 4.3 数据源对比

| 维度 | Agent 模式 | deviceMode |
|------|------------|------------|
| **Hook** | `useAgentBinding(currentAgentId, currentAgent?.binding)` | `useDeviceVncTarget(deviceId, subjectType, subjectId)` |
| **API** | `getAgentBinding` + `devices.get(binding.device_id)` | 仅 `devices.get(deviceId)` |
| **binding** | 来自 API 或 Agent 列表 | 构造 `syntheticBinding` |
| **依赖 Agent** | 强依赖，无 Agent 不渲染 | 不依赖 Agent |
| **VNC 启动** | vmService（Agent 体系） | `api.devices.start`（直接调用） |

### 4.4 当前实际行为

- 所有调用方均未传 `deviceMode` → **始终为 Agent 模式**。
- 依赖 `currentAgentId`：无当前 Agent 时，DeviceFloatingPanel 不渲染。

---

## 5. 与 DeviceManagerPage 的协作关系

### 5.1 当前架构

```
AgentDrawer (Devices tab)
   │
   │  selectedDeviceId, selectedVmUser (useAppStore)
   │  openDevice(deviceId) → setSelectedDeviceId, onOpenDevices()
   ▼
LayoutContainer
   │  activeView === 'devices' → onNarrowPageChange('devices')
   ▼
DeviceManagerPage
   │  读取 selectedDeviceId, selectedVmUser
   │  渲染 DeviceVNCView / DeviceDesktopView（全屏主区域）
   └─ 不渲染 DeviceFloatingPanel
```

### 5.2 数据流对比

| 维度 | ChatPanel + DeviceFloatingPanel | DeviceManagerPage |
|------|--------------------------------|-------------------|
| **设备选择来源** | `currentAgentId` → `useAgentBinding` → binding.device_id | `selectedDeviceId`（store） |
| **subject 选择** | binding.subject_type / subject_id | `selectedVmUser`（store，null=main） |
| **展示组件** | DeviceFloatingPanel → VNCViewShared / DeviceDesktopView / ScrcpyView | DeviceVNCView / DeviceDesktopView |
| **布局** | 浮层（compact）或内联 | 左侧列表 + 右侧全屏视图 |

### 5.3 协作现状

- **无直接协作**：DeviceManagerPage 与 DeviceFloatingPanel 为两条独立 UI 路径。
- **共享状态**：`selectedDeviceId`、`selectedVmUser` 由 AgentDrawer 写入，DeviceManagerPage 读取；DeviceFloatingPanel 不读取这些状态。
- **潜在协作**：若在 DeviceManagerPage 中嵌入 DeviceFloatingPanel（传入 `deviceMode`），可实现：
  - 设备列表 + 浮层预览并存；
  - 或窄屏下用 compact 浮层替代全屏 DeviceVNCView。
- **当前未实现**：DeviceManagerPage 使用 `DeviceVNCView`、`DeviceDesktopView` 全屏展示，未接入 DeviceFloatingPanel。

### 5.4 小结

| 问题 | 结论 |
|------|------|
| DeviceManagerPage 是否使用 DeviceFloatingPanel？ | ❌ 否 |
| 两者是否共享设备选择逻辑？ | 否；DeviceManagerPage 用 store，DeviceFloatingPanel 用 Agent binding 或 deviceMode |
| 接入 deviceMode 的合适入口？ | DeviceManagerPage 或 LayoutContainer（在 devices 视图时渲染带 deviceMode 的 DeviceFloatingPanel） |

---

## 6. 附录：关键代码位置

| 内容 | 文件 | 行号 |
|------|------|------|
| DeviceFloatingPanel 唯一调用 | ChatPanel.tsx | L59-61 |
| compact/inline/spacer 逻辑 | DeviceFloatingPanel.tsx | L437-453, L497-506 |
| Agent/deviceMode 切换 | DeviceFloatingPanel.tsx | L424-439 |
| DeviceModeConfig 定义 | DeviceFloatingPanel.tsx | L402-406 |
| useDeviceVncTarget | useDeviceVncTarget.ts | 全文 |
| DeviceManagerPage 主视图 | DeviceManagerPage.tsx | L534-596 |
| selectedDeviceId 写入 | AgentDrawer.tsx | L191-195 |
