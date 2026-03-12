# NovAIC 2026 三轮调研统一总结报告

> **产出日期**: 2026-03-12  
> **输入**: docs/survey-2026/ 下所有 ROUND1、ROUND2 文档；docs/ 下 Round3 调研文档；docs/unify-vnc/P2P-RACE-IMPLEMENTATION-PLAN-R3.md

---

## 一、各领域现状一览

### 1.1 P2P

| 维度 | 现状 |
|------|------|
| **架构** | P2pClient（relay/direct）、relay.rs（connect_via_relay_only）、tunnel.rs（VNC/Scrcpy 流）、rendezvous（relay_request、relay_refresh_for_pc、heartbeat）、vnc_endpoint（maindesk/subuser） |
| **打洞** | 已移除，远端仅走 relay |
| **连接路径** | 手机远端 VNC：relay_request → send_push_and_wait_ack → PC ACK → spawn connect_via_relay → run_tunnel_server；手机 sleep(2s) 后 connect_via_relay 配对 |
| **TTL 常量** | Gateway `_PENDING_SESSION_TTL_SECS=20`；Relay `SESSION_TTL=20`、`WAIT_FOR_PC_TIMEOUT=20`；relay.rs `INITIAL_DELAY_SECS=2` |
| **R4** | PC session 过期时调用 `relay_refresh_for_pc` 续期 |
| **R1/R5** | Gateway `send_push_and_wait_ack`（5s 超时）；PC 收 connect_relay 后先发 `connect_relay_ack` 再 spawn |

### 1.2 Device 管理

| 维度 | 现状 |
|------|------|
| **数据流** | Gateway → Tauri gateway_get/post → api.devices；listForUser、devices.get、start/stop/status |
| **组件** | DeviceManagerPage（listForUser + useDeviceStatusPolling）、DeviceFloatingPanel（useAgentBinding / useDeviceVncTarget）、AgentDrawer（listForUser） |
| **DeviceStatusStore** | `statuses: Map<statusKey, DeviceStatusEntry>`，key 为 `deviceId` 或 `deviceId:pcClientId`（复合 key） |
| **轮询** | useDeviceStatusPolling；5s/3s（有 VNC 时 3s）；调用方：DeviceManagerPage、DeviceFloatingPanel、AgentDrawer |
| **状态覆盖** | `useDeviceStatus(deviceId, pcClientId)` 覆盖 device.status，避免 listForUser 缓存滞后 |

### 1.3 App Instance

| 维度 | 现状 |
|------|------|
| **定义** | 进程级 UUID，每次 Tauri 启动生成，不持久化 |
| **存储** | Rust AppInstanceState、前端 useAppStore.appInstanceId、Gateway DeviceRegistry（x-app-instance-id header） |
| **使用** | my-devices 的 is_local 标注；resolveCurrentPcClientId（多 PC 选目标）；AddAndroidModal / AddLinuxVMUserModal 创建设备 |
| **同步** | App mount 时 `invoke('get_app_instance')` 异步写入 Store；Cloud Bridge 握手时写入 DeviceRegistry |

### 1.4 VNC / Relay

| 维度 | 现状 |
|------|------|
| **路由决策** | `route_vnc`：device_id == local → serve_local_vnc（QUIC loopback）；否则 serve_remote_vnc（relay） |
| **ensure_vnc_endpoint** | maindesk：QEMU socket；subuser：轮询 port 文件（30s）→ Unix 代理 |
| **Close reason** | vnc_proxy 各错误路径 send_ws_close_with_reason；VNC 30s 超时已发送；Scrcpy 30s 超时已发送 Close reason；noVNC patch 透传 reason |
| **重试** | vncStream 5 次指数退避；createVncTransport 30s 超时；transportError Retry 按钮 |

### 1.5 Agent-Device Binding

| 维度 | 现状 |
|------|------|
| **数据流** | agentId → getAgentBinding → devices.get → bindingToVncTarget → createVncTransport |
| **组件** | AgentDesktopView、VisualPanel、AgentDrawer、DeviceFloatingPanel（Agent 模式）、SettingsModal |
| **模式** | Agent 模式（useAgentBinding）；deviceMode（useDeviceVncTarget，传入 deviceId + subject） |

### 1.6 Gateway

| 维度 | 现状 |
|------|------|
| **核心模块** | agents、devices、vm、p2p、internal（pc_client、subagents 等） |
| **VNC 路由** | 不参与，Tauri vnc_proxy 全权 |
| **Relay** | relay-request、validate-relay-session、relay-refresh-for-pc；Tauri 实际 connect_via_relay |
| **VM 启动** | Gateway 编排、转发；Tauri VmControl 执行 |
| **vm/start vs devices/start** | vm/start 无 pc_client_id；devices/start 支持 pc_client_id |

---

## 二、已实施修复（2026-03-12）

