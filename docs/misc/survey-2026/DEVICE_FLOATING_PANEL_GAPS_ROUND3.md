# DeviceFloatingPanel 接入建议（深层）

> 基于 R1/R2 输出，产出 DeviceFloatingPanel 接入的深层建议：现状、deviceMode 接入可行方案、与 Agent 模式的协作关系。

**输入**：`DEVICE_FLOATING_PANEL_ROUND2.md`、`ChatPanel.tsx`、`DeviceManagerPage.tsx`、`DeviceFloatingPanel.tsx`、`LayoutContainer.tsx`、`AgentDrawer.tsx`

---

## 1. 现状：ChatPanel 已接入 compact，deviceMode 无传入方

### 1.1 当前接入情况

| 维度 | 现状 |
|------|------|
| **唯一调用方** | ChatPanel（L59-61）：`<DeviceFloatingPanel compact />` |
| **compact** | ✅ 已传入，浮层不占布局空间，右上角堆叠 |
| **deviceMode** | ❌ 未传入，始终为 `undefined` |
| **inline** | ❌ 未使用 |
| **placement** | 未使用（仅 inline 时生效） |

### 1.2 渲染路径与可见性

```
LayoutContainer
   │
   ├─ activeView === 'chat' 时
   │     └─ ChatPanel
   │           └─ DeviceFloatingPanel compact  ← 唯一挂载点，Agent 模式
   │
   └─ activeView === 'devices' 时
         └─ DeviceManagerPage  ← 不包含 DeviceFloatingPanel
```

- **Chat 视图**：DeviceFloatingPanel 以 Agent 模式渲染，依赖 `currentAgentId`；无当前 Agent 时 `return null`。
- **Devices 视图**：DeviceManagerPage 直接渲染 `DeviceVNCView` / `DeviceDesktopView` 全屏，**不渲染 DeviceFloatingPanel**。

### 1.3 deviceMode 能力现状

DeviceFloatingPanel 已实现 deviceMode 逻辑，但**无任何调用方传入**：

| 能力 | 实现位置 | 使用情况 |
|------|----------|----------|
| `DeviceModeConfig` 接口 | DeviceFloatingPanel L402-406 | 未使用 |
| `useDeviceVncTarget` | DeviceFloatingPanel L419-423 | 仅当 `deviceMode` 有值时生效 |
| `syntheticBinding` | DeviceFloatingPanel L443-455 | 仅 deviceMode 时构造 |
| `onStartVm` | DeviceFloatingPanel L457-459 | 仅 deviceMode 时传入 `api.devices.start` |
| Agent/deviceMode 切换 | DeviceFloatingPanel L424-439 | 始终走 Agent 分支 |

### 1.4 小结

- ChatPanel 已正确接入 compact 模式。
- deviceMode 能力完整，但**无传入方**，处于未使用状态。
- Devices 视图与 DeviceFloatingPanel 完全解耦，设备展示由 DeviceManagerPage 自行处理。

---

## 2. 接入 deviceMode 的可行方案

### 2.1 方案 A：DeviceManagerPage 内嵌 DeviceFloatingPanel（推荐）

**思路**：在 Devices 视图中，用 DeviceFloatingPanel（deviceMode）替代或补充当前全屏 DeviceVNCView。

#### 2.1.1 数据来源

DeviceManagerPage 与 AgentDrawer 共享 store：

- `selectedDeviceId`：当前选中设备
- `selectedVmUser`：`null` = main desktop，`{ username, displayNum }` = vm_user

可据此构造 `deviceMode`：

```typescript
const deviceMode = selectedDeviceId
  ? {
      deviceId: selectedDeviceId,
      subjectType: selectedVmUser ? 'vm_user' : 'main',
      subjectId: selectedVmUser?.username ?? undefined,
    }
  : undefined;
```

#### 2.1.2 子方案对比

| 子方案 | 描述 | 优点 | 缺点 |
|-------|------|------|------|
| **A1：完全替代** | 用 `DeviceFloatingPanel compact deviceMode={...}` 替代 DeviceVNCView/DeviceDesktopView | 统一浮层体验，代码复用 | 全屏场景需依赖 expand |
| **A2：并存** | 保留全屏视图，同时渲染 compact DeviceFloatingPanel | 兼容现有全屏习惯 | 两套展示可能重复 |
| **A3：按布局切换** | 宽屏用全屏，窄屏用 compact 浮层 | 适配不同屏幕 | 逻辑更复杂 |

