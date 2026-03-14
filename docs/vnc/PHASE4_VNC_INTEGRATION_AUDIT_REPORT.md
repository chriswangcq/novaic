# Phase 4 VNC 收敛 — 集成与迁移风险审核报告

**审核日期**：2025-03-12  
**审核范围**：DeviceManagerPage、DeviceFloatingPanel、VisualPanel、Header 及关联的 vncStream、DeviceStatusStore、useDeviceStatus  
**原则**：宁可错杀不可放过

---

## 一、审核摘要

| 严重程度 | 数量 | 说明 |
|----------|------|------|
| Critical | 4 | 功能回退、数据源不一致、构建/运行风险 |
| Major | 5 | 行为不一致、潜在 bug、多 tab 风险 |
| Minor | 3 | 可维护性、边界情况 |

---

## 二、Critical 问题

### C1. vncConnected 状态不再更新 — 潜在功能回退

**背景**：`useVNCConnection` 已删除（或从未存在），`vncConnected` 仅由 `VNCViewShared` 在 `onStatusChange('connected')` 时更新。

**影响分析**：
- **VNCViewShared**：会调用 `setVncConnected(true/false)`（VNCViewShared.tsx:45-46, 94-98）
- **AgentDesktopView / DeviceDesktopView**：使用 `createVncTransport` + `useVnc` + `VncCanvas`，**不**更新 `vncConnected`
- **结论**：当用户通过 AgentDesktopView、DeviceDesktopView、DeviceVNCView 连接 VNC 时，`vncConnected` 永远为 `false`

**依赖 vncConnected 的 UI**：
- 搜索结果显示：`vncConnected` 仅在 store 和 types 中定义，**无组件直接读取**
- 但 `types/index.ts` 的 `AppState` 仍包含 `vncConnected`，可能被：
  - 未来功能使用
  - 其他未搜索到的模块使用
  - 序列化/持久化逻辑使用

**建议**：
1. 全局搜索 `vncConnected` 的消费方，确认无遗漏
2. 若确实无消费方，考虑从 store 中移除或标记为 deprecated
3. 若需保留，在 `useVnc` 的 `status === 'connected'` 时同步更新 store

---

### C2. VisualPanel 与 useAgentDevice 数据源不一致

**问题**：VisualPanel 从 `agent.devices` 获取设备，useAgentDevice 从 `getAgentBinding` + `devices.get` 获取。

**代码位置**：
- VisualPanel.tsx:56-61：`currentAgent?.devices?.find(isLinuxDevice)`、`currentAgent?.devices?.find(isAndroidDevice)`
- useAgent 的 agents 来自 `api.listAgents()`，AICAgent 的 `devices` 为 `@deprecated`

**数据流对比**：

| 组件 | 数据源 | 说明 |
|------|--------|------|
| VisualPanel | `agents[].devices` | 来自 listAgents 响应，可能为空或过时 |
| AgentDesktopView | useAgentDevice → getAgentBinding + devices.get | 权威数据源 |
| DeviceFloatingPanel | useAgentBinding → getAgentBinding + devices.get | 权威数据源 |

**风险**：
1. `listAgents` 可能不返回 `devices` 或返回空数组
2. `agent.devices` 与 binding 可能不同步（Agent 只通过 binding 引用设备，不「拥有」devices 列表）
3. VisualPanel 的 `hasLinux`/`hasAndroid` 可能为 false，导致 Linux/Android 切换 tab 不显示或显示错误设备
4. `androidDeviceSerial` 来自 `androidDevice?.device_serial`，若 `agent.devices` 为空则 undefined，ScrcpyView 可能收到空 serial

**建议**：
1. VisualPanel 改为使用 `useAgentDevice(currentAgentId)` 或 `useAgentBinding(currentAgentId, currentAgent?.binding)` 获取设备
2. 或从 `deviceManagerDevices` + `getAgentBinding` 推导当前 Agent 的 Linux/Android 设备
3. 移除对 `agent.devices` 的依赖

---

### C3. DeviceFloatingPanel：main 用 VNCViewShared，vm_user 用 DeviceDesktopView — 行为不一致

**问题**：main 与 vm_user 使用完全不同的 VNC 实现，连接方式、状态管理、错误处理均不同。

