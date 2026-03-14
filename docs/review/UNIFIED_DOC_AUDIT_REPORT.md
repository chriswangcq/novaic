# UNIFIED_CURRENT_STATE_AND_RESEARCH.md 审核报告

> 审核范围：2.2 前端数据流、六、文件索引 6.1 前端  
> 对照代码路径：novaic-app/src（api, services/vm, components）  
> 审核日期：2025-03-12

---

## 一、2.2 前端数据流 逐条核对

### 1. DeviceManagerPage、AgentDrawer 是否用 listForUser，是否重复写入 deviceManagerDevices

| 项目 | 结论 | 代码位置 |
|------|------|----------|
| DeviceManagerPage 用 listForUser | **正确** | `novaic-app/src/components/VM/DeviceManagerPage.tsx` L468: `const res = await api.devices.listForUser();` |
| DeviceManagerPage 写入 deviceManagerDevices | **正确** | 同上 L469: `patchState({ deviceManagerDevices: next });` |
| AgentDrawer 用 listForUser | **正确** | `novaic-app/src/components/Layout/AgentDrawer.tsx` L92: `const res = await api.devices.listForUser();` |
| AgentDrawer 写入 deviceManagerDevices | **正确** | 同上 L95: `setDeviceManagerDevices(next);` |
| 重复调用、重复写入 | **正确** | 两处均独立调用 listForUser 并写入 store，存在重复 |

**修正建议**：可考虑由 AgentDrawer 或 DeviceManagerPage 单一数据源，另一处仅订阅 `deviceManagerDevices`；或抽离共享 `loadDevices` + 统一写入逻辑。

---

### 2. DeviceFloatingPanel、DeviceSidebar 是否用 getAgentBinding / agent.devices，是否未渲染

| 项目 | 结论 | 说明 |
|------|------|------|
| DeviceFloatingPanel 用 getAgentBinding | **错误** | **文件不存在**。项目中无 `DeviceFloatingPanel.tsx`，仅 `VmUserVNCView.tsx` L19 注释提到 "for embedding in DeviceFloatingPanel" |
| DeviceSidebar 用 agent.devices | **错误** | **文件不存在**。项目中无 `DeviceSidebar.tsx`，仅 `App.tsx` 注释提到 "DeviceSidebar" |
| 未渲染 | **需补充** | 文档写「未渲染」易理解为「已实现但未接入」。实际是 **组件文件不存在**，属于未实现 |

**修正建议**：文档应改为「DeviceFloatingPanel、DeviceSidebar 尚未实现（无对应组件文件）」，避免与「已实现但未接入」混淆。

---

### 3. api.ts 是否有 devices.*、getAgentBinding

| 项目 | 结论 | 代码位置 |
|------|------|----------|
| api.devices.* | **正确** | `novaic-app/src/services/api.ts` L746-823：`devices.listForUser`、`list`、`get`、`start`、`stop`、`status` 等 |
| api.getAgentBinding | **正确** | 同上 L365-369: `async getAgentBinding(agentId: string): Promise<AgentDeviceBinding \| null>` |

---

### 4. vm.ts 是否有 getVncTransport、getVncUrl

| 项目 | 结论 | 代码位置 |
|------|------|----------|
| getVncTransport | **正确** | `novaic-app/src/services/vm.ts` L176-185 |
| getVncUrl | **正确** | 同上 L166-169 |

**说明**：签名均为 `(agentId: string, deviceId?: string)`，与文档一致。

---

### 5. 文件索引 6.1 前端 路径准确性