#### 2.1.3 推荐实现（A1 变体）

- **有选中设备时**：仅渲染 `DeviceFloatingPanel compact deviceMode={...}`，不再渲染 DeviceVNCView/DeviceDesktopView。
- **无选中设备时**：保持当前空状态（提示从 Devices 区选择设备）。

修改位置示例：

```tsx
// DeviceManagerPage.tsx 主内容区
{effectiveSelectedDevice ? (
  <DeviceFloatingPanel
    compact
    deviceMode={{
      deviceId: effectiveSelectedDevice.id,
      subjectType: selectedVmUser ? 'vm_user' : 'main',
      subjectId: selectedVmUser?.username,
    }}
  />
) : (
  // 空状态...
)}
```

注意：deviceMode 为 vm_user 时，`DeviceModeConfig.subjectId` 需传 `username`；`displayNum` 由 DeviceFloatingPanel 内部通过 `vmUsers.list` 获取。

#### 2.1.4 与现有 DeviceVNCView 的差异

| 维度 | DeviceVNCView / DeviceDesktopView | DeviceFloatingPanel |
|------|-----------------------------------|----------------------|
| 布局 | 全屏占满 | compact 浮层，可 expand |
| 关闭 | onClose 清空 selectedDeviceId | 无 onClose，需在 DeviceManagerPage 层处理 |
| 启动 VM | 内部处理 | deviceMode 时用 `api.devices.start` |

若采用 A1，需在 DeviceFloatingPanel 或 DeviceManagerPage 增加「关闭/取消选中」入口（如工具栏按钮），并调用 `patchState({ selectedDeviceId: null, selectedVmUser: null })`。

---

### 2.2 方案 B：LayoutContainer 统一挂载 deviceMode 浮层

**思路**：在 LayoutContainer 层，当 `activeView === 'devices'` 且存在 `selectedDeviceId` 时，额外渲染一个 DeviceFloatingPanel（deviceMode）。

#### 2.2.1 实现示意

```tsx
// LayoutContainer.tsx
const selectedDeviceId = useAppStore(s => s.selectedDeviceId);
const selectedVmUser = useAppStore(s => s.selectedVmUser);

// 在 main 内、与 ChatPanel/DeviceManagerPage 同级
{activeView === 'devices' && selectedDeviceId && (
  <DeviceFloatingPanel
    compact
    deviceMode={{
      deviceId: selectedDeviceId,
      subjectType: selectedVmUser ? 'vm_user' : 'main',
      subjectId: selectedVmUser?.username,
    }}
  />
)}
```

#### 2.2.2 与 DeviceManagerPage 的关系

- DeviceManagerPage 可继续使用 DeviceVNCView 全屏，或改为空状态/简化视图。
- DeviceFloatingPanel 作为浮层叠加在 Devices 视图上。
- 优点：LayoutContainer 统一控制浮层，DeviceManagerPage 职责更单一。
- 缺点：需明确 DeviceManagerPage 与浮层的主次关系，避免重复展示。

---

### 2.3 方案 C：独立设备视图（新入口）

**思路**：新增不依赖 Agent、不依赖 Devices tab 的「独立设备预览」入口，直接使用 DeviceFloatingPanel + deviceMode。

#### 2.3.1 典型场景

- 从通知、快捷入口、外部链接打开指定设备预览。
- 独立路由，如 `/device/:deviceId` 或 `/device/:deviceId/:subjectType/:subjectId`。

#### 2.3.2 实现要点

- 新页面/路由组件，从 URL 或 store 读取 `deviceId`、`subjectType`、`subjectId`。
- 渲染 `DeviceFloatingPanel compact deviceMode={...}` 或 `inline`。
- 与 Chat、Devices 视图解耦，不依赖 `currentAgentId` 或 AgentDrawer 选择。

#### 2.3.3 适用性

- 适合作为后续扩展，用于深度链接、通知跳转等。
- 当前阶段优先级可低于方案 A/B。

---

### 2.4 方案对比小结

