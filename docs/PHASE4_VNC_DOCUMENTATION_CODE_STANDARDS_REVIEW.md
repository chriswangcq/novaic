# Phase 4 VNC 收敛 — 文档与代码规范审核报告

**审核范围**：novaic-app Phase 4 新增和修改的所有文件  
**审核日期**：2026-03-12  
**审核重点**：JSDoc/TSDoc、注释准确性、命名一致性、文件头职责说明、与项目规范一致性  
**原则**：宁可错杀不可放过

---

## 一、审核文件清单

| 文件 | 类型 | 行数 |
|------|------|------|
| `src/services/vncTransport.ts` | 传输层 | 34 |
| `src/services/vncBridge.ts` | 传输层 | 118 |
| `src/hooks/useVnc.ts` | 会话层 | 167 |
| `src/hooks/useAgentDevice.ts` | 数据层 | 109 |
| `src/components/Visual/VncCanvas.tsx` | 展示层 | 35 |
| `src/components/Visual/AgentDesktopView.tsx` | 视图层 | 168 |
| `src/components/Visual/DeviceDesktopView.tsx` | 视图层 | 348 |
| `src/components/Visual/DeviceVNCView.tsx` | 视图层 | 118 |
| `src/stores/deviceStatusStore.ts` | 状态 | 68 |
| `src/types/vnc.ts` | 类型 | 34 |
| `src/components/Layout/DeviceFloatingPanel.tsx` | 布局（Phase 4 相关） | 671 |
| `src/components/Visual/VNCViewShared.tsx` | 遗留（与 Phase 4 并存） | 245 |
| `src-tauri/src/commands/vnc_urls.rs` | Rust 命令 | 120 |
| `src-tauri/src/commands/vnc_bridge.rs` | Rust 命令 | 219 |
| `src-tauri/src/vnc_proxy.rs` | Rust 核心 | 643 |
| `src-tauri/p2p/src/relay.rs` | P2P Phase 4 | 241 |

---

## 二、问题列表（按严重程度）

### Critical（严重）

| 编号 | 问题 | 文件 | 行号 | 描述 |
|------|------|------|------|------|
| **C1** | **DeviceFloatingPanel 注释与实现不符** | DeviceFloatingPanel.tsx | 5 | 注释写 `main → VNCViewShared, vm_user → VmUserVNCView`，实际 vm_user 已改为 `DeviceDesktopView`。VmUserVNCView 若已删除，注释会误导后续维护。 |
| **C2** | **VncTarget subjectType: 'default' 语义未文档化** | types/vnc.ts | 28 | `subjectType: 'main' \| 'vm_user' \| 'default'` 中，`'default'` 的语义及与 main/vm_user 的区别未在 JSDoc 中说明。design doc 中 default 表示 Android 默认，但 VncTarget 主要用于 VNC，易混淆。 |
| **C3** | **VncTransport 类型无 JSDoc** | vncTransport.ts | 14 | `export type VncTransport = string \| VncBridgeTransport` 无注释，使用者需阅读实现才能理解 string 表示 WebSocket URL、对象表示 Bridge。 |
| **C4** | **VncBridgeTransport 参数命名与 VncTarget 不一致** | vncBridge.ts | 56-58 | 构造函数参数为 `(agentId, deviceId)`，而 createVncTransport 传入 `(resourceId, pcClientId)`。语义一致但命名不一致，无注释说明映射关系。 |

---

### Major（重要）