| 维度 | main (VNCViewShared) | vm_user (DeviceDesktopView) |
|------|----------------------|-----------------------------|
| 连接方式 | vncStream（vmService.getVncTransport） | createVncTransport + useVnc |
| 传输层 | OTA/WebSocket 由 vncStream 内部决定 | vncTransport（VncBridge 或 WebSocket） |
| 状态更新 | 更新 store.vncConnected | 不更新 |
| 错误 UI | 内置 Start VM / 连接失败 | renderOverlay 统一 |
| 启停逻辑 | startVm 调用 vmService.start(agentId) | DeviceDesktopView 无 main 的 start/stop（vm_user 无启停） |

**行为差异**：
1. **连接建立**：main 用 deviceId 作为 streamKey，vm_user 用 `deviceId:username` 作为 resourceId
2. **viewOnly**：main 通过 `setVNCViewOnly(device.id, !operating)` 控制；DeviceDesktopView 无 viewOnly 透传（需确认）
3. **expand/collapse**：两者都在同一 Card 内，main 的流不重连，vm_user 的 DeviceDesktopView 会随 mount/unmount 重连（取决于父组件是否条件渲染）

**建议**：
1. 统一 main 与 vm_user 的 VNC 实现路径，或明确文档化两种路径的适用场景
2. 若保留双路径，确保 viewOnly、错误处理、重连行为一致
3. 评估 DeviceFloatingPanel 的 main 是否应迁移到 DeviceDesktopView（subjectType='main'），以统一行为

---

### C4. DeviceFloatingPanel：vm_user 的 displayNum 硬编码为 0

**代码**：DeviceFloatingPanel.tsx:308
```tsx
<DeviceDesktopView
  subjectType="vm_user"
  deviceId={device.id}
  username={binding.subject_id}
  displayNum={0}  // 硬编码
  ...
/>
```

**问题**：`AgentDeviceBinding` 无 `display_num` 字段，但 `DeviceSubject` 有。vm_user 的 VNC 端口为 `5900 + display_num`，若实际为 1 或 2，传 0 会连错端口。

**建议**：
1. 从 `api.vmUsers.list(device.id)` 获取对应用户的 `display_num`，或
2. 若 Gateway 的 binding 扩展了 `display_num`，从 binding 读取
3. 否则需确认 vm_user 的 display_num 是否恒为 0

---

## 三、Major 问题

### M1. DeviceFloatingPanel 自建 status 轮询，与 DeviceStatusStore 脱节

**代码**：DeviceFloatingPanel.tsx:407-418
```tsx
const fetchDeviceStatus = useCallback(async () => {
  if (!device?.id) { setDeviceStatuses({}); return; }
  const s = await api.devices.status(device.id);
  setDeviceStatuses({ [device.id]: s.running });
}, [device?.id]);
useEffect(() => {
  fetchDeviceStatus();
  const id = setInterval(fetchDeviceStatus, 5000);
  return () => clearInterval(id);
}, [fetchDeviceStatus]);
```

**问题**：
- DeviceManagerPage、AgentDrawer、DeviceRow 使用 `useDeviceStatus` + `useDeviceStatusPolling`
- DeviceFloatingPanel 独立轮询，不写入 DeviceStatusStore
- 多组件同时显示同一设备时，状态可能不一致
- 轮询间隔 5s 与 DeviceStatusPolling 一致，但数据不共享

**建议**：改用 `useDeviceStatus(device.id)` 并确保父级或全局已启动 `useDeviceStatusPolling`
- 需确认 DeviceFloatingPanel 的父组件是否传入 devices 给 useDeviceStatusPolling
- 当前 DeviceFloatingPanel 仅绑定 agent 的单个 device，AgentDrawer 的 devices 来自 listForUser，可能包含该 device；若 drawer 未打开则 devices 可能为空，轮询不启动

---

### M2. DeviceFloatingPanel 与 DeviceManagerPage 的 device 数据源不同

**DeviceFloatingPanel**：`useAgentBinding` → `getAgentBinding` + `devices.get`  
**DeviceManagerPage**：`deviceManagerDevices`（来自 listForUser）+ `useAgentDevice` 的 device（当 selectedDeviceId 为 agent 绑定设备时）

**风险**：两处同时打开时，若 listForUser 与 getAgentBinding 返回的 device 不一致（如 pc_client_id、status 不同），可能显示不同设备信息。

---

### M3. vncStream 的 streamKey 与 createVncTransport 的 resourceId 语义不一致

