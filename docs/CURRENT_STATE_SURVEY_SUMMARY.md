# NovAIC 当前状态调研总结

> 三轮调研（浅→中→深），每轮 6 名 subagent，共 18 份子报告。汇总 P2P、Device 管理、App Instance、VNC/Relay、Agent-Device、Gateway 等各领域现状。

---

## 一、P2P

### 1.1 架构概览

| 组件 | 位置 | 职责 |
|------|------|------|
| **P2pClient** | p2p/client.rs | connect（relay）、connect_direct（本地） |
| **P2pServer** | p2p/server.rs | STUN → QUIC bind → heartbeat → accept |
| **relay** | p2p/relay.rs | connect_via_relay、connect_via_relay_only |
| **tunnel** | p2p/tunnel.rs | run_tunnel_server、open_vnc_stream、open_scrcpy_stream |
| **vnc_endpoint** | p2p/vnc_endpoint.rs | ensure_vnc_endpoint（maindesk/subuser 统一） |

**打洞已移除**：远端仅走 relay，`hole_punch::punch_and_connect` 已删除。

### 1.2 连接路径

| 场景 | 路径 |
|------|------|
| 手机远端 VNC | serve_remote_vnc → get_or_create_remote_conn → P2pClient::connect → connect_via_relay_only → relay_request + connect_via_relay → open_vnc_stream |
| PC 入站 relay | CloudBridge ConnectRelay → connect_via_relay → run_tunnel_server → accept_bi → handle_incoming_stream |
| 本地 VNC | serve_local_vnc → connect_direct → hole_punch::connect_to_peer → open_vnc_stream |

### 1.3 已知竞态与缺口（Round3）

| ID | 问题 | 严重度 |
|----|------|--------|
| R1/R5 | 推送无 ACK、无重试，PC 断连时静默丢失 | 高 |
| R2 | 手机立即 connect vs PC 建连耗时（5–15s） | 高 |
| R4 | PC 重试无 session 刷新，session 过期后重试无效 | 高 |
| R3 | Relay 等待 10s 可能不足 | 中 |
| E1 | invoke 失败无 .catch，用户无提示 | 高 |
| E2 | RFB 不暴露 close reason | 中 |

---

## 二、Device 管理

### 2.1 数据流

```
Gateway → Tauri gateway_get/post → api.devices
  → listForUser: AgentDrawer, DeviceManagerPage, DeviceManagerModal
  → devices.get: useAgentBinding, useDeviceVncTarget, DeviceManagerPage
  → start/stop/status: DeviceManagerPage, DeviceFloatingPanel, DeviceVNCView
```

### 2.2 组件与数据源（P1 改造后）

| 组件 | 设备详情来源 | Agent 依赖 |
|------|--------------|------------|
| **DeviceManagerPage** | listForUser.find + devices.get | 无 |
| **DeviceFloatingPanel (Agent 模式)** | useAgentBinding → devices.get | 强依赖 |
| **DeviceFloatingPanel (deviceMode)** | useDeviceVncTarget → devices.get | 无 |

### 2.3 DeviceStatusStore 与轮询

- **Store**：`statuses: Map<deviceId, DeviceStatusEntry>`，key 仅 deviceId
- **轮询**：useDeviceStatusPolling，5s/3s（有 VNC 时 3s）
- **调用方**：AgentDrawer、DeviceFloatingPanel；**DeviceManagerPage 不调用**

### 2.4 已知问题（Round3）

| 问题 | 影响 |
|------|------|
| DeviceManagerPage 无轮询 | drawer 关闭后状态不再更新，退化为 listForUser 30s 缓存 |
| 多 PC 覆盖 | Store key 仅 deviceId，同一设备多 pc_client_id 会互相覆盖 |
| useDeviceVncTarget 未接入 | 仅 DeviceFloatingPanel deviceMode 使用，DeviceManagerPage 未用 |

**修复建议**：P0 DeviceManagerPage 自驱动 useDeviceStatusPolling；P0 Store 支持 (deviceId, pcClientId) 复合 key。

**已修复（2026-03-12）**：DeviceManagerPage 已添加 useDeviceStatusPolling；DeviceStatusStore 已支持复合 key；DeviceFloatingPanel 已接入 ChatPanel；Scrcpy 30s 超时已发送 Close reason；app_instance 已提前在 mount 时获取。

---

## 三、App Instance 管理

### 3.1 定义与生命周期

| 项目 | 说明 |
|------|------|
| **含义** | 一次应用运行实例的 UUID，生命周期等于进程 |
| **生成** | Tauri setup.rs，`AppInstance::new_desktop()` / `new_mobile()` |
| **存储** | Rust AppInstanceState、前端 useAppStore.appInstanceId、Gateway DeviceRegistry |

### 3.2 使用场景

- **my-devices**：`current_app_instance_id` → `get_device_by_app_instance_id` → current_pc_client_id → 标注 is_local
- **Cloud Bridge**：连接时 `x-app-instance-id` header 建立 app_instance ↔ device_id 映射
- **resolveCurrentPcClientId**：多 PC 时选 is_local 设备，无则退化为 devices[0]

### 3.3 失败场景（Round3）

| 场景 | 降级行为 |
|------|----------|
| 前端 appInstanceId 未同步 | resolveCurrentPcClientId 返回 undefined → Modal 报错 |
| Cloud Bridge 未连接 | 无 is_local，退化为取第一个设备 |
| 未传 current_app_instance_id | Gateway 不标 is_local |

