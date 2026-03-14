# Phase 4 VNC 收敛 — UX 与边界情况代码审核报告

**审核范围**：AgentDesktopView、DeviceDesktopView、DeviceVNCView、VncCanvas、VisualPanel、DeviceFloatingPanel、DeviceManagerPage

**审核日期**：2026-03-12

---

## 一、问题列表（按严重程度）

### P0 — 严重（影响核心功能或数据正确性）

| # | 组件 | 问题 | 说明 |
|---|------|------|------|
| P0-1 | DeviceFloatingPanel | **多 PC 场景下 `api.devices.stop/start/status` 未传 `pcClientId`** | `StoppedDeviceChip.handleStart`、`DeviceCard` 的 PowerMenu `onConfirm`、`fetchDeviceStatus` 均调用 `api.devices.start(device.id)` / `api.devices.stop(device.id)` / `api.devices.status(device.id)` 而未传 `device.pc_client_id`。多 PC 时后端会 fallback 到第一个在线 PC，可能操作错误设备。 |
| P0-2 | useVnc | **`containerRef` 未加入 `doConnect` 依赖** | `doConnect` 的 `useCallback` 依赖为 `[scaleViewport, clipViewport, viewOnly]`，未包含 `containerRef`。若 `containerRef.current` 在首次渲染为 null、后续才挂载，`useEffect` 会重跑但 `doConnect` 闭包可能持有旧 ref。实际影响取决于 RFB 挂载时机，存在潜在竞态。 |
| P0-3 | DeviceDesktopView (vm_user) | **`displayNum` 固定为 0** | `DeviceFloatingPanel` 调用 `DeviceDesktopView` 时传 `displayNum={0}`，而 vm_user 的 display 可能非 0。VncTarget 的 resourceId 为 `deviceId:username`，后端可能依赖 display 区分会话，传错可能导致连接错误桌面。 |

### P1 — 高（影响用户体验或可预期性）

| # | 组件 | 问题 | 说明 |
|---|------|------|------|
| P1-1 | AgentDesktopView / DeviceDesktopView | **transportError 无重试入口** | 当 `createVncTransport` 失败时，直接渲染错误 UI，无 Retry 按钮。用户只能切换 agent/device 或刷新页面才能重试。 |
| P1-2 | AgentDesktopView / DeviceDesktopView | **`reconnecting` 与 `failed` 共用同一 overlay** | `renderOverlay` 中 `reconnecting` 和 `failed` 都显示 "Connection failed" + Retry。`reconnecting` 时自动重连中，用户点 Retry 会触发额外 `doConnect()`，可能与自动重连竞态。 |
| P1-3 | useVnc | **重连失败后 errorMsg 固定为英文** | `setErrorMsg('Connection lost, max retries exceeded')` 硬编码英文，与 VNCViewShared 等组件的「连接失败」「VM 未连接」等中文不一致。 |
| P1-4 | DeviceDesktopView (maindesk) | **startDevice 成功后固定 2s 再 setDeviceStatus** | `await new Promise((r) => setTimeout(r, 2000))` 后直接 `setDeviceStatus('running')`，未轮询或调用 `api.devices.status` 确认。若 VM 启动慢于 2s，会过早显示 VNC 并可能连接失败。 |
| P1-5 | DeviceVNCView (Android) | **startDevice 成功后无等待** | 与 DeviceDesktopView 不同，Android 的 `startDevice` 成功后立即 `setStatus('running')`，ScrcpyView 的 `autoConnect` 可能早于设备就绪。 |
| P1-6 | DeviceManagerPage | **空状态提示与布局不一致** | 空状态写「从左侧 Devices 区选择一个设备」，但 PC 布局下设备列表在 AgentDrawer（左侧），手机布局下需先返回 sidebar 才能看到列表。`isPageMode` 时提示「点击左上角菜单，在 Devices 区选择设备」更准确，但两种模式提示可能混淆。 |
| P1-7 | DeviceFloatingPanel | **loading/error 时直接 return null** | `if (loading) return null;` 和 `if (error) { console.warn(...); return null; }` 导致加载中或绑定失败时浮窗完全消失，用户无任何反馈，易误以为功能不可用。 |
| P1-8 | VncCanvas | **transport 为 null 时仍渲染 overlay 容器** | `renderOverlay && status !== 'connected'` 时渲染 overlay。当 `transport` 为 null，`useVnc` 会 `setStatus('disconnected')`，overlay 会显示 "Disconnected" + Reconnect。但此时 `connect()` 内部 `if (!t || !containerRef.current) return` 会直接返回，Reconnect 无效，用户会困惑。 |

