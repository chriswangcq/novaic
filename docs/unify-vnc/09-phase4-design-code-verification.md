# Phase 4 设计文档与代码对照检查报告

> 对照 `docs/unify-vnc/02-expert-design.md`、`04-task-breakdown.md`、`03-maindesk-vs-subuser.md` 与当前代码实现，逐项核对。

---

## 一、设计文档关键要求

### 1.1 02-expert-design 核心设计

| 设计点 | 要求 | 来源 |
|--------|------|------|
| VncTarget | pcClientId、resourceId、subjectType、deviceId、username? | §1.3 |
| createVncTransport | 根据 pcClientId 判断本机/远程；本机 ws://localhost/...；远程 Bridge 或 P2P | §3.2 |
| useVnc | 接收 transport + rfbOptions，管理生命周期，2s 重试、5 次、指数退避 | §3.2 |
| VncCanvas | 纯展示，接收 vnc 会话，渲染画面、处理输入 | §4.1 |
| AgentDesktopView | useAgentDevice → createVncTransport → useVnc → VncCanvas | §4.1 |
| DeviceDesktopView | deviceId、subjectType、subjectId，跳过 binding，直接构造 VncTarget | §4.1 |
| RFB 参数 | shared: true、wsProtocols: ['binary']、credentials、clipViewport: true | §3.2 |
| WebSocket 探测 | 取消前端探测，依赖后端 ensure_vnc_endpoint | §3.3 |
| vncStream | 保留但重构为 createVncTransport 的共享模式（P4-17） | §4.2 |

### 1.2 04-task-breakdown Phase 4 任务

- P4-1~5：createVncTransport
- P4-6~10：useVnc + VncCanvas
- P4-11~17：业务层组件、迁移、删除旧 hook
- P4-17：vncStream 重构（未完成）

---

## 二、代码实现对照

### 2.1 传输层 createVncTransport

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| 函数签名 | `createVncTransport(target: VncTarget)` | ✅ `createVncTransport(target: VncTarget)` | 一致 |
| OTA/Bridge | shouldUseVncBridge 合并进内部 | ✅ 内部调用 `shouldUseVncBridge()` | 一致 |
| 本机 URL | ws://localhost/.../vnc/{pc_client_id}/{resource_id} | ✅ 通过 `get_vnc_proxy_url`，Tauri 内部构造 | 一致 |
| 参数映射 | resourceId → agent_id；pcClientId → device_id | ✅ `agentId: resourceId, deviceId: pcClientId ?? null` | 一致 |
| P2P vs Bridge | Tauri 内部根据 my-devices 决策 | ✅ vnc_urls.rs 优先 local_vmcontrol，否则 my-devices | 一致 |

**vnc_urls.rs 参数语义**：`agentId` = resource_id（maindesk: device_id；subuser: device_id:username），`deviceId` = pc_client_id。与 createVncTransport 传参一致。

---

### 2.2 通用层 useVnc + VncCanvas

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| useVnc 签名 | `useVnc(transport, rfbOptions)` | ✅ `useVnc(transport, containerRef, options)` | 多 containerRef，合理（RFB 需挂载点） |
| 重连策略 | 2s 起、5 次、指数退避 | ✅ RETRY_DELAY_MS=2000, MAX_RETRIES=5, `delay * 2^retryCount` | 一致 |
| 状态 | connecting \| connected \| disconnected \| reconnecting \| failed | ✅ `VncSessionStatus` 五种状态 | 一致 |
| VncCanvas | 纯展示，接收 vnc 会话 | ✅ 接收 transport + options，内部 useVnc，renderOverlay 可选 | 一致 |
| WebSocket 探测 | 取消 | ✅ useVnc 无 testWebSocket，直接 RFB 连接 | 一致 |

---

### 2.3 RFB 参数

| 参数 | 设计 | RFB_OPTIONS | useVnc 使用 | 结论 |
|------|------|-------------|------------|------|
| shared | true | ✅ true | ✅ `{ ...RFB_OPTIONS }` | 一致 |
| wsProtocols | ['binary'] | ✅ ['binary'] | 继承 | 一致 |
| credentials | 按设备配置 | ✅ {} | 继承 | 一致 |
| clipViewport | true | ✅ true | 可 override | 一致 |

