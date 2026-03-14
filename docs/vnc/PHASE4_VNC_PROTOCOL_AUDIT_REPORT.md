# Phase 4 VNC 收敛 — 协议与逻辑正确性审核报告

**审核日期**：2025-03-12  
**审核范围**：createVncTransport、vncBridge、get_vnc_proxy_url、useVnc、resourceId/agentId 语义、RFB 参数、重连逻辑、maindesk vs vm_user  
**原则**：宁可错杀不可放过

---

## 一、resourceId / agentId 语义与格式

### 1.1 设计约定（vnc_proxy.rs、vnc_endpoint.rs）

| 概念 | Rust 侧期望 | 格式 |
|------|-------------|------|
| `pc_client_id` / `device_id`（URL 第一段） | 物理 PC 标识（VmControl Ed25519 hex） | 用于 P2P locate、路由 |
| `agent_id` / `resource_id`（URL 第二段） | maindesk: `device_id`；subuser: `device_id:username` | 用于 tunnel::open_vnc_stream、ensure_vnc_endpoint |

### 1.2 数据流核对

| 调用链 | resourceId/agentId 来源 | 格式 | 与 Rust 期望 |
|--------|------------------------|------|---------------|
| **createVncTransport** | `target.resourceId` | maindesk: `device_id`；vm_user: `device_id:username` | ✅ 一致 |
| **get_vnc_proxy_url** | `agentId: resourceId` | 同上 | ✅ 一致 |
| **VncBridgeTransport** | `agentId: resourceId`（构造函数） | 同上 | ✅ 一致 |
| **vnc_bridge_connect** | `agentId` 直接透传 | 同上 | ✅ 一致 |
| **vmService.getVncTransport** | `agentId` 参数 | 见下 | ⚠️ 见 P1 |
| **vncStream.connectStream** | `agentId` 参数 | 见下 | ⚠️ 见 P1 |

### 1.3 问题列表

#### P1. 【高】VNCViewShared / vncStream 的 agentId 与 resourceId 混用

**位置**：`VNCViewShared.tsx` L49-50、`vncStream.ts` L116-134

**现象**：
- `VNCViewShared` 使用 `streamKey = propDeviceId || agentId`，即 maindesk 时 `streamKey = device.id`
- `subscribeToVNCStream(streamKey, subscriber)` 未传 `deviceId`（pc_client_id）
- `vmService.getVncTransport(agentId, deviceId)` 被调用为 `getVncTransport(streamKey, undefined)`

**分析**：
- maindesk：`device.id` = devices 表主键 = `device_id`，与 resourceId 语义一致 ✅
- 但 `getVncTransport` 的第二个参数 `deviceId` 应为 `pc_client_id`（物理 PC），用于多 PC 路由
- `VNCViewShared` 未传 `device.pc_client_id`，导致移动端/多 PC 场景下可能从 my-devices 取到错误目标

**建议**：`subscribeToVNCStream(streamKey, subscriber, deviceId?)` 调用时传入 `device.pc_client_id`，并在 `DeviceFloatingPanel` 中传递：

```ts
subscribeToVNCStream(streamKey, {...}, device.pc_client_id);
```

---

#### P2. 【中】createVncTransport 将 resourceId 作为 agentId 透传

**位置**：`vncTransport.ts` L27-30

**现象**：
```ts
const url = await invoke<string>('get_vnc_proxy_url', {
  agentId: resourceId,
  deviceId: pcClientId ?? null,
});
```

**分析**：`resourceId` 与 Rust 侧 `agent_id` 语义一致（maindesk=device_id，subuser=device_id:username），命名 `agentId` 在 Rust 注释中已说明为「VM/agent 标识」，实际即 resource_id。**无逻辑错误**，但参数名 `agentId` 易与前端「Agent UUID」混淆。

**建议**：在 Tauri 命令注释中明确 `agentId` 实为 `resource_id`，或考虑重命名为 `resourceId`（需改 Rust 接口）。

---

## 二、RFB 参数与 RFB_OPTIONS 一致性

### 2.1 Phase 3 设计（04-task-breakdown.md P3-9、P3-10）

- `shared: true`
- `wsProtocols: ['binary']`
- `credentials: {}`
- `clipViewport: true`

### 2.2 实际使用

