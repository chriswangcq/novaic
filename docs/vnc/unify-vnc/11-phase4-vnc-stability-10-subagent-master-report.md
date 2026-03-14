# Phase 4 VNC 稳定性 — 10 Subagent 综合研究报告

> 针对「VNC 非常不稳定」问题，派出 10 名 subagent 从不同角度对照设计文档、代码 diff 进行深入研究。本报告汇总各 subagent 结论，并按优先级给出修复建议。

---

## 一、Subagent 分工与报告索引

| # | 研究方向 | 报告文件 | 核心发现 |
|---|----------|----------|----------|
| 1 | 连接生命周期与重连策略 | [VNC_STABILITY_RECONNECT_REPORT.md](./VNC_STABILITY_RECONNECT_REPORT.md) | clean 误判、双轨重连不一致 |
| 2 | 传输层与多 PC 路由 | [VNC_TRANSPORT_MULTI_PC_ROUTING_REPORT.md](./VNC_TRANSPORT_MULTI_PC_ROUTING_REPORT.md) | reconnectVNCStream 未传 deviceId、StreamState 未持久化 pcClientId |
| 3 | RFB 与 noVNC 行为 | [NOVNC_BEHAVIOR_STABILITY_REPORT.md](./NOVNC_BEHAVIOR_STABILITY_REPORT.md) | credentials 未按设备配置、removeEventListener 缺失 |
| 4 | vncStream 与 createVncTransport 双轨 | [VNC_STREAM_VS_CREATE_TRANSPORT_DUAL_TRACK_REPORT.md](./VNC_STREAM_VS_CREATE_TRANSPORT_DUAL_TRACK_REPORT.md) | testWebSocket 与设计冲突、main 重连更弱 |
| 5 | 后端隧道与 socket 时序 | [VNC_BACKEND_TUNNEL_TIMING_REPORT.md](./VNC_BACKEND_TUNNEL_TIMING_REPORT.md) | 30s 超时无 reason、远端+subuser 易超时 |
| 6 | OTA Bridge 与本地 WebSocket | [OTA_BRIDGE_VS_LOCAL_WS_STABILITY_REPORT.md](./OTA_BRIDGE_VS_LOCAL_WS_STABILITY_REPORT.md) | vnc_bridge_close 后 Bridge 任务不退出、无超时 |
| 7 | 前端竞态与快速切换 | [VNC_RACE_FAST_SWITCH_REPORT.md](./VNC_RACE_FAST_SWITCH_REPORT.md) | vncTarget=null 时 requestId 未递增、vncStream 无 requestId |
| 8 | 组件挂载与 effect 依赖 | [VNC_M4_CONTAINERREF_EFFECT_DEPENDENCY_REPORT.md](./VNC_M4_CONTAINERREF_EFFECT_DEPENDENCY_REPORT.md) | containerRef 变化不触发 effect、createVncTransport 无超时 |
| 9 | 错误传播与重试 UX | [VNC_ERROR_PROPAGATION_RETRY_UX_REPORT.md](./VNC_ERROR_PROPAGATION_RETRY_UX_REPORT.md) | transportError 无 Retry、30s 超时无 reason |
| 10 | 状态一致性与轮询 | [VNC_STABILITY_STATE_POLLING_REPORT.md](./VNC_STABILITY_STATE_POLLING_REPORT.md) | vncStream 未接入 DeviceStatusStore、reconnect 未传 deviceId |

---

## 二、P0 级问题（必须修复）

### P0-1：useVnc 中 `e.detail?.clean` 误判导致服务器端断开不重连

**来源**：Subagent 1  
**位置**：`useVnc.ts` L108-127  
**根因**：noVNC 的 `clean` 在服务器端断开（网络中断、VM 停止）时仍为 `true`，useVnc 误判为「用户主动断开」而不重连。  
**影响**：AgentDesktopView / DeviceDesktopView 在断网、VM 重启等场景下无法自动恢复。  
**修复**：用 `userInitiatedDisconnectRef` 标记本端是否发起断开，不再依赖 `clean` 决定是否重连。

---

### P0-2：vnc_proxy 30s 超时后不发送 Close reason

**来源**：Subagent 5、9  
**位置**：`vnc_proxy.rs`  
**根因**：超时后只 drop future，不调用 `send_ws_close_with_reason`。  
**影响**：前端收到 abrupt close，无明确错误；用户看到约 30s 转圈后突然失败，无法区分超时与其他网络问题。  
**修复**：在 30s 超时前主动发送 `send_ws_close_with_reason(ws, "VNC connection timed out (30s)")`。