---

## 四、VNC / Relay

### 4.1 连接决策

| 决策点 | 位置 | 结果 |
|--------|------|------|
| OTA vs WebSocket | createVncTransport | window.isSecureContext → VncBridgeTransport |
| 本机 vs 远程 | vnc_proxy::route_vnc | device_id == local_id → serve_local_vnc |
| 本地 QUIC | get_or_create_local_conn | connect_direct(127.0.0.1:19998) |
| 远程 QUIC | get_or_create_remote_conn | P2pClient::connect → relay |

### 4.2 ensure_vnc_endpoint

- **maindesk**：`novaic-vnc-{resource_id}.sock`
- **subuser**：轮询 port 文件（最多 30s）→ 创建 Unix 代理

### 4.3 稳定性（Round3）

**已修复**：P0-2 超时 Close reason、P0-3 transportError Retry、vncStream 重试 5 次指数退避、createVncTransport 30s 超时。

**已知问题**：Scrcpy 30s 超时无 Close reason；远端 + subuser 场景 30s 可能不足。

---

## 五、Agent-Device Binding

### 5.1 数据流

```
agentId → getAgentBinding → AgentDeviceBinding
  → devices.get(device_id) → Device
  → bindingToVncTarget(binding, device) → VncTarget
  → createVncTransport → VncBridge / WebSocket
```

### 5.2 依赖组件

| 组件 | 数据源 | 用途 |
|------|--------|------|
| AgentDesktopView | useAgentDevice | VNC 主桌面 |
| VisualPanel | useAgentDevice | 设备类型判断 |
| AgentDrawer | useAgentDevice | Devices tab 高亮 |
| DeviceFloatingPanel | useAgentBinding | Agent 模式设备浮层 |
| SettingsModal | setAgentBinding/clearAgentBinding | 设备绑定配置 |

---

## 六、Gateway API

### 6.1 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| agents | /api/agents | CRUD、binding、model |
| devices | /api/devices | list、get、start、stop、status |
| vm | /api/vm | start、stop、status（agent_id） |
| p2p | /api/p2p | heartbeat、relay-request、my-devices |
| internal | /internal | pc/ws、subagents、agents（仅本机） |

### 6.2 vm/start vs devices/start

| 维度 | vm/start | devices/start |
|------|----------|---------------|
| 主参数 | agent_id | device_id（path） |
| 多 PC | 不支持 | 支持 pc_client_id 查询参数 |
| 语义 | Agent 维度 | Device 维度 |

### 6.3 Gateway vs Tauri 职责

| 领域 | Gateway | Tauri |
|------|---------|-------|
| VNC 路由 | 不参与 | 全权 |
| Relay | relay-request、validate | 实际 connect_via_relay |
| VM 启动 | 编排、转发 | VmControl 执行 |

---

## 七、DeviceFloatingPanel 接入现状（Round3）

| 项目 | 现状 |
|------|------|
| **渲染** | **未接入**：LayoutContainer、AgentDrawer、ChatPanel 均未渲染 |
| **deviceMode** | 无传入方（组件 orphaned） |
| **设计** | HANDOVER 中为 ChatPanel 右上角浮层 |

**建议**：P0 在 ChatPanel 内渲染 `<DeviceFloatingPanel compact />`（Agent 模式）。

---

## 八、调研文档索引

| 轮次 | 领域 | 文档 |
|------|------|------|
| R1 | P2P | docs/P2P_ARCHITECTURE_SURVEY_ROUND1.md |
| R1 | Device | docs/DEVICE_DATAFLOW_RESEARCH_ROUND1.md |
| R1 | App Instance | docs/RESEARCH_APP_INSTANCE_OVERVIEW.md |
| R1 | VNC/Relay | docs/VNC_RELAY_CONNECTION_FLOW_DIAGRAM.md |
| R1 | Agent-Device | （subagent 内联输出） |
| R1 | Gateway | （subagent 内联输出） |
| R2 | P2P relay/tunnel | docs/RESEARCH_P2P_RELAY_TUNNEL_DETAILS.md |
| R2 | DeviceStatusStore | docs/DEVICE_STATUS_STORE_POLLING_RESEARCH_ROUND2.md |
| R2 | app_instance-my-devices | docs/RESEARCH_APP_INSTANCE_MYDEVICES_LINKAGE.md |
| R2 | vnc_proxy 路由 | docs/VNC_PROXY_ROUTING_CODE_PATH.md |
| R2 | connect_relay | docs/RESEARCH_CONNECT_RELAY_FLOW.md |
| R2 | Device-Agent 解耦 | docs/DEVICE_AGENT_DECOUPLE_DATAFLOW_RESEARCH_ROUND2.md |
| R3 | P2P 竞态 | docs/P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md |
| R3 | Device 竞态 | docs/DEVICE_STATUS_RACE_MULTI_PC_RESEARCH_ROUND3.md |
| R3 | app_instance 失败 | docs/RESEARCH_APP_INSTANCE_SYNC_AND_FAILURE_SCENARIOS.md |
| R3 | VNC 稳定性 | docs/VNC_STABILITY_RECONNECT_RESEARCH_ROUND3.md |
| R3 | DeviceFloatingPanel | docs/DEVICE_FLOATING_PANEL_DEVICEMODE_RESEARCH_ROUND3.md |
| R3 | Gateway 职责 | docs/GATEWAY_VS_TAURI_RESPONSIBILITY_BOUNDARY_RESEARCH_ROUND3.md |
