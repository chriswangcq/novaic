# 第三轮调研（深层）：DeviceFloatingPanel 接入与 deviceMode 使用

> 调研范围：DeviceFloatingPanel 渲染位置、deviceMode 传入方、预期使用场景、接入建议

---

## 一、DeviceFloatingPanel 的渲染位置

### 1.1 设计文档中的预期位置

| 来源 | 预期位置 | 说明 |
|------|----------|------|
| **HANDOVER.md** | ChatPanel 内 | `ChatPanel ├── DeviceFloatingPanel (compact) ← 右上角浮层，不占布局` |
| **DEVICE_MANAGEMENT_AGENT_STRATEGY_REPORT** | ChatPanel 内右上角浮层 | 设计为「Agent 上下文的设备预览」 |
| **unify-vnc/04-task-breakdown** | 按需实现 | P4-19：Popover + `useAgentDevice` |

### 1.2 实际代码中的渲染情况

| 组件 | 是否渲染 DeviceFloatingPanel | 说明 |
|------|------------------------------|------|
| **LayoutContainer** | ❌ 否 | 仅包含 PrimaryNav、AgentDrawer、Resizer、Header、ChatPanel、DeviceManagerPage、SettingsModal、MorePage |
| **AgentDrawer** | ❌ 否 | 仅包含 Agents tab、Devices tab、Settings 相关，无 DeviceFloatingPanel |
| **ChatPanel** | ❌ 否 | 包含 MessageList、MainAgentLogPreview、SubagentList、ExecutionLog、ChatInput，**无 DeviceFloatingPanel** |
| **App.tsx** | ❌ 否 | 仅注释提到 DeviceSidebar，无 DeviceFloatingPanel 引用 |

### 1.3 结论

**DeviceFloatingPanel 当前为 orphaned 组件**：已实现（约 670 行），但未被任何父组件 import 或渲染。设计文档中「ChatPanel 内右上角浮层」的位置尚未接入。

---

## 二、当前是否有组件传入 deviceMode？

### 2.1 调用方检查

```bash
# 全项目 grep：DeviceFloatingPanel 的 import 与使用
```

| 文件 | 行为 |
|------|------|
| `DeviceFloatingPanel.tsx` | 自身定义并导出 |
| `useDeviceVncTarget.ts` | 注释提及「用于 DeviceFloatingPanel 的 deviceMode」 |
| **其他 .tsx/.ts 文件** | **无 import、无渲染、无 deviceMode 传入** |

### 2.2 结论

**当前没有任何组件传入 deviceMode**。因为 DeviceFloatingPanel 本身未被渲染，所以不存在调用方，deviceMode 的传入方为「暂无」。

---

## 三、deviceMode 的预期使用场景

### 3.1 接口定义

```ts
// DeviceFloatingPanel.tsx L537-542
export interface DeviceModeConfig {
  deviceId: string;
  subjectType: 'main' | 'vm_user' | 'default';
  subjectId?: string;  // vm_user 时必填
}
```

### 3.2 双模式逻辑（组件内已实现）

| 模式 | 数据源 | 条件 | 触发 |
|------|--------|------|------|
| **Agent 模式** | `useAgentBinding(currentAgentId)` | 无 deviceMode 且 currentAgentId 存在 | 有 Agent 时展示其绑定设备 |
| **deviceMode** | `useDeviceVncTarget(deviceId, subjectType, subjectId)` | deviceMode 存在 | 父组件传入 deviceId + subject |

### 3.3 预期入口与触发条件

| 场景 | 入口 | 触发条件 | deviceMode 来源 |
|------|------|----------|-----------------|
| **Agent 上下文预览** | ChatPanel 右上角 | 选中 Agent 且有 binding | 不传（Agent 模式） |
| **从 Devices tab 选择设备后预览** | AgentDrawer Devices tab 选择 | 用户点击某设备 → 可选在 Chat 旁浮层预览 | `selectedDeviceId` + `selectedVmUser` |
| **DeviceManagerPage 内嵌预览** | 设备管理页 | 在设备列表旁展示 mini 预览 | `selectedDeviceId` + `selectedVmUser` |
| **独立设备查看（无 Agent）** | 任意入口 | 需要「只看设备、不选 Agent」时 | 显式传入 deviceId + subject |

### 3.4 设计文档中的预期

- **12-radical-agent-device-separation-design**：DeviceFloatingPanel 支持 deviceMode，当 deviceId 直接传入时，用 `devices.get(deviceId)` + subject 构造 VncTarget，不查 AgentBinding。
- **expert-advance-for-unify-vnc**：DeviceFloatingPanel 用 Popover 实现即可，数据源为 `useAgentDevice`；若需脱离 Agent 直接查看设备，需 `deviceMode` 或类似机制。
- **DEVICE_AGENT_DECOUPLE_DATAFLOW_RESEARCH_ROUND2**：DeviceManagerPage 可选接入 useDeviceVncTarget；DeviceFloatingPanel 的 deviceMode 用于「纯 Device 流」场景。