### P2 — 中（边界情况或体验细节）

| # | 组件 | 问题 | 说明 |
|---|------|------|------|
| P2-1 | AgentDesktopView / DeviceDesktopView | **快速切换 agent/device 时可能闪烁** | `vncTarget` 变化会触发 `createVncTransport`，旧 transport 的 cleanup 与新区建可能重叠。`cancelled` 可避免 setState，但 VncCanvas 会先 unmount 再 mount，可能短暂显示 loading 或空白。 |
| P2-2 | VisualPanel | **Linux/Android 切换时 ScrcpyView 与 AgentDesktopView 同时 unmount** | `activeView` 切换时，旧视图直接卸载。若用户频繁切换，会反复建立/断开 VNC 与 Scrcpy 连接，增加后端压力且可能产生连接泄漏。 |
| P2-3 | DeviceFloatingPanel | **DeviceCard 单/双击逻辑易误触** | 250ms 内区分单击（expand）与双击（expand + operating）。慢速双击可能被识别为两次单击；快速单击可能误判为双击。 |
| P2-4 | DeviceDesktopView (maindesk) | **deviceStatus `unknown` 时显示 "Waiting for VM…"** | `unknown` 多为 `api.devices.status` 请求失败，显示 "Waiting for VM…" 易误导用户以为 VM 在启动中，实际可能是网络错误。 |
| P2-5 | DeviceVNCView (Android) | **ScrcpyView 传入 `device_serial \|\| ''`** | 当 `device.device_serial` 为空时传空字符串，ScrcpyView 可能仍尝试连接，产生无意义错误。 |
| P2-6 | DeviceManagerPage | **DeviceListPanel 未使用** | `DeviceListPanel` 在文件中定义并 export，但未被引用。设备选择依赖 AgentDrawer 的 devicesContent，若未来需要独立 DeviceManagerPage 布局（如 320px 列表 + 右侧 VNC），需接入。当前为死代码。 |
| P2-7 | AgentDesktopView | **error 来自 useAgentDevice 时无 refetch 入口** | `if (error)` 时仅展示错误文案，无「重试」按钮，用户需切换 agent 或刷新才能重试。 |
| P2-8 | VNCViewShared | **与 Phase 4 收敛组件不同数据流** | DeviceFloatingPanel 的 main 使用 VNCViewShared（vncStream 服务），而 DeviceDesktopView 使用 createVncTransport + useVnc + VncCanvas。两套路径状态、错误处理、重连逻辑不一致，增加维护成本。 |

### P3 — 低（优化建议）