| 领域 | 修复项 | 说明 |
|------|--------|------|
| **P2P** | R2/R3（20s TTL + 2s 手机延迟） | Gateway `_PENDING_SESSION_TTL_SECS=20`；Relay `SESSION_TTL=20`、`WAIT_FOR_PC_TIMEOUT=20`；relay.rs `INITIAL_DELAY_SECS=2` |
| **P2P** | R4（PC session 刷新） | Gateway `POST /api/p2p/relay-refresh-for-pc`；CloudBridge 失败且 is_session_error 时调用 refresh |
| **P2P** | R1/R5（推送 ACK） | Gateway `send_push_and_wait_ack`（5s）；PC 收 connect_relay 后先发 connect_relay_ack 再 spawn |
| **P2P** | E2（RFB Close Reason） | noVNC patch 透传 `_rfbCloseReason`；vnc_proxy 各错误路径 send_ws_close_with_reason |
| **Device** | DeviceManagerPage 轮询 | 已添加 useDeviceStatusPolling，自驱动，不依赖 AgentDrawer |
| **Device** | Store 复合 key | DeviceStatusStore 支持 `statusKey(deviceId, pcClientId)`，多 PC 状态隔离 |
| **Device** | DeviceFloatingPanel 接入 | 已接入 ChatPanel，`<DeviceFloatingPanel compact />`（Agent 模式） |
| **VNC** | 超时 Close reason | P0-2 VNC 30s 超时、P0-3 transportError Retry、vncStream 5 次指数退避、createVncTransport 30s 超时 |
| **VNC** | Scrcpy 30s 超时 | 已发送 Close reason |
| **App Instance** | 提前获取 | app_instance 在 mount 时获取，供 my-devices、resolveCurrentPcClientId 使用 |

---

## 三、剩余缺口汇总表

### 3.1 按领域

| 领域 | 缺口 ID | 描述 | 优先级 |
|------|---------|------|--------|
| **P2P** | R3 余量 | Relay 20s 等待在极端慢网下可能不足 | 中 |
| **P2P** | E1 | invoke 失败无 .catch，用户无提示（"Starting…" 一直转圈） | 高 |
| **P2P** | E4 | PC relay 失败无反馈到手机 | 中 |
| **P2P** | 并发 relay_request | 同一 target 快速双击可创建多 session，无去重 | 低 |
| **Device** | useAgentDevice 30s 缓存 | deviceCache 仅 deviceId，多 PC 同 device 可能读到错误缓存 | 中 |
| **Device** | listForUser 与 status 一致性 | 后端 listForUser status 缓存策略审查 | P1 |
| **Device** | DeviceManagerPage deviceMode | 未接入 DeviceFloatingPanel 的 deviceMode | P2 |
| **App Instance** | 双重异步 | appInstanceId 与 DeviceRegistry 无强一致保证；登录后快速操作可能失败 | 高 |
| **App Instance** | 错误提示 | resolveCurrentPcClientId 失败时「请选择目标 PC 或确保 Tauri 应用已连接」未区分根因 | 中 |
| **VNC** | 30s 可能不足 | 远端 + subuser 且 port 未就绪时，P2P(10–30s) + ensure_vnc_endpoint(0–30s) 易超时 | 中 |
| **VNC** | 错误文案 | "Connection lost, max retries exceeded" 等为英文 | 低 |
| **VNC** | 未覆盖场景 | ensure_vnc_endpoint subuser 30s 超时错误在 PC 侧，QUIC stream 直接结束，VncProxy 无具体 reason | 中 |
| **Gateway** | vm/start 多 PC | 无 pc_client_id，始终取第一个 | 中 |
| **DeviceFloatingPanel** | deviceMode 传入方 | 暂无调用方传入 deviceMode；DeviceManagerPage 未接入 | P2 |

### 3.2 按优先级

| 优先级 | 缺口 | 领域 | 建议 |
|--------|------|------|------|
| **P0** | E1 invoke 失败无 .catch | P2P | 所有 get_vnc_proxy_url / get_scrcpy_proxy_url 调用加 .catch() 并 setErrorMsg |
| **P0** | 双重异步 | App Instance | 登录后等待 appInstanceId 或 Modal 打开时重试 resolveCurrentPcClientId |
| **P1** | listForUser status 缓存 | Device | 后端审查 listForUser 的 status 来源与缓存策略 |
| **P1** | useAgentDevice 多 PC 缓存 | Device | 缓存 key 含 pc_client_id |

| **P2** | R3 余量 | P2P | 极端慢网可考虑 25s |
| **P2** | E4 PC relay 失败无反馈 | P2P | 设计 PC→Gateway→手机 的失败通知 |
| **P2** | 错误提示区分 | App Instance | 区分 appInstanceId 未同步 / Cloud Bridge 未连 / 设备列表为空 |
| **P2** | 30s 可能不足 | VNC | 远端 + subuser 场景考虑 WS_UPGRADE_TIMEOUT 延长至 60s |
| **P2** | ensure_vnc_endpoint 错误传播 | VNC | PC 侧超时错误通过 QUIC 协议传回 VncProxy |
| **P2** | vm/start 多 PC | Gateway | 增加 pc_client_id 或引导使用 devices/start |
| **P2** | DeviceManagerPage deviceMode | DeviceFloatingPanel | 按需接入 deviceMode 浮层预览 |