---

## 四、DeviceFloatingPanel 接入现状 + deviceMode 接入建议

### 4.1 接入现状汇总

| 维度 | 状态 | 说明 |
|------|------|------|
| **组件实现** | ✅ 已实现 | 约 670 行，支持 main/vm_user/default、VNCViewShared、DeviceDesktopView、ScrcpyView |
| **渲染位置** | ❌ 未接入 | 设计为 ChatPanel 内右上角，实际未渲染 |
| **Agent 模式** | ✅ 已支持 | useAgentBinding，有 currentAgentId 时渲染 |
| **deviceMode** | ✅ 已支持 | useDeviceVncTarget，传入 deviceMode 时渲染 |
| **deviceMode 传入方** | ❌ 暂无 | 无父组件调用，故无传入 |
| **数据源** | ✅ 已接入 | useDeviceStatusPolling + useDeviceStatus（DeviceStatusStore） |

### 4.2 接入建议

#### 4.2.1 第一步：接入 Agent 模式（按设计文档）

**位置**：`ChatPanel.tsx` 内，与主内容区同级，作为 compact 浮层。

```tsx
// ChatPanel.tsx 内
<div className="relative flex flex-col h-full bg-nb-bg/50">
  <DeviceFloatingPanel compact />  {/* 右上角浮层，不占布局 */}
  <div ref={mainAreaRef} className="flex-1 flex flex-col min-h-0 relative">
    {/* MessageList、Execution Log 等 */}
  </div>
  {/* ... */}
</div>
```

**条件**：仅在 `activeView === 'chat'` 时渲染（LayoutContainer 内 ChatPanel 已满足此条件）。

#### 4.2.2 第二步：deviceMode 接入（可选）

**场景 A：AgentDrawer Devices tab 选择后，在 Chat 旁浮层预览**

- 当 `activeView === 'chat'` 且 `selectedDeviceId` 存在时，可选传入 deviceMode：
  ```tsx
  deviceMode={selectedDeviceId ? {
    deviceId: selectedDeviceId,
    subjectType: selectedVmUser ? 'vm_user' : 'main',
    subjectId: selectedVmUser?.username
  } : undefined}
  ```
- 需与产品确认：是「Agent 绑定设备预览」优先，还是「Devices tab 选中设备」优先；若两者共存，需定义优先级规则。

**场景 B：DeviceManagerPage 内嵌 mini 预览**

- 在 DeviceManagerPage 内渲染 `<DeviceFloatingPanel inline deviceMode={...} />`，传入 `effectiveSelectedDevice` + `selectedVmUser`。
- 与主区 DeviceVNCView/DeviceDesktopView 可能重复，需评估是否必要。

**场景 C：独立设备查看（无 Agent）**

- 任意入口需「只看设备」时，传入 deviceMode，不依赖 currentAgentId。
- 当前 `if (!isDeviceMode && !currentAgentId) return null` 已支持该逻辑。

#### 4.2.3 优先级建议

| 优先级 | 任务 | 说明 |
|--------|------|------|
| **P0** | 在 ChatPanel 内渲染 DeviceFloatingPanel（compact，Agent 模式） | 符合 HANDOVER 设计，补齐缺失接入 |
| **P1** | 确认 deviceMode 产品需求 | 若需「Devices tab 选择后浮层预览」，由 LayoutContainer 或 ChatPanel 传入 selectedDeviceId + selectedVmUser |
| **P2** | DeviceManagerPage 内嵌 deviceMode | 按需，避免与主区 VNC 重复 |

### 4.3 数据流示意（接入后）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent 模式（ChatPanel 内）                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  currentAgentId → useAgentBinding → device + binding                         │
│       │                                                                      │
│       ▼                                                                      │
│  DeviceFloatingPanel(compact)  ← 右上角浮层                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  deviceMode（可选接入）                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  selectedDeviceId + selectedVmUser (AppStore)                                 │
│       │                                                                      │
│       ▼                                                                      │
│  DeviceFloatingPanel(compact, deviceMode={{ deviceId, subjectType, subjectId }})│
│       │                                                                      │
│       ▼                                                                      │
│  useDeviceVncTarget → devices.get(deviceId) → VncTarget                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 五、附录：关键文件路径

| 文件 | 路径 |
|------|------|
| DeviceFloatingPanel | `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` |
| ChatPanel | `novaic-app/src/components/Chat/ChatPanel.tsx` |
| LayoutContainer | `novaic-app/src/components/Layout/LayoutContainer.tsx` |
| AgentDrawer | `novaic-app/src/components/Layout/AgentDrawer.tsx` |
| useDeviceVncTarget | `novaic-app/src/hooks/useDeviceVncTarget.ts` |
| useAgentBinding | `novaic-app/src/hooks/useAgentBinding.ts` |