**VNCViewShared**：`streamKey = propDeviceId || agentId`，主桌面用 deviceId  
**createVncTransport**：`resourceId` 为 `deviceId`（main）或 `deviceId:username`（vm_user）

**vncStream**：`connectStream(agentId, deviceId)`，内部用 `vmService.getVncTransport(agentId, deviceId)`，stream 存储 key 为 agentId（见 vncStream.ts:116-118 的 streams 使用 agentId）

**注意**：vncStream 的 `streams` 使用 `agentId` 作为 key（connectStream 第一个参数），但 subscribeToVNCStream 的 streamKey 可为 deviceId。需核对 vncStream 内部 key 是否与 streamKey 一致。

---

### M4. 多 tab / 多窗口场景

**风险**：
1. **多 tab**：同一用户打开多个 tab，每个 tab 有独立 React 实例，store 不共享（若为多 tab 则各有 store）。vncStream、DeviceStatusStore 为模块级单例，会共享。
2. **VNCViewShared**：streams 按 streamKey 全局共享，多 tab 订阅同一 stream 会共享连接，可能符合预期
3. **DeviceDesktopView**：每次 mount 创建新 transport，多 tab 会建立多个 VNC 连接
4. **DeviceStatusStore**：多 tab 共享，轮询可能重复执行（每个 tab 的 useDeviceStatusPolling 都会 run）

**建议**：明确多 tab 下的预期行为，并做测试验证

---

### M5. Header 不直接涉及 VNC，但 useAgent 依赖 agents 结构

**Header**：仅用 agents、currentAgentId 做切换，无 VNC 相关逻辑。  
**风险**：若 agents 结构变更（如移除 devices），Header 不受影响，但需确认 useAgent 的 `currentAgent` 是否被其他 VNC 相关逻辑间接使用。

---

## 四、Minor 问题

### m1. 删除 useVNCConnection 的遗留影响

**结论**：useVNCConnection 未在代码库中找到，可能已删除或从未提交。若曾存在，需确认无残留引用。

---

### m2. DeviceFloatingPanel 的 DeviceDesktopView 传 displayNum=0

**见 C4**，此处为 Minor 重复，若 display_num 恒为 0 则可接受。

---

### m3. DeviceStatusStore 与 vncConnectionCount

**useVnc** 会调用 `incrementVncConnectionCount` / `decrementVncConnectionCount`，影响轮询间隔。  
**VNCViewShared** 不调用，因此通过 VNCViewShared 建立的连接不会计入 vncConnectionCount，轮询间隔可能偏大（当仅 VNCViewShared 连接时）。

---

## 五、删除文件对构建和运行的影响

**审核范围**：未发现明确「删除」的 Phase 4 文件列表。  
**假设**：若删除了 useVNCConnection、旧 VNCView 等：

- **构建**：若有残留 import 会报错，需全局搜索确认
- **运行**：若删除后无替代，对应功能会缺失

**建议**：执行 `git diff` 或 `git status` 确认 Phase 4 实际删除的文件，并逐一核对 import 是否已清理。

---

## 六、总结与优先级

| 优先级 | 问题 | 建议 |
|--------|------|------|
| P0 | C2 数据源不一致 | VisualPanel 改用 useAgentDevice/useAgentBinding |
| P0 | C4 displayNum 硬编码 | 从 vmUsers.list 或 binding 获取 |
| P1 | C1 vncConnected | 确认消费方，必要时在 useVnc 中更新 |
| P1 | C3 main vs vm_user 行为不一致 | 文档化或统一实现 |
| P1 | M1 DeviceFloatingPanel 轮询 | 接入 DeviceStatusStore |
| P2 | M4 多 tab | 测试并文档化 |
| P2 | M3 streamKey 语义 | 核对 vncStream 实现 |

---

## 七、审核清单（勾选）

- [x] DeviceManagerPage 调用方检查
- [x] DeviceFloatingPanel 调用方检查
- [x] VisualPanel 调用方检查
- [x] Header 调用方检查
- [x] vncConnected 状态依赖分析
- [x] DeviceFloatingPanel main vs vm_user 行为对比
- [x] VisualPanel 与 useAgentDevice 数据源对比
- [x] vncStream、DeviceStatusStore、useDeviceStatus 集成
- [x] 多 tab / 多窗口场景
- [ ] 删除文件清单（需从 git 获取）