| 编号 | 问题 | 文件 | 行号 | 描述 |
|------|------|------|------|------|
| **M1** | **buildVncTarget 无 JSDoc** | DeviceDesktopView.tsx | 41-59 | 对 vm_user 的 `pcClientId` 可选及 fallback 行为无说明。后续维护者易误以为 pcClientId 必填。 |
| **M2** | **useVnc 函数无 JSDoc** | useVnc.ts | 36-39 | 公共 API `useVnc(transport, containerRef, options)` 无 `@param`、`@returns` 说明。 |
| **M3** | **AgentDesktopViewProps 无 JSDoc** | AgentDesktopView.tsx | 15-22 | 接口及 `agentId`、`onClose`、`viewOnly`、`embedded` 无说明。 |
| **M4** | **DeviceDesktopViewProps 无 JSDoc** | DeviceDesktopView.tsx | 19-39 | `DeviceDesktopViewMainProps`、`DeviceDesktopViewVmUserProps` 及 `subjectType`、`device`、`deviceId`、`username`、`displayNum`、`pcClientId` 无说明。 |
| **M5** | **VncCanvasProps 注释不完整** | VncCanvas.tsx | 12-17 | `renderOverlay` 的 `ctx` 类型及 `status`、`errorMsg`、`connect` 含义未在 JSDoc 中说明。 |
| **M6** | **useAgentDevice 函数无 JSDoc** | useAgentDevice.ts | 56 | 公共 API `useAgentDevice(agentId)` 无 `@param`、`@returns` 说明。 |
| **M7** | **types/vnc.ts 文件头与内容不符** | types/vnc.ts | 1-4 | 文件头写「Phase 3 统一 RFB 参数」，但文件同时包含 Phase 1 的 VncTarget。应拆分为「Phase 1 VncTarget」「Phase 3 RFB_OPTIONS」或统一说明。 |
| **M8** | **VNCViewShared deviceId 注释易混淆** | VNCViewShared.tsx | 26-27 | 注释写「Device ID，主桌面时使用（与 devices.start 一致，VNC socket 为 novaic-vnc-{deviceId}.sock）」。maindesk 时 deviceId 实为 resourceId（= device_id），与 pc_client_id 不同，易误导。 |
| **M9** | **vnc_urls.rs agentId 注释不精确** | vnc_urls.rs | 17 | 注释写「VM/agent 标识」，实际为 resource_id（maindesk: device_id；subuser: `{deviceId}:{username}`）。应明确为 resource_id。 |

---

### Minor（轻微）

| 编号 | 问题 | 文件 | 行号 | 描述 |
|------|------|------|------|------|
| **m1** | **AgentDesktopView 文件头无依赖说明** | AgentDesktopView.tsx | 1-6 | 文件头写「useAgentDevice → createVncTransport → useVnc → VncCanvas」，但未说明依赖的 hooks、services、types。 |
| **m2** | **DeviceDesktopView 文件头无依赖说明** | DeviceDesktopView.tsx | 1-7 | 文件头未列出 createVncTransport、api、VncCanvas 等依赖。 |
| **m3** | **DeviceVNCView 文件头无「职责」说明** | DeviceVNCView.tsx | 1-6 | 仅写「Phase 4 收敛」「Linux → DeviceDesktopView, Android → ScrcpyView」，未说明「职责」：路由到不同设备类型的视图。 |
| **m4** | **useVnc 文件头未说明依赖** | useVnc.ts | 1-6 | 未列出 RFB、deviceStatusStore、vncTransport、vncBridge。 |
| **m5** | **vncTransport 文件头未说明依赖** | vncTransport.ts | 1-9 | 未列出 invoke、vncBridge、types/vnc。 |
| **m6** | **useAgentDevice 未说明 deviceCache 模块级单例** | useAgentDevice.ts | 23-24 | `deviceCache` 为模块级 Map，无大小限制，长时间使用可能内存增长。应在注释中说明或标注技术债。 |
| **m7** | **P1-15 注释位置** | useVnc.ts | 141 | `// P1-15: VNC 连接期间通知 store，轮询降为 3s` 引用任务编号，但未说明与 deviceStatusStore 的联动逻辑。 |
| **m8** | **DeviceStatusStore 无方法 JSDoc** | deviceStatusStore.ts | 19-30 | `setStatus`、`subscribeDevice`、`incrementVncConnectionCount` 等无 `@param`、`@returns`。 |
| **m9** | **VncBridgeTransport 类无 JSDoc** | vncBridge.ts | 36 | 类及 `connect`、`close`、`send` 方法无 JSDoc。 |
| **m10** | **relay.rs 模块头未说明导出** | p2p/src/relay.rs | 1-4 | 模块头未列出 `RelayRole`、`connect_via_relay`、`punch_or_relay` 等公开 API。 |