| 文档路径 | 实际路径 | 结论 |
|----------|----------|------|
| `api.ts` | `novaic-app/src/services/api.ts` | **需补充**：应写 `services/api.ts` |
| `vm.ts` | `novaic-app/src/services/vm.ts` | **需补充**：应写 `services/vm.ts` |
| `vncBridge.ts` | `novaic-app/src/services/vncBridge.ts` | **需补充**：应写 `services/vncBridge.ts` |
| `vncStream.ts` | `novaic-app/src/services/vncStream.ts` | **需补充**：应写 `services/vncStream.ts` |
| `useAgentBinding.ts` | **不存在** | **错误**：项目中无此文件 |
| `DeviceManagerPage.tsx` | `novaic-app/src/components/VM/DeviceManagerPage.tsx` | **需补充**：应写 `components/VM/DeviceManagerPage.tsx` |
| `AgentDrawer.tsx` | `novaic-app/src/components/Layout/AgentDrawer.tsx` | **需补充**：应写 `components/Layout/AgentDrawer.tsx` |
| `DeviceFloatingPanel.tsx` | **不存在** | **错误** |
| `DeviceSidebar.tsx` | **不存在** | **错误** |
| `VmUserVNCView.tsx` | `novaic-app/src/components/VM/VmUserVNCView.tsx` | **需补充**：应写 `components/VM/VmUserVNCView.tsx` |
| `VNCViewShared.tsx` | **不存在** | **错误**：实际为 `VNCView.tsx`（`components/Visual/VNCView.tsx`），无 VNCViewShared |
| `DeviceVNCView.tsx` | `novaic-app/src/components/Visual/DeviceVNCView.tsx` | **需补充**：应写 `components/Visual/DeviceVNCView.tsx` |
| `useVNCConnection.ts` | `novaic-app/src/components/Visual/useVNCConnection.ts` | **需补充**：应写 `components/Visual/useVNCConnection.ts` |
| `useDeviceVNCConnection.ts` | `novaic-app/src/components/Visual/useDeviceVNCConnection.ts` | **需补充**：应写 `components/Visual/useDeviceVNCConnection.ts` |

---

### 6. 轮询 status 的间隔（5s/5s/3s）是否准确

| 场景 | 文档描述 | 实际值 | 结论 | 代码位置 |
|------|----------|--------|------|----------|
| AgentDrawer VM status 轮询 | 5s | **5000ms** | **正确** | `AgentDrawer.tsx` L107: `POLL_CONFIG.VM_STATUS_NORMAL_INTERVAL` → config L94: 5000 |
| AgentDrawer loadDevices 轮询 | 5s | **5000ms** | **正确** | `AgentDrawer.tsx` L115: `POLL_CONFIG.VM_STATUS_NORMAL_INTERVAL` → 5000 |
| useVNCConnection WebSocket 重试轮询 | 3s | **3000ms** | **正确** | `useVNCConnection.ts` L209-215: `setInterval(..., 3000)` |
| useDeviceVNCConnection WebSocket 重试轮询 | 3s | **3000ms** | **正确** | `useDeviceVNCConnection.ts` L157-160: `setInterval(..., 3000)` |

**说明**：config 中还有 `VM_STATUS_FAST_INTERVAL: 3000`、`VNC_POLL_INTERVAL: 5000`，文档未区分具体用途，但 5s/5s/3s 的表述与上述实际用法一致。

---

## 二、修正建议汇总

### 2.2 前端数据流

1. **DeviceFloatingPanel、DeviceSidebar**：改为「尚未实现（无对应组件文件）」，删除「用 getAgentBinding / agent.devices」的描述。
2. **问题列表**：保留「DeviceManagerPage 与 AgentDrawer 重复调用 listForUser、重复写入 deviceManagerDevices」；补充「DeviceFloatingPanel、DeviceSidebar 未实现」。

### 6.1 前端文件索引

1. **删除不存在的文件**：`useAgentBinding.ts`、`DeviceFloatingPanel.tsx`、`DeviceSidebar.tsx`。
2. **VNCViewShared.tsx**：改为 `VNCView.tsx`，路径 `components/Visual/VNCView.tsx`。
3. **补全路径**：所有条目统一为 `novaic-app/src/` 下的相对路径（如 `services/api.ts`、`components/VM/DeviceManagerPage.tsx` 等）。

---

## 三、核对结论汇总表

| 核对项 | 结论 |
|--------|------|
| DeviceManagerPage 用 listForUser | 正确 |
| AgentDrawer 用 listForUser | 正确 |
| 重复写入 deviceManagerDevices | 正确 |
| DeviceFloatingPanel 用 getAgentBinding | 错误（文件不存在） |
| DeviceSidebar 用 agent.devices | 错误（文件不存在） |
| api.ts devices.* / getAgentBinding | 正确 |
| vm.ts getVncTransport / getVncUrl | 正确 |
| 文件索引路径 | 部分错误/需补充 |
| 轮询间隔 5s/5s/3s | 正确 |
