# VNC 统一优化 — 任务清单

> 基于 [02-expert-design.md](./02-expert-design.md) 拆分的可执行任务，按 Phase 组织。  
> 建议使用 `[ ]` / `[x]` 标记完成状态。

---

## Phase 1：Device 模型对齐（约 1-2 周）

### 1.1 后端命名规范

- [x] **P1-1** 将 `pc_clients` 表主键列 `device_id` 重命名为 `pc_client_id`（或新增 migration）
- [x] **P1-2** 在 Gateway API 响应中，my-devices、devices 等返回的物理机标识使用 `pc_client_id` 字段名
- [x] **P1-3** 在 vnc_proxy、vnc_urls、vnc_bridge 等 Rust 代码中，为「物理机标识」参数添加类型别名或注释，明确标注为 `pc_client_id`
- [x] **P1-4**（可选）VNC proxy 路径改为 `/vnc/{pc_client_id}/{resource_id}`；若短期不改，在注释中说明当前 `device_id` 实为 `pc_client_id`

### 1.2 前端类型与 Hook

- [x] **P1-5** 定义 `VncTarget` 类型（`pcClientId`, `resourceId`, `subjectType`, `deviceId`, `username?`）
- [x] **P1-6** 实现 `useAgentDevice(agentId)` hook：`getAgentBinding` → `devices.get`，返回 `{ binding, device, vncTarget, isLoading, error }`
- [x] **P1-7** 在 `useAgentDevice` 中根据 binding 派生 `vncTarget`（maindesk: `resourceId = device_id`；subuser: `resourceId = deviceId:username`）
- [x] **P1-8** 为 `useAgentDevice` 添加缓存/去重（同一 device_id 只请求一次 devices.get）

### 1.3 废弃 api.devices.list(agentId)

- [x] **P1-9** 移除或标记废弃 `api.devices.list(agentId)`，确保不再调用 `GET /api/agents/{id}/devices`
- [x] **P1-10** 查找所有使用 `api.devices.list(agentId)` 或 `agent.devices` 的代码，改为 `useAgentDevice` 或 `listForUser` + `getAgentBinding`
- [x] **P1-11** AgentDrawer 中，当用户选择某个 Agent 后，设备详情展示改用 `useAgentDevice(agentId)` 而非从 `deviceManagerDevices` 按 ID 查找

### 1.4 DeviceStatusStore

- [x] **P1-12** 创建 `DeviceStatusStore`（Zustand 或 Jotai atom），维护 `Map<deviceId, DeviceStatus>`
- [x] **P1-13** 实现统一的 status 轮询循环（间隔 5s），或接入 WebSocket 推送
- [x] **P1-14** 将 AgentDrawer、useVNCConnection、useDeviceVNCConnection 等处的独立 status 轮询迁移为订阅 `DeviceStatusStore`
- [x] **P1-15**（可选）VNC 连接期间将轮询间隔降为 3s（通过 store 的 subscription count 动态调整）

### Phase 1 验收

- [ ] 设备模型语义清晰，`device_id` / `pc_client_id` 在代码和文档中区分明确
- [ ] 前端获取 Agent 关联设备统一走 `useAgentDevice`
- [ ] status 轮询收敛到单一 store，无重复定时器

---

## Phase 2：AppInstance / 拓扑（约 0.5-1 周）

### 2.1 Gateway my-devices API

- [x] **P2-1** 修改 my-devices API：查询参数由 `current_device_id` 改为 `current_app_instance_id`
- [x] **P2-2** Gateway 通过 DeviceRegistry 根据 `current_app_instance_id` 查到对应 `pc_client_id`，在返回的 devices 中标记 `is_local`
- [x] **P2-3** 更新 my-devices 的 API 文档和类型定义

### 2.2 前端 app_instance_id 全局存储

- [x] **P2-4** 在 Tauri setup 阶段获取 `app_instance_id`（通过 `get_app_instance` 或现有 AppInstance 状态）
- [x] **P2-5** 将 `app_instance_id` 存入全局 atom/context，供全应用访问
- [x] **P2-6** 在 `get_vnc_proxy_url`、`vnc_bridge_connect` 的调用链中传入 `current_app_instance_id`，构造 my-devices 请求时带上该参数

### 2.3 多 PC 路由修复

- [x] **P2-7** 修改 `get_pc_client_manager` 或等效逻辑，支持通过 `pc_client_id`（或 `VncTarget.pcClientId`）显式指定目标 PC
- [x] **P2-8** devices API（start/stop/status 等）在需要时传入目标 `pc_client_id`，而非始终用第一个设备

### Phase 2 验收

- [ ] 调用 my-devices 时传入 `current_app_instance_id`，`is_local` 正确生效
- [ ] 多 PC 场景下可指定目标设备进行路由

---

## Phase 3：VNC 后端统一（约 1-2 周）

### 3.1 VmControl ensure_vnc_endpoint