| 位置 | shared | clipViewport | scaleViewport | 与 RFB_OPTIONS |
|------|--------|--------------|--------------|----------------|
| **RFB_OPTIONS** (vnc.ts) | true | true | - | 基准 |
| **useVnc** | 继承 RFB_OPTIONS | 可 override，默认 `RFB_OPTIONS.clipViewport` | 默认 true | ✅ |
| **AgentDesktopView** | - | `clipViewport: true` | `scaleViewport: true` | ✅ |
| **DeviceDesktopView** | - | `clipViewport: true` | `scaleViewport: true` | ✅ |
| **vncStream** | 继承 RFB_OPTIONS | **override 为 false** | true | ⚠️ 见 P3 |

### 2.3 问题列表

#### P3. 【中】vncStream 与 useVnc 的 clipViewport 不一致

**位置**：`vncStream.ts` L168-169

**现象**：
```ts
rfb.clipViewport = false;  // Frame capture: 避免 clipping 以获取完整 framebuffer
```

**分析**：vncStream 用于帧捕获（缩略图），故意设为 `false` 以获取完整 framebuffer，与 Phase 3 的「统一 clipViewport: true」有差异。设计上属于合理 override，但需在文档中明确「frame capture 场景例外」。

**建议**：在 `vncStream.ts` 或 `RFB_OPTIONS` 注释中说明：`clipViewport` 在 frame capture 场景下应 override 为 `false`。

---

#### P4. 【低】useVnc 未显式传递 shared

**位置**：`useVnc.ts` L84

**现象**：`new RFB(containerRef.current, t as never, { ...RFB_OPTIONS })` 会继承 `shared: true`，未再显式设置。

**分析**：行为正确，无逻辑错误。仅建议在 useVnc 注释中注明「RFB 参数来自 RFB_OPTIONS，shared 等由 Phase 3 统一」。

---

## 三、maindesk vs vm_user 的 resourceId 格式

### 3.1 约定

| subjectType | resourceId | vnc_endpoint 期望 |
|-------------|------------|-------------------|
| main / default | `device_id` | `[a-zA-Z0-9_-]+` |
| vm_user | `device_id:username` | `[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+` |

### 3.2 来源核对

| 来源 | maindesk resourceId | vm_user resourceId |
|------|---------------------|---------------------|
| **useAgentDevice** | `device_id` | `${device_id}:${subject_id}` |
| **DeviceDesktopView** | `device.id` | `${deviceId}:${username}` |
| **vnc_endpoint validate** | 不含 `:` | 含 `:`，split 后校验 vm_id、username |

**结论**：格式一致 ✅

---

## 四、重连逻辑与 noVNC disconnect 事件

### 4.1 useVnc 重连逻辑

**位置**：`useVnc.ts` L98-117

```ts
rfb.addEventListener('disconnect', ((e: Event & { detail?: { clean?: boolean } }) => {
  const clean = e?.detail?.clean ?? false;
  if (clean) {
    setStatus('disconnected');
  } else {
    setStatus('reconnecting');
    // 指数退避重连...
  }
}) as EventListener);
```

### 4.2 问题列表

#### P5. 【高】noVNC disconnect 事件可能无 detail.clean

**现象**：代码依赖 `e?.detail?.clean`，若 noVNC 不提供该字段，则 `clean ?? false` 恒为 `false`，所有断开均被视为「非 clean」，触发重连。

**影响**：
- 用户主动断开（如切换 Agent）时，若 disconnect 事件无 `clean`，会错误触发重连
- 组件 unmount 时，cleanup 先设 `mountedRef.current = false`，handler 会 `return`，故 unmount 场景安全 ✅
- 但 transport 切换时：`doConnect` 内 `rfbRef.current.disconnect()` 会触发旧 RFB 的 disconnect 事件，此时 `mountedRef` 仍为 true，可能误触发重连

**建议**：
1. 查阅 `@novnc/novnc` 源码确认 disconnect 事件是否包含 `detail.clean`
2. 若不存在，考虑用其他方式区分「用户主动断开」与「异常断开」（如增加 `userInitiatedDisconnect` 标志，在 `disconnect()` 中设置）
3. 或在 transport 切换时，在 disconnect 前设置「切换中」标志，disconnect handler 内跳过重连

---

#### P6. 【高】disconnect 事件与 doConnect 的竞态

**位置**：`useVnc.ts` L76-81、L98-117