**vncStream 特例**：frame capture 时 `clipViewport: false`，设计文档未明确，属合理 override。

---

### 2.4 业务层组件

| 组件 | 设计 | 实现 | 结论 |
|------|------|------|------|
| AgentDesktopView | useAgentDevice → createVncTransport → useVnc → VncCanvas | ✅ 流程一致 | 一致 |
| DeviceDesktopView | deviceId、subjectType、subjectId，直接 VncTarget | ✅ main: device；vm_user: deviceId, username, displayNum, pcClientId | 一致（displayNum 为 UI 用） |
| VNCView 迁移 | → AgentDesktopView | ✅ 已删除，VisualPanel 用 AgentDesktopView | 一致 |
| DeviceVNCView 迁移 | → DeviceDesktopView 或 AgentDesktopView | ✅ Linux→DeviceDesktopView，Android→Scrcpy+start/stop | 一致 |
| VmUserVNCView 迁移 | → DeviceDesktopView | ✅ 已删除，DeviceManagerPage/DeviceFloatingPanel 用 DeviceDesktopView | 一致 |
| useVNCConnection 删除 | 删除 | ✅ 已删除 | 一致 |
| useDeviceVNCConnection 删除 | 删除 | ✅ 已删除 | 一致 |

---

### 2.5 DeviceFloatingPanel 与 VNCViewShared

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| main 分支 | 设计目标为统一到 AgentDesktopView/DeviceDesktopView | ⚠️ 仍用 **VNCViewShared**（vncStream） | **与设计有偏差** |
| vm_user 分支 | → DeviceDesktopView | ✅ DeviceDesktopView | 一致 |
| 数据源 | useAgentDevice | ✅ useAgentBinding（等价） | 一致 |
| pcClientId | 多 PC 需传 | ✅ VNCViewShared 已传 pcClientId；DeviceDesktopView 已传 device.pc_client_id | **已修复** |
| VNCViewShared | 未传 pcClientId 给 vncStream | ✅ `subscribeToVNCStream(streamKey, subscriber, pcClientId)` | **已修复** |

**说明**：P4-17 要求将 vncStream 重构为 createVncTransport 的共享模式，当前未完成。main 仍走 vncStream，已修复 pcClientId 传递。

---

### 2.6 VncTarget 与 useAgentDevice

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| pcClientId | 可选，Phase 1 可由 createVncTransport 解析 | ✅ 可选，useAgentDevice 从 device.pc_client_id 填充 | 一致 |
| resourceId | maindesk: device_id；subuser: deviceId:username | ✅ bindingToVncTarget 正确拼接 | 一致 |
| subjectType | main \| vm_user \| default | ✅ 类型定义一致 | 一致 |

---

### 2.7 状态轮询与 DeviceStatusStore

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| 轮询收敛 | 单一 store，无重复定时器 | ✅ useDeviceStatusPolling + DeviceStatusStore | 一致 |
| VNC 连接期间 | 轮询降为 3s | ✅ useVnc 中 incrementVnc/decrementVnc 通知 store | 一致 |
| DeviceFloatingPanel | 应订阅 store | ✅ useDeviceStatusPolling + useDeviceStatus | **已修复** |

---

### 2.8 get_vnc_proxy_url 与 vnc_proxy 路径

| 检查项 | 设计 | 实现 | 结论 |
|--------|------|------|------|
| 路径语义 | 建议 `/vnc/{pc_client_id}/{resource_id}` | vnc_proxy.rs `ws_url(device_id, agent_id)` | 语义一致（device_id 即 pc_client_id） |
| 注释 | 标注 device_id 实为 pc_client_id | ✅ vnc_urls.rs 注释已说明 | 一致 |

---

## 三、与设计文档的偏差汇总

### 3.1 已修复

| 编号 | 偏差 | 修复 |
|------|------|------|
| D2 | VNCViewShared 未传 pcClientId | ✅ VNCViewShared 增加 pcClientId prop，DeviceFloatingPanel 传入 device.pc_client_id |
| D3 | DeviceFloatingPanel 自建 5s 轮询 | ✅ 改为 useDeviceStatusPolling + useDeviceStatus |

### 3.2 待规划