---

### P0-3：transportError 时无 Retry 按钮

**来源**：Subagent 9  
**位置**：`AgentDesktopView.tsx`、`DeviceDesktopView.tsx`  
**根因**：createVncTransport 失败时直接渲染错误页，不渲染 VncCanvas，因此无 Retry。  
**影响**：用户无法重试，需刷新页面或切换 Agent 才能恢复。  
**修复**：在 transportError 页面增加 Retry 按钮，重新调用 `createVncTransport`。

---

### P0-4：containerRef 变化不触发 useVnc effect

**来源**：Subagent 8  
**位置**：`useVnc.ts`  
**根因**：effect 依赖 `[transport, doConnect, disconnect]`，不包含 `containerRef`。ref 变化不触发重渲染，effect 不会重跑。  
**影响**：若 containerRef 首次为 null（如延迟挂载），之后变为非 null 时 effect 不会重新执行，导致永不连接。  
**修复**：用 ref callback 驱动 `containerReady` 状态，并将其加入 effect 依赖。

---

### P0-5：AgentDesktopView / DeviceDesktopView vncTarget=null 时 requestId 未递增

**来源**：Subagent 7  
**位置**：`AgentDesktopView.tsx` L32-46  
**根因**：effect 中 `if (!vncTarget) return` 提前 return，未执行 `++requestIdRef`，上一个 createVncTransport 的 resolve 仍会执行 `setTransport(t)`。  
**影响**：vncTarget 从 A→null→B 时，A 的旧结果可能覆盖 B，导致连错设备。  
**修复**：在 early return 之前先执行 `++requestIdRef`。

---

### P0-6：vncStream reconnectVNCStream 未传 deviceId，多 PC 重连路由错误

**来源**：Subagent 2、10  
**位置**：`vncStream.ts` reconnectVNCStream、StreamState  
**根因**：reconnectVNCStream(agentId) 不传 deviceId；StreamState 未持久化 pcClientId。  
**影响**：多 PC 时重连可能路由到错误物理机。  
**修复**：在 StreamState 中持久化 deviceId；reconnectVNCStream 支持可选 deviceId 参数；VNCViewShared 的 startVm 中传入 pcClientId。

---

## 三、P1 级问题（建议尽快修复）

### P1-1：vncStream 与 useVnc 重连策略不一致

**来源**：Subagent 1、4、10  
**位置**：`vncStream.ts`、`useVnc.ts`  
**问题**：vncStream 为 2s 固定、3 次；useVnc 为 2s 起、5 次、指数退避。main 路径重连更弱。  
**修复**：将 vncStream 重试改为 5 次 + 指数退避，与 useVnc 一致。

---

### P1-2：vncStream 与 createVncTransport 双轨 — main 仍用 vncStream

**来源**：Subagent 4  
**位置**：`DeviceFloatingPanel.tsx`（main 分支）  
**问题**：设计 §3.3 要求取消前端 WebSocket 探测；vncStream 仍调用 testWebSocket，与设计不符。  
**修复**：移除 vncStream 中的 testWebSocket 调用；或规划 P4-17 将 main 迁移到 createVncTransport。

---

### P1-3：vncStream 未接入 DeviceStatusStore

**来源**：Subagent 10  
**位置**：`vncStream.ts`  
**问题**：useVnc 在 connected 时 incrementVncConnectionCount，vncStream 不调用。main 路径的 VNC 连接不会触发轮询降为 3s。  
**修复**：在 vncStream connect 时 increment，disconnect 时 decrement。

---

### P1-4：vncStream 无 requestId，快速切换 pcClientId 时竞态

**来源**：Subagent 7  
**位置**：`vncStream.ts` connectStream  
**问题**：connectStream 无 requestId 校验；StreamState 不保存 deviceId。P1 的 connectStream 进行中切换到 P2，P1 完成后会覆盖 state，导致连到错误 PC。  
**修复**：增加 requestId 校验；在 StreamState 中保存 currentDeviceId；重连时使用 state 中的 currentDeviceId。

---

### P1-5：createVncTransport 与 VncBridgeTransport.connect 无超时

**来源**：Subagent 6、8  
**位置**：`vncTransport.ts`、`vncBridge.ts`  
**问题**：网络慢或后端无响应时，用户会一直看到 "Preparing transport…"，无超时或重试。  
**修复**：为 createVncTransport 增加超时（如 30s），超时后 reject 并展示可重试的错误。

