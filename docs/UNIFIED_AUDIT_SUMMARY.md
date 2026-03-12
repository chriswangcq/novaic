# UNIFIED_CURRENT_STATE_AND_RESEARCH.md 审核汇总

> 5 名 subagent 对综合版文档的逐条核对结果与已应用的修正。

---

## 一、审核结论总览

| 审核范围 | 负责人 | 结论 | 主要修正 |
|----------|--------|------|----------|
| Device 与 Binding | Subagent 1 | 正确 | 补充 api.devices.list(agentId) 404、devices.id vs pc_clients.device_id |
| AppInstance 与 my-devices | Subagent 2 | 正确 | 补充「VmControl 子进程」表述 |
| VNC maindesk/subuser | Subagent 3 | 部分错误 | VNCViewShared 不存在→VNCView；maindesk 区分 agentId/device.id |
| 前端组件与数据流 | Subagent 4 | 部分错误 | DeviceFloatingPanel/DeviceSidebar 尚未实现；useAgentBinding 不存在 |
| 后端 API 与文件索引 | Subagent 5 | 正确 | 补全路径（p2p/src/tunnel.rs 等） |

---

## 二、已应用的文档修正

### 2.1 Device 管理

- 补充：前端 `api.devices.list(agentId)` 会 404，应废弃并改用 `listForUser` + `getAgentBinding`
- 补充：`devices` 主键 `id`，`pc_clients` 主键 `device_id`；VNC proxy 使用物理 device_id

### 2.2 前端数据流

- DeviceFloatingPanel、DeviceSidebar：由「未渲染」改为「**尚未实现**」
- 问题描述：由「已实现但未接入」改为「尚未实现」

### 2.3 VNC 调用链

- 组件：VNCViewShared → **VNCView、DeviceVNCView**（区分 agent 场景与 device 场景）
- resource_id：maindesk 区分 VNCView 用 `currentAgentId`、DeviceVNCView 用 `device.id`

### 2.4 文件索引

- 删除：useAgentBinding.ts、DeviceFloatingPanel.tsx、DeviceSidebar.tsx、VNCViewShared.tsx（不存在）
- 补全：api.ts → `src/services/api.ts`，组件路径补全
- 后端：`p2p/tunnel.rs` → `p2p/src/tunnel.rs`，其他路径补全

### 2.5 AppInstance

- 数据流：补充「Tauri 主进程 setup → VmControl Cloud Bridge WS」

### 2.6 Gaps 5.4

- VNCViewShared → VNCView
- DeviceSidebar、DeviceFloatingPanel：由「是否接入或移除」改为「是否实现及如何接入」

---

## 三、审核报告文件索引

| 文件 | 内容 |
|------|------|
| `docs/UNIFIED_DEVICE_SECTION_AUDIT.md` | Device 与 Binding 逐条核对 |
| `docs/UNIFIED_APPINSTANCE_MYDEVICES_AUDIT.md` | AppInstance 与 my-devices 逐条核对 |
| `docs/UNIFIED_DOC_AUDIT_REPORT.md` | 前端组件与数据流审核 |
| （VNC、后端） | 由 subagent 直接返回，未单独落文件 |

---

## 四、无需修正的核对项（已确认正确）

- Device 按 User 组织，Agent 通过 Binding 引用
- list_by_agent、GET /api/agents/{id}/devices 不存在
- get_pc_client_manager 对 devices API 始终用第一个设备
- AppInstance 字段、my-devices 来源与返回结构
- current_device_id 未传导致 is_local 未生效
- find_vnc_target 逻辑（resource_id 含 ':' → subuser）
- 后端 socket/port 路径
- 前端 WebSocket 探测、轮询、RFB 参数差异
- api.ts → invoke、vmService.getVncTransport → vnc_proxy/vnc_bridge
- vnc_proxy 路径 ws://.../vnc/{device_id}/{agent_id}