| **P3** | 并发 relay_request | P2P | 2s 内同 target 复用 session |
| **P3** | 错误文案中英混用 | VNC | 统一文案 |

---

## 四、建议实施顺序

### 4.1 短期（1–2 周）

1. **E1 invoke 失败 .catch**：覆盖所有 `get_vnc_proxy_url`、`get_scrcpy_proxy_url` 调用链，补 `.catch()` 并 `setErrorMsg`。
2. **App Instance 双重异步**：AddAndroidModal / AddLinuxVMUserModal 在 `resolveCurrentPcClientId` 返回 undefined 时，先等待 `appInstanceId` 或重试 1–2 次，再提示错误。
3. **listForUser 缓存审查**：后端确认 status 来源与 TTL，必要时缩短或改为实时查询。

### 4.2 中期（2–4 周）

4. **useAgentDevice 多 PC 缓存**：`deviceCache` 的 key 改为 `deviceId:pcClientId`，避免多 PC 同 device 缓存错乱。
5. **P2P E4**：设计 PC relay 失败时向手机反馈的机制（或手机端超时文案更明确）。
6. **VNC 30s 超时**：远端 + subuser 场景评估 WS_UPGRADE_TIMEOUT 延长至 60s，或按 `is_remote + subject_type` 动态设置。
7. **Gateway vm/start 多 PC**：增加 `pc_client_id` 参数或文档明确迁移到 devices/start。

### 4.3 长期（按需）

8. **DeviceManagerPage deviceMode**：在 Devices 视图时传入 `deviceMode`，实现设备浮层预览。
9. **ensure_vnc_endpoint 错误传播**：PC 侧 subuser 超时错误通过 QUIC 协议传回 VncProxy，再发送 Close reason。
10. **P2P 并发 relay_request**：2s 内同 target 复用 session，减少重复请求。

---

## 五、文档索引

### 5.1 调研文档（survey-2026）

| 轮次 | 领域 | 文档 |
|------|------|------|
| R1 | P2P | docs/survey-2026/P2P_ARCHITECTURE_ROUND1.md |
| R2 | P2P relay/tunnel | docs/survey-2026/P2P_RELAY_TUNNEL_ROUND2.md |
| R1 | Device | docs/survey-2026/DEVICE_MANAGEMENT_ROUND1.md |
| R2 | Device 多 PC | docs/survey-2026/DEVICE_STATUS_MULTIPC_ROUND2.md |
| R1 | App Instance | docs/survey-2026/APP_INSTANCE_ROUND1.md |
| R2 | App Instance 同步 | docs/survey-2026/APP_INSTANCE_SYNC_ROUND2.md |
| R1 | VNC/Relay | docs/survey-2026/VNC_RELAY_ROUND1.md |
| R2 | VNC 路由 | docs/survey-2026/VNC_PROXY_ROUTING_ROUND2.md |
| R1 | Agent-Device | docs/survey-2026/AGENT_DEVICE_BINDING_ROUND1.md |
| R1 | Gateway | docs/survey-2026/GATEWAY_API_ROUND1.md |
| R2 | Gateway 职责 | docs/survey-2026/GATEWAY_TAURI_BOUNDARY_ROUND2.md |
| R2 | DeviceFloatingPanel | docs/survey-2026/DEVICE_FLOATING_PANEL_ROUND2.md |

### 5.2 Round3 深层调研（survey-2026）

| 领域 | 文档 |
|------|------|
| P2P 缺口 | docs/survey-2026/P2P_GAPS_ROUND3.md |
| Device 缺口 | docs/survey-2026/DEVICE_GAPS_ROUND3.md |
| App Instance 缺口 | docs/survey-2026/APP_INSTANCE_GAPS_ROUND3.md |
| VNC 缺口 | docs/survey-2026/VNC_GAPS_ROUND3.md |
| DeviceFloatingPanel 缺口 | docs/survey-2026/DEVICE_FLOATING_PANEL_GAPS_ROUND3.md |

### 5.3 设计文档（unify-vnc）

| 文档 | 说明 |
|------|------|
| docs/unify-vnc/P2P-RACE-IMPLEMENTATION-PLAN-R3.md | P2P 竞态修复实施计划 |
| docs/unify-vnc/P2P-R1R5-PUSH-ACK-DESIGN-R2.md | R1/R5 ACK 设计 |
| docs/unify-vnc/P2P-R2R3-MOBILE-DELAY-RELAY-WAIT-DESIGN-R2.md | R2/R3 设计 |
| docs/unify-vnc/P2P-R4-PC-SESSION-REFRESH-DESIGN-R2.md | R4 设计 |
| docs/unify-vnc/P2P-E2-RFB-CLOSE-REASON-DESIGN-R2.md | E2 设计 |

### 5.4 汇总文档

| 文档 | 说明 |
|------|------|
| docs/CURRENT_STATE_SURVEY_SUMMARY.md | 三轮调研汇总（旧版） |
| docs/survey-2026/CURRENT_STATE_SURVEY_SUMMARY_2026.md | 本文档（2026 统一总结） |

---

*报告由 docs/survey-2026/ 下 ROUND1、ROUND2 及 docs/ 下 Round3 调研文档汇总生成。*