| 编号 | 偏差 | 影响 | 建议 |
|------|------|------|------|
| D1 | **DeviceFloatingPanel main 仍用 VNCViewShared** | 未统一到 createVncTransport 路径，main 与 vm_user 双轨 | 规划将 main 迁移到 AgentDesktopView 或 DeviceDesktopView；或实现 P4-17 将 vncStream 作为 createVncTransport 共享模式 |

### 3.3 设计未明确但实现合理

| 编号 | 实现 | 说明 |
|------|------|------|
| R1 | useVnc 接收 containerRef | 设计写 rfbOptions，实际 RFB 需 DOM 挂载点，containerRef 合理 |
| R2 | VncConnectionOverlay 抽取 | 设计未要求，但减少重复，符合 DRY |
| R3 | DeviceDesktopView 的 displayNum | 设计未提，用于 vm_user 的 UI 展示，合理 |
| R4 | vncStream clipViewport: false | frame capture 需要完整 framebuffer，合理 override |

### 3.4 未完成任务（设计已列出）

| 编号 | 任务 | 状态 |
|------|------|------|
| P4-17 | vncStream 重构为 createVncTransport 共享模式 | 未实现 |
| P4-18 | DeviceSidebar | 按需，未实现 |
| P4-19 | DeviceFloatingPanel 完善 | D2、D3 已修复；main 仍待 P4-17 后统一 |

---

## 四、代码 diff 与设计一致性

### 4.1 已删除文件（符合设计）

- `useVNCConnection.ts` ✅
- `useDeviceVNCConnection.ts` ✅
- `VNCView.tsx` ✅
- `VmUserVNCView.tsx` ✅

### 4.2 新增文件（符合设计）

- `vncTransport.ts` ✅ createVncTransport
- `useVnc.ts` ✅ 通用会话 hook
- `VncCanvas.tsx` ✅ 纯展示
- `AgentDesktopView.tsx` ✅
- `DeviceDesktopView.tsx` ✅
- `VncConnectionOverlay.tsx` ✅（设计未要求，合理优化）
- `useAgentDevice.ts` ✅（Phase 1）
- `vncBridge.ts` ✅（OTA Bridge）
- `types/vnc.ts` ✅ VncTarget、RFB_OPTIONS

### 4.3 修改文件与设计对照

| 文件 | 修改方向 | 与设计一致性 |
|------|----------|--------------|
| DeviceVNCView | Linux→DeviceDesktopView，Android→Scrcpy | ✅ |
| VisualPanel | VNCView→AgentDesktopView，agent.devices→useAgentDevice | ✅ |
| DeviceManagerPage | VmUserVNCView→DeviceDesktopView | ✅ |
| DeviceFloatingPanel | vm_user→DeviceDesktopView，displayNum，pcClientId；useDeviceStatusPolling；VNCViewShared pcClientId | ✅ |
| VNCViewShared | 增加 pcClientId；subscribeToVNCStream 传第三参 | ✅ |
| Header | 移除 useVNCConnection | ✅ |
| config | VNC_RETRY_DELAY_MS 等 | ✅ |
| vm.ts | 移除 URL 日志 | ✅ |

---

## 五、结论与建议

### 5.1 设计符合度

- **传输层、会话层、展示层**：与设计一致。
- **业务层迁移**：VNCView、DeviceVNCView、VmUserVNCView 已按设计迁移。
- **已修复**：VNCViewShared pcClientId 传递；DeviceFloatingPanel 轮询收敛到 DeviceStatusStore。
- **待规划**：DeviceFloatingPanel main 仍用 VNCViewShared；P4-17 vncStream 重构。

### 5.2 建议修复优先级

1. ~~**P0**：VNCViewShared 调用 subscribeToVNCStream 时传入 device.pc_client_id（多 PC 路由）。~~ ✅ 已修复
2. ~~**P1**：DeviceFloatingPanel 轮询改为订阅 DeviceStatusStore。~~ ✅ 已修复
3. **P2**：规划 P4-17，将 main 迁移到 createVncTransport 路径，或实现 vncStream 共享模式。

### 5.3 设计文档更新建议

- 在 04-task-breakdown 中注明：DeviceFloatingPanel main 暂保留 VNCViewShared，待 P4-17 完成后再统一。
- 补充 VncConnectionOverlay、displayNum 等实现细节，便于后续维护。
