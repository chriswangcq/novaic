# Phase 4 VNC 收敛 — API 一致性与向后兼容性审核报告

**审核日期**：2025-03-12  
**审核范围**：createVncTransport、vmService.getVncTransport、get_vnc_proxy_url 调用关系；VncTarget/VncTransport 类型；useVNCConnection/useDeviceVNCConnection 迁移；vncStream、VNCViewShared 与 Phase 4 新实现的兼容性

---

## 一、审核结论摘要

| 类别 | 数量 |
|------|------|
| Critical（严重） | 3 |
| High（高） | 5 |
| Medium（中） | 4 |
| Low（低） | 2 |

---

## 二、问题列表

### Critical（严重）

#### C1. VNCViewShared 未迁移，仍使用 vncStream + vmService.getVncTransport，且未传 pcClientId

**文件**：`novaic-app/src/components/Visual/VNCViewShared.tsx`、`novaic-app/src/components/Layout/DeviceFloatingPanel.tsx`

**描述**：
- DeviceFloatingPanel 对 main subject_type 使用 `VNCViewShared`，而非 Phase 4 的 `DeviceDesktopView` 或 `AgentDesktopView`
- VNCViewShared 依赖 `vncStream.subscribeToVNCStream(streamKey, subscriber)`，内部调用 `vmService.getVncTransport(agentId, deviceId)`
- **关键问题**：`subscribeToVNCStream(agentId, subscriber, deviceId?)` 的第三个参数 `deviceId`（即 pcClientId）从未传入
- VNCViewShared 调用：`subscribeToVNCStream(streamKey, { onFrame, onStatusChange, onError })`，仅 2 个参数
- DeviceFloatingPanel 有 `device.pc_client_id`，但 VNCViewShared 不接受 pcClientId prop，无法传递

**影响**：多 PC 场景下，maindesk 的 VNC 路由错误，可能连到错误的物理机。

**建议**：
1. 将 DeviceFloatingPanel 的 main 分支迁移为 `DeviceDesktopView subjectType="main" device={device}`，与 vm_user 分支一致
2. 或：VNCViewShared 增加 `pcClientId?: string` prop，并传给 `subscribeToVNCStream(streamKey, subscriber, pcClientId)`

---

#### C2. vncStream 与 createVncTransport 双轨并存，API 不一致

**文件**：`novaic-app/src/services/vncStream.ts`、`novaic-app/src/services/vncTransport.ts`

**描述**：
- Phase 4 设计：`createVncTransport(VncTarget)` 统一传输层，参数为 `resourceId`、`pcClientId`
- vncStream 仍使用 `vmService.getVncTransport(agentId, deviceId)`，参数语义为 agentId + 可选 deviceId
- 两套 API 语义一致（agentId=resourceId, deviceId=pcClientId），但 vncStream 的 `connectStream(agentId, deviceId?)` 在多数调用路径未传 deviceId
- `reconnectVNCStream(agentId)` 无 deviceId 参数，重连时丢失 pcClientId

**影响**：维护两套传输获取逻辑，易产生行为差异；vncStream 路径多 PC 路由不可靠。

**建议**：
1. 将 vncStream 内部改为使用 `createVncTransport(buildVncTargetFromStreamKey(streamKey, pcClientId))`，或
2. 按 P4-17 计划，将 vncStream 重构为 createVncTransport 的共享模式，彻底统一

---

#### C3. DeviceFloatingPanel 注释与实现不符（VmUserVNCView 已删除）

**文件**：`novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` 第 5 行

**描述**：注释写 `main → VNCViewShared, vm_user → VmUserVNCView`，实际 vm_user 已改为 `DeviceDesktopView`。VmUserVNCView 若已删除，注释会误导后续维护。

**影响**：低（仅文档），但需修正以保持一致性。

**建议**：更新注释为 `main → VNCViewShared, vm_user → DeviceDesktopView`。

---

### High（高）

#### H1. get_vnc_proxy_url 参数映射：createVncTransport 正确，vncStream 路径缺失 pcClientId

**文件**：`novaic-app/src-tauri/src/commands/vnc_urls.rs`、`novaic-app/src/services/vncTransport.ts`

**描述**：
- Tauri `get_vnc_proxy_url(agentId, deviceId?)`：agentId = resource_id（maindesk: device_id；subuser: `${deviceId}:${username}`），deviceId = pc_client_id
- `createVncTransport` 正确传入：`{ agentId: resourceId, deviceId: pcClientId ?? null }`
- vncStream 路径：`vmService.getVncTransport(agentId, deviceId)`，但 VNCViewShared 未传 deviceId，导致 pcClientId 为 undefined

**影响**：createVncTransport 路径正确；vncStream 路径多 PC 时错误。

**建议**：同 C1、C2。

---

#### H2. VNCViewShared 与 AgentDesktopView 功能差异，未统一