| # | 组件 | 问题 | 说明 |
|---|------|------|------|
| P3-1 | 全局 | **无障碍（a11y）缺失** | 除 TauriRequiredFallback、AgentDrawer 的 `aria-label` 外，VNC 相关组件几乎无 `aria-*`、`role`、`tabIndex`。Retry/Reconnect/Start/Stop 等按钮无 `aria-label`，键盘用户难以理解。 |
| P3-2 | 全局 | **无键盘导航** | VNC 视图内的 Retry、Reconnect、Close 等按钮可点击，但无 Tab 顺序或焦点管理。ESC 仅在 AgentDrawer、DeviceFloatingPanel 的 expanded 状态有处理，VncCanvas overlay 内无。 |
| P3-3 | 全局 | **移动端/窄屏布局未针对 VNC 优化** | 使用 `min-w-0`、`truncate` 等通用布局，无针对 VNC 画布在窄屏下的缩放、触摸手势优化。DeviceFloatingPanel 的 overlay 尺寸基于 `window.innerWidth/Height`，横竖屏切换时需 resize 事件，已有 `recompute`，但小屏下可能过于拥挤。 |
| P3-4 | 全局 | **中英混用** | AgentDesktopView/DeviceDesktopView 为英文（"Connecting to desktop…", "Connection failed"），VNCViewShared、DeviceManagerPage 空状态为中文。DeviceFloatingPanel 的 PowerMenu 为中文（"关闭设备?"）。 |
| P3-5 | DeviceDesktopView | **vm_user 的 toolbar 显示 username** | 子用户桌面 toolbar 显示 `username` 和 `display :{displayNum}`，若 `displayNum` 固定为 0 可能误导。 |
| P3-6 | DeviceFloatingPanel | **StoppedDeviceChip 的 handleStart 无 pcClientId** | 与 P0-1 重复，但需在修复时一并考虑。 |
| P3-7 | useVnc | **credentialsrequired 时 errorMsg 为英文** | `setErrorMsg('VNC requires credentials (unexpected)')` 为英文。 |

---

## 二、pcClientId 未传时的行为汇总

| 调用位置 | API | pcClientId 来源 | 未传时行为 |
|----------|-----|-----------------|------------|
| DeviceDesktopView (maindesk) | status, start, stop | `device.pc_client_id` | 设备有 `pc_client_id` 时正常；新建/无字段时可能 fallback 到第一个 PC |
| DeviceDesktopView (vm_user) | 无 | `props.pcClientId` | DeviceManagerPage 传 `effectiveSelectedDevice.pc_client_id`；DeviceFloatingPanel 传 `device.pc_client_id`。多 PC 时依赖 device 数据正确 |
| DeviceVNCView (Android) | status, start, stop | `device.pc_client_id` | 同上 |
| DeviceFloatingPanel | status, start, stop | `device.pc_client_id` | **当前未传**，见 P0-1 |
| createVncTransport | get_vnc_proxy_url | `target.pcClientId` | `pcClientId ?? null` 传给 Tauri，后端从 my-devices 解析 |
| useAgentDevice | bindingToVncTarget | `device?.pc_client_id` | 来自 device 缓存，新建设备可能为 undefined |

**结论**：多 PC 场景下，DeviceFloatingPanel 的 start/stop/status 必须修复；其余调用处需确保 device 数据含 `pc_client_id`，新建设备需通过 `api.p2p.resolveCurrentPcClientId` 等解析当前 PC。

---

## 三、加载/错误/空状态提示检查

| 场景 | 组件 | 当前提示 | 问题 |
|------|------|----------|------|
| 无 agent 选中 | AgentDesktopView | "No agent selected" | 清晰 |
| 加载 agent 设备 | AgentDesktopView | "Loading agent device…" | 清晰 |
| useAgentDevice 错误 | AgentDesktopView | `{error}` | 无重试 |
| 无设备绑定 | AgentDesktopView | "No device bound" | 清晰 |
| transport 创建失败 | AgentDesktopView | `{transportError}` | 无重试 |
| VNC connecting | AgentDesktopView | "Connecting to desktop…" | 清晰 |
| VNC failed/reconnecting | AgentDesktopView | "Connection failed" + Retry | reconnecting 时 Retry 可能竞态 |
| VNC disconnected | AgentDesktopView | "Disconnected" + Reconnect | 清晰 |
| maindesk 未运行 | DeviceDesktopView | "VM is stopped" / "Waiting for VM…" | unknown 时 "Waiting for VM…" 易误导 |
| maindesk starting | DeviceDesktopView | "Connecting to desktop…" | 清晰 |
| maindesk error | DeviceDesktopView | "Connection failed" + Retry | 清晰 |
| transport 创建失败 | DeviceDesktopView | `{transportError}` | 无重试 |
| 无设备选中 | DeviceManagerPage | "从左侧 Devices 区选择一个设备" | 手机布局下需更精确 |
| 设备列表加载失败 | DeviceManagerPage | `{error}` + 重试 | 有重试 |
| DeviceFloatingPanel loading | DeviceFloatingPanel | (无) | return null，无反馈 |
| DeviceFloatingPanel error | DeviceFloatingPanel | (无) | return null，仅 console.warn |