---

### Info（建议）

| 编号 | 问题 | 文件 | 行号 | 描述 |
|------|------|------|------|------|
| **i1** | **中英混用：文件头多为中文** | 多处 | - | Phase 4 文件头多为中文（如「统一 VNC 传输层」「纯展示组件」），与项目其他文件（如 FRONTEND_ARCHITECTURE.md 英文）风格不统一。建议统一为英文或明确「Phase 4 文件头用中文」的规范。 |
| **i2** | **AgentDesktopView 文案全英文** | AgentDesktopView.tsx | 54-78 | "Connecting to desktop…"、"Connection failed"、"Disconnected"、"Retry"、"Reconnect" 等为英文，与部分中文注释混用。若产品面向中文用户，可考虑 i18n。 |
| **i3** | **DeviceDesktopView 文案全英文** | DeviceDesktopView.tsx | 141-175 | 同上。 |
| **i4** | **DeviceVNCView 无文件级 Phase 标记** | DeviceVNCView.tsx | 1 | 文件头写「Phase 4 收敛」，但未说明与 Phase 4 任务 P4-14 的对应关系。 |
| **i5** | **vmService.getVncTransport 无 @deprecated** | vm.ts | 163 | 若 vncStream 迁移后计划删除，应添加 `@deprecated 请使用 createVncTransport(VncTarget)，vncStream 迁移后移除`。 |
| **i6** | **types/index.ts 未 re-export VncTransport** | types/index.ts | 6 | 仅导出 `VncTarget`、`RFB_OPTIONS`，`VncTransport` 需从 vncTransport 导入。若希望类型统一入口，可 re-export。 |
| **i7** | **vnc_proxy.rs 注释已更新** | vnc_proxy.rs | 1-25 | 当前注释已包含 relay、tunnel、pc_client_id、resource_id，与 design 一致。✓ 无问题。 |
| **i8** | **setup.rs 注释已更新** | setup.rs | 1-4 | 已写「VncProxy 统一 relay 逻辑（打洞已移除）」。✓ 无问题。 |

---

## 三、与项目规范一致性检查

### 3.1 HANDOVER.md

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 架构分层（Render/Business/DB） | ⚠️ 部分 | Phase 4 组件在 Render 层，vncTransport 在 Business 层，符合 FRONTEND_ARCHITECTURE。但 useVnc 直接依赖 deviceStatusStore，与「Hooks 触发 action」略有耦合。 |
| 命名规范（pc_client_id vs device_id） | ✓ | vnc_urls、vnc_proxy、VncTarget 已区分。 |
| Gateway/Relay 联动 | ✓ | 注释与 HANDOVER 五附一致。 |

### 3.2 docs/unify-vnc/02-expert-design.md

| 检查项 | 结果 | 说明 |
|--------|------|------|
| VncTarget 结构 | ✓ | pcClientId、resourceId、subjectType、deviceId、username 与设计一致。 |
| createVncTransport 职责 | ✓ | 根据 target 建立传输，OTA 用 Bridge，本机/远程用 URL。 |
| useAgentDevice 数据流 | ✓ | getAgentBinding → devices.get，替代 api.devices.list。 |

### 3.3 docs/unify-vnc/04-task-breakdown.md

| 检查项 | 结果 | 说明 |
|--------|------|------|
| P4-1~P4-10 传输层/会话层/展示层 | ✓ | createVncTransport、useVnc、VncCanvas 已实现。 |
| P4-11~P4-16 业务层组件 | ✓ | AgentDesktopView、DeviceDesktopView、DeviceVNCView 已迁移。 |
| P4-17 vncStream 重构 | ⚠️ 未完成 | 任务清单标记为 `[ ]`，vncStream 与 createVncTransport 双轨并存。 |