**文件**：`novaic-app/src/components/Visual/VNCViewShared.tsx`、`novaic-app/src/components/Visual/AgentDesktopView.tsx`

**描述**：

| 特性 | VNCViewShared | AgentDesktopView |
|------|---------------|------------------|
| 传输 | vncStream（共享连接、帧复制） | createVncTransport（独立连接） |
| 缩略图 | 支持（isThumbnail，copyFrame） | 无 |
| 全屏 | attachVNCContainer 附加 RFB | 直接渲染 VncCanvas |
| viewOnly | setVNCViewOnly(streamKey, vncLocked) | options.viewOnly |
| 启动 VM | vmService.start(agentId) | 无（依赖 useAgentDevice） |
| 数据源 | agentId + deviceId props | agentId → useAgentDevice |

VNCViewShared 的设计目的是「多组件共享同一 VNC 连接」（缩略图 + 全屏切换不重连）。AgentDesktopView 无此特性。若将 DeviceFloatingPanel main 迁移为 DeviceDesktopView，需确认：展开/收起时是否会重复建连（可能影响体验）。

**影响**：两套实现行为不同，需产品决策是否统一或保留 VNCViewShared 的共享场景。

**建议**：
1. 若统一：DeviceDesktopView 需支持「共享连接」模式（如 P4-17 的 createVncTransport 引用计数），或接受展开时重连
2. 若保留：VNCViewShared 增加 pcClientId 支持，修复多 PC 路由

---

#### H3. setVNCViewOnly 与 vncStream 的 agentId 语义

**文件**：`novaic-app/src/hooks/useLayout/DeviceFloatingPanel.tsx`、`novaic-app/src/services/vncStream.ts`

**描述**：`setVNCViewOnly(device.id, !operating)` 使用 device.id 作为 stream key。对 maindesk，device.id = resourceId，与 streamKey 一致。但 `setVNCViewOnly` 的注释写的是 agentId，实际为 resourceId（maindesk 时 device_id）。语义混用。

**影响**：低，但命名易混淆。

**建议**：在 vncStream 或 VNCViewShared 注释中明确：streamKey 在 maindesk 时为 device_id（= resourceId）。

---

#### H4. VncTransport 类型未从 types/index 统一导出

**文件**：`novaic-app/src/types/index.ts`、`novaic-app/src/services/vncTransport.ts`

**描述**：
- `types/index.ts` 导出 `VncTarget`、`RFB_OPTIONS`
- `VncTransport` 仅在 `vncTransport.ts` 定义，各模块需 `import type { VncTransport } from '../../services/vncTransport'`
- 其他模块（VncCanvas、useVnc、AgentDesktopView、DeviceDesktopView）均从 vncTransport 直接导入，无问题
- 若未来有模块从 types 导入，会找不到 VncTransport

**影响**：当前无问题；但类型导出分散，不利于统一入口。

**建议**：在 `types/index.ts` 或 `types/vnc.ts` 中 re-export `VncTransport`，或保持现状并文档化「VncTransport 从 vncTransport 导入」。

---

#### H5. vmService.getVncTransport 与 createVncTransport 并存，向后兼容性风险

**文件**：`novaic-app/src/services/vm.ts`、`novaic-app/src/services/vncTransport.ts`

**描述**：
- `vmService.getVncTransport(agentId, deviceId?)` 仍被 vncStream 使用
- Phase 4 新组件使用 `createVncTransport(VncTarget)`
- 若未来删除 vmService.getVncTransport，需确保 vncStream 已迁移

**影响**：当前无问题；删除前需完成 vncStream 迁移。

**建议**：在 vm.ts 的 getVncTransport 上添加 `@deprecated` 注释，注明「请使用 createVncTransport(VncTarget)，vncStream 迁移后移除」。

---

### Medium（中）

#### M1. useVNCConnection、useDeviceVNCConnection 已删除，无遗留调用方

**结论**：✅ 无遗漏

**验证**：`grep -r "useVNCConnection\|useDeviceVNCConnection" novaic-app/src` 无匹配。两 hook 已删除，且无调用方引用。

---

#### M2. DeviceVNCView 已迁移至 DeviceDesktopView

**文件**：`novaic-app/src/components/Visual/DeviceVNCView.tsx`

**描述**：DeviceVNCView 对 Linux 分支已使用 `DeviceDesktopView subjectType="main" device={device}`，迁移正确。Android 分支使用 ScrcpyView，与 VNC 无关。

**结论**：✅ 正确

---

#### M3. 类型 VncTarget 导出完整

**文件**：`novaic-app/src/types/index.ts`、`novaic-app/src/types/vnc.ts`

**描述**：`VncTarget` 从 types/vnc 定义，经 types/index 导出。useAgentDevice、DeviceDesktopView、vncTransport 等均能正确 import。

**结论**：✅ 正确

---