- [x] **P3-1** 在 p2p 中实现 `ensure_vnc_endpoint(resource_id) -> Result<SocketPath>`（vmcontrol/tunnel 共用）
- [x] **P3-2** maindesk 分支：直接返回 QEMU VNC socket 路径 `/tmp/novaic/novaic-vnc-{vm_id}.sock`
- [x] **P3-3** subuser 分支：轮询等待 port 文件 `/tmp/novaic/share-{vm_id}/vnc-{username}.port` 出现（最多 30s，间隔 500ms）
- [x] **P3-4** subuser 分支：读取 port 后建立 Unix socket 代理 `/tmp/novaic/vnc-{vm_id}-{username}.sock`，转发到 TCP
- [x] **P3-5** 失败时返回明确错误（Xvnc 未启动、超时等），便于上层区分处理

### 3.2 tunnel.rs 简化

- [x] **P3-6** 将 `find_vnc_target` 简化为调用 `ensure_vnc_endpoint(resource_id)`，拿到 socket path 后做通用 Unix 流转发
- [x] **P3-7** 移除 `if resource_id.contains(':')` 等 maindesk/subuser 分支逻辑
- [x] **P3-8** 确保 tunnel 层只做「根据 resource_id 查 socket → 转发」，不再感知 subject 类型

### 3.3 RFB 参数统一

- [x] **P3-9** 确定 RFB 参数统一方案：前端统一 `RFB_OPTIONS`
- [x] **P3-10** 统一参数：`shared: true`、`wsProtocols: ['binary']`、`credentials`、`clipViewport: true`

### Phase 3 验收

- [x] maindesk 与 subuser 走同一套 VNC 入口，tunnel 无类型分支
- [x] subuser 连接可靠性提升（内部等待 port 文件）
- [x] RFB 参数一致

---

## Phase 4：前端 VNC 收敛（约 1-2 周）

### 4.1 传输层 createVncTransport

- [x] **P4-1** 实现 `createVncTransport(target: VncTarget)`：根据 `pcClientId` 判断本机/远程，返回 WebSocket 或等效双向流
- [x] **P4-2** 本机：`ws://localhost:{port}/vnc/{pc_client_id}/{resource_id}`（vnc_proxy）
- [x] **P4-3** 远程：VNC Bridge（Cloud Relay）或 P2P QUIC，逻辑从 `vmService.getVncTransport` 迁移
- [x] **P4-4** 将 `vncBridge.shouldUseVncBridge` 合并进 `createVncTransport` 内部
- [x] **P4-5** P2P vs Cloud Bridge 选择逻辑放入 `createVncTransport`，通过 my-devices 拓扑判断

### 4.2 通用层 useVnc + VncCanvas

- [x] **P4-6** 实现 `useVnc(transport, rfbOptions)`：管理 VNC 会话生命周期（连接、重连、断开、状态上报）
- [x] **P4-7** 统一重连策略：断开后 2s 重试，最多 5 次，指数退避
- [x] **P4-8** 统一状态：`connecting | connected | disconnected | reconnecting | failed`
- [x] **P4-9** 实现 `<VncCanvas>` 纯展示组件：接收 vnc 会话对象，渲染画面、处理输入事件
- [x] **P4-10** 取消前端 WebSocket 探测，依赖后端 `ensure_vnc_endpoint`；连接前可用 `useDeviceStatus` 轮询 status

### 4.3 业务层组件

- [x] **P4-11** 实现 `<AgentDesktopView agentId={...}>`：`useAgentDevice` → `createVncTransport` → `useVnc` → `<VncCanvas>`
- [x] **P4-12** 实现 `<DeviceDesktopView deviceId={...} subjectType={...} subjectId={...}>`：直接构造 VncTarget，跳过 binding 查询
- [x] **P4-13** 迁移 VNCView 到 `<AgentDesktopView>`
- [x] **P4-14** 迁移 DeviceVNCView 到 `<DeviceDesktopView>` 或 `<AgentDesktopView>`（视场景）
- [x] **P4-15** 迁移 VmUserVNCView 到 `<AgentDesktopView>` 或 `<DeviceDesktopView>`
- [x] **P4-16** 删除 `useVNCConnection`、`useDeviceVNCConnection`
- [ ] **P4-17** 重构 `vncStream`：作为 `createVncTransport` 的共享模式（引用计数 + 连接复用）

### 4.4 DeviceSidebar / DeviceFloatingPanel（按需）

- [ ] **P4-18** 根据产品需求决定是否实现 DeviceSidebar：数据源 `listForUser()` + my-devices 拓扑
- [ ] **P4-19** 根据产品需求决定是否实现 DeviceFloatingPanel：Popover + `useAgentDevice`

### Phase 4 验收

- [ ] 三个 VNC View 收敛为 `<AgentDesktopView>` / `<DeviceDesktopView>`
- [ ] 传输层、会话层、展示层职责清晰
- [ ] 代码量减少约 40-50%，maindesk/subuser 行为一致

---

## 依赖关系

```
Phase 1 ─┬─→ Phase 2（可并行）
         └─→ Phase 3（可并行）
                  └─→ Phase 4（依赖 Phase 3）
```

---

## 任务统计

| Phase | 任务数 | 预估周期 |
|-------|--------|----------|
| Phase 1 | 15 | 1-2 周 |
| Phase 2 | 8 | 0.5-1 周 |
| Phase 3 | 10 | 1-2 周 |
| Phase 4 | 19 | 1-2 周 |
| **合计** | **52** | **4-6 周** |