**现象**：
1. `doConnect` 内 `rfbRef.current.disconnect()` 断开旧 RFB
2. disconnect 事件可能异步触发
3. handler 中 `rfbRef.current = null` 可能覆盖已创建的新 RFB
4. handler 中 `doConnect()` 重试可能与当前正在进行的 `doConnect` 重复执行

**影响**：transport 快速切换时，可能出现双重连接、ref 被错误置空、重复重连。

**建议**：
1. 在 `doConnect` 开头生成 `connectId`，disconnect handler 内仅当 `connectId` 匹配当前连接时才处理
2. 或在 disconnect 前设置 `rfbRef.current = null`，避免 handler 再次置空
3. 在 handler 中判断：若 `rfbRef.current` 已指向不同的 RFB 实例，则跳过（说明已切换）

---

#### P7. 【中】重连时未保留 viewOnly 等用户设置

**位置**：`useVnc.ts` L106-111

**现象**：重连时调用 `doConnect()`，`doConnect` 的依赖含 `viewOnly`，故会使用当前 `viewOnly` 创建新 RFB。

**分析**：`doConnect` 依赖 `[scaleViewport, clipViewport, viewOnly]`，重连时会使用最新 options，理论上会保留。但若用户在「重连中」修改了 viewOnly，新连接会反映新值。**无明确 bug**，但需确认：重连创建的是全新 RFB，options 来自闭包，应为当前值。

**建议**：在注释中明确「重连会使用当前 options（含 viewOnly）创建新连接」。

---

### 4.3 vncStream 重连逻辑

**位置**：`vncStream.ts` L188-225

**现象**：
- 不区分 `clean`，所有 disconnect 均可能触发重连
- `wasConnected ? 'disconnected' : 'error'`：仅「曾连接成功」时标 disconnected，否则 error
- 重连时 `connectStream(agentId, deviceId)` 未传 `deviceId`（见 P1）
- `state.viewOnly` 在 `connectStream` 内使用，重连会保留 ✅

**问题**：与 P1 相同，`deviceId` 未传递；且 vncStream 不区分 clean，可能对用户主动断开也重连（但 vncStream 通常无显式「断开」入口，多为组件 unmount 时 unsubscribe，此时会 `disconnectStream`，不会走到 disconnect 的自动重连逻辑）。

---

## 五、VncBridgeTransport 与 WebSocket URL 的 RFB 初始化等价性

### 5.1 两种模式

| 模式 | 传输 | RFB 构造 |
|------|------|----------|
| WebSocket URL | `string` | `new RFB(container, url, { ...RFB_OPTIONS })` |
| VncBridgeTransport | `VncBridgeTransport` | `new RFB(container, transport, { ...RFB_OPTIONS })` |

### 5.2 等价性分析

- noVNC RFB 构造函数接受 `string | WebSocket` 或兼容接口
- `VncBridgeTransport` 实现 `readyState`、`onopen`、`onmessage`、`send`、`close` 等，与 WebSocket 行为兼容
- 两种模式均走同一 `get_vnc_proxy_url` / `vnc_bridge_connect` 逻辑，最终 URL 格式一致
- RFB 参数均来自 `RFB_OPTIONS` + 各处的 override（scaleViewport、clipViewport 等）

**结论**：RFB 初始化等价 ✅

---

## 六、问题汇总（按严重程度）

| ID | 严重程度 | 描述 |
|----|----------|------|
| P1 | 高 | VNCViewShared/vncStream 未传 pc_client_id，多 PC 路由可能错误 |
| P5 | 高 | noVNC disconnect 可能无 detail.clean，导致误重连 |
| P6 | 高 | disconnect 事件与 doConnect 竞态，可能双重连接或 ref 错误 |
| P2 | 中 | agentId 命名易与 Agent UUID 混淆 |
| P3 | 中 | vncStream clipViewport 与 Phase 3 不一致，需文档说明 |
| P7 | 中 | 重连时 viewOnly 保留行为需在注释中明确 |
| P4 | 低 | useVnc shared 等参数可补充注释 |

---

## 七、建议修复优先级

1. **P1**：在 `subscribeToVNCStream` 调用链中补充 `pc_client_id` 传递
2. **P5、P6**：核实 noVNC disconnect API，并加固 useVnc 的 disconnect 处理与 transport 切换逻辑
3. **P3**：在 vncStream 与 RFB_OPTIONS 处补充 frame capture 的 clipViewport 说明
4. **P2、P4、P7**：文档与注释层面的澄清