#### M4. get_vnc_proxy_url 的 agentId/deviceId 与 resourceId/pcClientId 映射正确

**文件**：`novaic-app/src-tauri/src/commands/vnc_urls.rs`、`novaic-app/src/services/vncTransport.ts`

**描述**：
- Rust：agentId = resource_id（maindesk: device_id；subuser: `${deviceId}:${username}`），deviceId = pc_client_id
- createVncTransport：`{ agentId: resourceId, deviceId: pcClientId ?? null }` ✓
- vnc_proxy ws_url：`/vnc/{pc_client_id}/{resource_id}` ✓

**结论**：createVncTransport 路径映射正确。

---

### Low（低）

#### L1. VncBridgeTransport 的 agentId/deviceId 与 VncTarget 的 resourceId/pcClientId 命名不一致

**文件**：`novaic-app/src/services/vncBridge.ts`、`novaic-app/src/services/vncTransport.ts`

**描述**：VncBridgeTransport 构造函数参数为 `(agentId, deviceId)`，createVncTransport 传入 `(resourceId, pcClientId)`。语义一致，但命名不一致，可能增加理解成本。

**建议**：在 vncTransport 或 vncBridge 注释中说明：agentId = resourceId，deviceId = pcClientId。

---

#### L2. reconnectVNCStream 缺少 deviceId 参数

**文件**：`novaic-app/src/services/vncStream.ts` 第 447–451 行

**描述**：`reconnectVNCStream(agentId)` 内部调用 `connectStream(agentId)`，未传 deviceId。若 stream 建立时曾传 deviceId，重连时丢失。

**影响**：vncStream 的 subscribeToVNCStream 当前也未传 deviceId，故重连时行为一致（都缺 pcClientId）。但若修复 H1 后，subscribe 传入 deviceId，需在 connectStream 中持久化该参数，供 reconnect 使用。

**建议**：在 StreamState 中存储 `pcClientId?: string`，connectStream 和 reconnectVNCStream 使用该值。

---

## 三、调用关系汇总

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 4 新路径（createVncTransport）                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ AgentDesktopView → useAgentDevice → createVncTransport → useVnc → VncCanvas  │
│ DeviceDesktopView → buildVncTarget → createVncTransport → useVnc → VncCanvas │
│ DeviceVNCView (Linux) → DeviceDesktopView                                     │
│ createVncTransport → invoke('get_vnc_proxy_url', { agentId: resourceId,       │
│                    deviceId: pcClientId ?? null })                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 遗留路径（vncStream + vmService.getVncTransport）                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ DeviceFloatingPanel (main) → VNCViewShared → subscribeToVNCStream(streamKey)  │
│   → connectStream(agentId) [deviceId 未传!]                                   │
│   → vmService.getVncTransport(agentId, deviceId)                             │
│   → invoke('get_vnc_proxy_url', { agentId, deviceId })                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、修复优先级建议

### 立即修复（Critical）

1. **C1**：DeviceFloatingPanel main 迁移为 DeviceDesktopView，或 VNCViewShared 增加 pcClientId 并传给 vncStream
2. **C2**：规划 vncStream 迁移至 createVncTransport，或至少修复 pcClientId 传递
3. **C3**：更新 DeviceFloatingPanel 注释

### 短期修复（High）

4. **H2**：明确 VNCViewShared 与 AgentDesktopView 的定位与取舍
5. **H4**：统一 VncTransport 类型导出（可选）
6. **H5**：为 vmService.getVncTransport 添加 @deprecated

### 中期优化（Medium）

7. **M1–M4**：已确认无问题

### 低优先级（Low）

8. **L1**：补充命名映射注释
9. **L2**：vncStream 支持 pcClientId 持久化（若保留 vncStream）

---

## 五、附录：文件清单

| 文件 | 角色 |
|------|------|
| `novaic-app/src/services/vncTransport.ts` | createVncTransport（Phase 4 统一入口） |
| `novaic-app/src/services/vm.ts` | getVncTransport、getVncUrl（遗留，vncStream 使用） |
| `novaic-app/src/services/vncStream.ts` | 共享连接、VNCViewShared 依赖 |
| `novaic-app/src/services/vncBridge.ts` | VncBridgeTransport（OTA 模式） |
| `novaic-app/src/components/Visual/VNCViewShared.tsx` | 使用 vncStream，未迁移 |
| `novaic-app/src/components/Visual/AgentDesktopView.tsx` | Phase 4，createVncTransport |
| `novaic-app/src/components/Visual/DeviceDesktopView.tsx` | Phase 4，createVncTransport |
| `novaic-app/src/components/Visual/DeviceVNCView.tsx` | 已迁移，使用 DeviceDesktopView |
| `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | main→VNCViewShared，vm_user→DeviceDesktopView |
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url |
| `novaic-app/src/types/vnc.ts` | VncTarget 定义 |