---

### P1-6：credentials 未按设备配置传入

**来源**：Subagent 3  
**位置**：`RFB_OPTIONS`、`useVnc`、`vncStream`  
**问题**：RFB_OPTIONS.credentials = {} 恒为空；credentialsrequired 一律视为 unexpected 并失败。  
**修复**：从设备配置读取 VNC 密码，在创建 RFB 时传入 credentials；credentialsrequired 时若有密码则 sendCredentials。

---

### P1-7：vnc_bridge_close 后 Bridge 任务不退出

**来源**：Subagent 6  
**位置**：Tauri vnc_bridge  
**问题**：`vnc_bridge_close` 只从 map 中移除 bridge，Bridge 任务不会立即退出，WebSocket 可能长期挂起，存在资源泄漏。  
**修复**：增加 CancellationToken 或关闭 channel，让任务主动关闭 WS。

---

### P1-8：useVnc 在 disconnect 中不读取 e?.detail?.reason

**来源**：Subagent 9  
**位置**：`useVnc.ts`  
**问题**：后端返回的具体错误被丢弃，用户只看到通用文案。  
**修复**：在 disconnect 中读取 `e?.detail?.reason`，优先展示后端错误。

---

### P1-9：reconnecting 时 overlay 未禁用 Retry

**来源**：Subagent 9  
**位置**：`VncConnectionOverlay.tsx`  
**问题**：重连过程中点 Retry 会触发额外 doConnect，可能与自动重连产生竞态。  
**修复**：reconnecting 时显示 "Reconnecting…" 并禁用 Retry，避免与自动重连竞态。

---

## 四、P2 级问题（逐步改进）

| # | 问题 | 来源 | 修复建议 |
|---|------|------|----------|
| 1 | 远端 + subuser 易超时（P2P + ensure_vnc_endpoint 叠加 > 30s） | Subagent 5 | 延长或动态设置 WS 超时（如 60s） |
| 2 | 建立后断开时未附带 reason | Subagent 5 | bridge_ws_quic 中 quic_recv 因 EOF 退出时发送带 reason 的 Close |
| 3 | RFB 未 removeEventListener | Subagent 3 | 在 disconnect/cleanup 时移除监听器 |
| 4 | vncStream 无 reconnecting 状态 | Subagent 4 | 增加 reconnecting 状态 |
| 5 | useVnc effect cleanup 未显式 disconnect | Subagent 7 | 在 effect cleanup 中显式调用 disconnect |

---

## 五、修复优先级建议（汇总）

| 优先级 | 修复项 | 预计影响 |
|--------|--------|----------|
| **P0** | clean 误判、30s 超时 reason、transportError Retry、containerRef 依赖、requestId 递增、reconnect 传 deviceId | 显著提升断连恢复、多 PC 正确性、重试体验 |
| **P1** | 双轨重连统一、vncStream 接入 DeviceStatusStore、vncStream requestId、createVncTransport 超时、credentials、Bridge 任务退出、disconnect reason、reconnecting 禁用 Retry | 进一步稳定、一致性、UX |
| **P2** | 超时延长、建立后断开 reason、removeEventListener、reconnecting 状态、effect cleanup | 长期优化 |

---

## 六、附录：Subagent 报告文件列表

以下报告已存放于 `docs/unify-vnc/` 目录：

- `docs/unify-vnc/VNC_STABILITY_RECONNECT_REPORT.md`
- `docs/unify-vnc/VNC_TRANSPORT_MULTI_PC_ROUTING_REPORT.md`
- `docs/unify-vnc/NOVNC_BEHAVIOR_STABILITY_REPORT.md`
- `docs/unify-vnc/VNC_STREAM_VS_CREATE_TRANSPORT_DUAL_TRACK_REPORT.md`
- `docs/unify-vnc/VNC_BACKEND_TUNNEL_TIMING_REPORT.md`
- `docs/unify-vnc/OTA_BRIDGE_VS_LOCAL_WS_STABILITY_REPORT.md`
- `docs/unify-vnc/VNC_RACE_FAST_SWITCH_REPORT.md`
- `docs/unify-vnc/VNC_M4_CONTAINERREF_EFFECT_DEPENDENCY_REPORT.md`
- `docs/unify-vnc/VNC_ERROR_PROPAGATION_RETRY_UX_REPORT.md`
- `docs/unify-vnc/VNC_STABILITY_STATE_POLLING_REPORT.md`