---

## 四、过时注释汇总

| 文件 | 位置 | 过时内容 | 应改为 |
|------|------|----------|--------|
| DeviceFloatingPanel.tsx | 5 | `vm_user → VmUserVNCView` | `vm_user → DeviceDesktopView` |
| types/vnc.ts | 1 | 「Phase 3 统一 RFB 参数」 | 补充「含 Phase 1 VncTarget」或拆分文件 |
| vnc_urls.rs | 17 | agentId 注释「VM/agent 标识」 | resource_id（maindesk: device_id；subuser: `{deviceId}:{username}`） |

---

## 五、JSDoc/TSDoc 缺失汇总

| 文件 | 缺失项 |
|------|--------|
| vncTransport.ts | VncTransport 类型、createVncTransport 的 target 字段说明 |
| useVnc.ts | useVnc 函数、UseVncResult 各字段 |
| VncCanvas.tsx | VncCanvasProps 各 prop 的详细说明、renderOverlay ctx |
| AgentDesktopView.tsx | AgentDesktopViewProps、各 prop |
| DeviceDesktopView.tsx | buildVncTarget、DeviceDesktopViewProps、各 prop |
| DeviceVNCView.tsx | DeviceVNCViewProps |
| useAgentDevice.ts | useAgentDevice 函数、bindingToVncTarget、getDeviceCached |
| vncBridge.ts | VncBridgeTransport 类、connect/close/send、agentId/deviceId 与 resourceId/pcClientId 映射 |
| deviceStatusStore.ts | 各 store 方法 |
| types/vnc.ts | subjectType: 'default' 语义 |

---

## 六、修复优先级建议

### 立即修复（Critical）

1. **C1**：更新 DeviceFloatingPanel 注释为 `main → VNCViewShared, vm_user → DeviceDesktopView`
2. **C2**：在 VncTarget 的 subjectType 上补充 JSDoc，说明 `'default'` 语义（若用于 Android 则注明；若仅占位则说明）
3. **C3**：为 VncTransport 类型添加 JSDoc
4. **C4**：在 VncBridgeTransport 构造函数或 vncTransport 调用处添加注释：`agentId = resourceId, deviceId = pcClientId`

### 短期修复（Major）

5. **M1**：为 buildVncTarget 添加 JSDoc，说明 vm_user 的 pcClientId 可选及 fallback
6. **M2~M6**：为 useVnc、AgentDesktopViewProps、DeviceDesktopViewProps、VncCanvasProps、useAgentDevice 添加完整 JSDoc
7. **M7**：修正 types/vnc.ts 文件头
8. **M8**：修正 VNCViewShared deviceId 注释
9. **M9**：修正 vnc_urls.rs agentId 注释

### 中期优化（Minor）

10. **m1~m10**：补充文件头依赖说明、方法 JSDoc、relay 模块导出说明

### 低优先级（Info）

11. **i1~i6**：统一中英风格、补充 @deprecated、考虑 types re-export

---

## 七、总结

| 类别 | 数量 |
|------|------|
| Critical | 4 |
| Major | 9 |
| Minor | 10 |
| Info | 8 |

**整体评价**：Phase 4 VNC 收敛在架构与实现上与设计文档基本一致，但**文档与代码规范存在明显短板**。主要问题集中在：

1. **JSDoc/TSDoc 不完整**：多数公共 API（useVnc、useAgentDevice、buildVncTarget、各 Props）无参数与返回值说明
2. **注释过时**：DeviceFloatingPanel、vnc_urls、types/vnc 存在与实现不符的注释
3. **命名映射未文档化**：VncBridgeTransport 的 agentId/deviceId 与 VncTarget 的 resourceId/pcClientId 无注释说明
4. **文件头职责与依赖不完整**：多数文件头未列出依赖模块

建议按优先级逐步修复，优先处理 Critical 与 Major 项，确保后续维护者能快速理解 Phase 4 的职责边界与调用关系。