---

## 四、网络断开/超时/重连失败体验

| 环节 | 行为 | 问题 |
|------|------|------|
| useVnc 断开重连 | 非 clean 断开时进入 reconnecting，2s 起指数退避，最多 5 次 | 5 次后 failed，用户可点 Retry 手动重连 |
| reconnecting 时 Retry | 会调用 `doConnect()` | 与自动重连可能竞态，建议重连中禁用 Retry 或合并逻辑 |
| transport 为 null 时 Reconnect | `connect()` 直接 return | 无效果，用户困惑 |
| createVncTransport 超时 | 无显式超时，Promise 一直 pending | 可能长时间卡在 loading |
| api.devices.status 失败 | 设 DeviceDesktopView 为 unknown | 显示 "Waiting for VM…" 易误导 |

---

## 五、快速切换 agent/device 的 UI 状态

| 场景 | 行为 | 问题 |
|------|------|------|
| 切换 agentId | useAgentDevice 重新 fetch，vncTarget 变化，createVncTransport 重建 | 旧 transport cleanup 可能滞后，新 transport 建立前可能短暂显示 loading |
| 切换 activeView (Linux/Android) | 直接卸载旧视图、挂载新视图 | 连接反复建立/断开，无连接池或复用 |
| 切换 selectedDevice | DeviceManagerPage 重新渲染 DeviceVNCView/DeviceDesktopView | 同上，VNC 连接重建 |
| DeviceFloatingPanel 展开/收起 | 同一 DeviceCard 内组件不 unmount | 设计合理，无重连 |

---

## 六、移动端/窄屏布局与交互

| 组件 | 布局 | 问题 |
|------|------|------|
| AgentDesktopView | 全高，toolbar 固定顶部 | 无针对窄屏的 touch 优化 |
| DeviceDesktopView | 同上 | 同上 |
| DeviceManagerPage | 空状态时居中，有按钮 | 手机布局下需返回 sidebar 选设备，流程略绕 |
| DeviceFloatingPanel | 固定定位，基于 window 尺寸 | 小屏下 overlay 可能过小 |
| VisualPanel | 可调整 VM 高度比例 | 窄屏下 resize 手柄可能难操作 |
| VncCanvas | 无 | 无触摸手势（缩放、拖拽）的显式支持，依赖 noVNC 默认行为 |

---

## 七、建议修复优先级

1. **P0**：修复 DeviceFloatingPanel 的 pcClientId 传递；修复 vm_user 的 displayNum；评估 useVnc 的 containerRef 依赖。
2. **P1**：为 transportError 增加 Retry；区分 reconnecting 与 failed 的 overlay；为 DeviceFloatingPanel 的 loading/error 增加占位或 skeleton；transport 为 null 时隐藏或禁用 Reconnect。
3. **P2**：统一 reconnecting 时 Retry 行为；deviceStatus unknown 时显示更准确提示；考虑 DeviceListPanel 的用途或移除。
4. **P3**：补充 a11y（aria-label、键盘导航）；统一中英文；优化窄屏布局。

---

## 八、附录：文件索引

- `novaic-app/src/components/Visual/AgentDesktopView.tsx`
- `novaic-app/src/components/Visual/DeviceDesktopView.tsx`
- `novaic-app/src/components/Visual/DeviceVNCView.tsx`
- `novaic-app/src/components/Visual/VncCanvas.tsx`
- `novaic-app/src/components/Visual/VisualPanel.tsx`
- `novaic-app/src/components/Visual/VNCViewShared.tsx`
- `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx`
- `novaic-app/src/components/VM/DeviceManagerPage.tsx`
- `novaic-app/src/hooks/useVnc.ts`
- `novaic-app/src/hooks/useAgentDevice.ts`
- `novaic-app/src/services/vncTransport.ts`