| 方案 | 改动范围 | 复杂度 | 推荐度 | 备注 |
|------|----------|--------|--------|------|
| **A：DeviceManagerPage 内嵌** | DeviceManagerPage | 中 | ⭐⭐⭐ | 直接复用 deviceMode，体验统一 |
| **B：LayoutContainer 挂载** | LayoutContainer | 低 | ⭐⭐ | 需协调与 DeviceManagerPage 的展示关系 |
| **C：独立设备视图** | 新路由/页面 | 中 | ⭐ | 适合后续扩展 |

---

## 3. 与 Agent 模式的协作关系

### 3.1 模式互斥与数据源

DeviceFloatingPanel 内部对 Agent 模式与 deviceMode 做互斥切换：

```typescript
// DeviceFloatingPanel.tsx L424-432
const isDeviceMode = !!deviceMode;
const device = isDeviceMode ? deviceVncTarget.device : agentBinding.device;
// ...
if (!isDeviceMode && !currentAgentId) return null;
```

| 条件 | 模式 | 数据源 | 渲染条件 |
|------|------|--------|----------|
| `deviceMode` 有值 | **deviceMode** | `useDeviceVncTarget(deviceId, subjectType, subjectId)` | device 存在且无 error |
| `deviceMode` 无值 且 `currentAgentId` 有值 | **Agent 模式** | `useAgentBinding(currentAgentId, ...)` | device 存在且无 error |
| `deviceMode` 无值 且 `currentAgentId` 无值 | - | - | **return null**，不渲染 |

### 3.2 视图与模式映射

| 视图 | 挂载位置 | 模式 | 设备来源 |
|------|----------|------|----------|
| **Chat** | ChatPanel | Agent | `currentAgentId` → binding.device_id |
| **Devices** | DeviceManagerPage（或 LayoutContainer） | deviceMode | `selectedDeviceId` + `selectedVmUser` |

两者不会同时生效：同一时刻要么 Agent 模式，要么 deviceMode。

### 3.3 切换行为

1. **Chat → Devices**：ChatPanel 卸载，DeviceManagerPage 挂载；若接入方案 A/B，则 DeviceFloatingPanel 以 deviceMode 渲染，设备来自 `selectedDeviceId`。
2. **Devices → Chat**：DeviceManagerPage 卸载，ChatPanel 挂载；DeviceFloatingPanel 切回 Agent 模式，设备来自 `currentAgentId` 的 binding。
3. **无 Agent 时进 Chat**：`!currentAgentId` → DeviceFloatingPanel 不渲染。
4. **无选中设备时进 Devices**：若采用方案 A/B 且 `!selectedDeviceId`，则不渲染 deviceMode 浮层（或显示空状态）。

### 3.4 协作设计原则

1. **单一数据源**：Agent 模式用 `currentAgentId`，deviceMode 用 `selectedDeviceId` + `selectedVmUser`，避免混用。
2. **状态边界清晰**：`selectedDeviceId` / `selectedVmUser` 由 AgentDrawer 写入，DeviceManagerPage 或 LayoutContainer 读取；DeviceFloatingPanel 仅消费 props，不直接写 store。
3. **关闭/取消选中**：deviceMode 下需提供「关闭预览」并清空 `selectedDeviceId`，可由 DeviceManagerPage 或 LayoutContainer 提供入口并调用 `patchState`。

### 3.5 潜在冲突与处理

| 场景 | 风险 | 建议 |
|------|------|------|
| 快速切换 Chat/Devices | 浮层闪烁或重复挂载 | 依赖 React 挂载/卸载，一般无问题 |
| Agent 绑定设备 = 当前选中设备 | 两套逻辑指向同一设备 | 正常，仅数据源不同 |
| 从 Devices 选设备后切回 Chat | selectedDeviceId 仍存在 | 可选：切回 Chat 时清空 selectedDeviceId，避免混淆 |

---

## 4. 附录：关键代码位置

| 内容 | 文件 | 行号 |
|------|------|------|
| ChatPanel 调用 DeviceFloatingPanel | ChatPanel.tsx | L59-61 |
| DeviceFloatingPanel props 与 deviceMode 逻辑 | DeviceFloatingPanel.tsx | L407-439 |
| DeviceManagerPage 主视图 | DeviceManagerPage.tsx | L534-596 |
| selectedDeviceId 写入 | AgentDrawer.tsx | L193-197 |
| LayoutContainer 视图分支 | LayoutContainer.tsx | L91-93, L145-149, L218-223 |
