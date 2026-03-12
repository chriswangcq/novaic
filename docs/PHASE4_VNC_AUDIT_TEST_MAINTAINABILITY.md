# Phase 4 VNC 收敛 — 测试与可维护性审核报告

**审核范围**：novaic-app Phase 4 相关新增与修改文件  
**审核日期**：2025-03-12  
**审核重点**：单元测试、可测性、注释文档、魔法数字、错误信息、组件臃肿

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
| `src-tauri/src/commands/vnc_bridge.rs` | Rust 后端 | 219 |
| `src-tauri/src/vnc_proxy.rs` | Rust 后端 | 643 |

---

## 二、问题列表（按严重程度）

### Critical（严重）

| 编号 | 问题 | 文件 | 描述 |
|------|------|------|------|
| **C1** | **无任何单元测试** | 全项目 | `novaic-app` 下无 `.test.ts` / `.spec.ts` 文件。Vitest、@testing-library/react 已安装，但 package.json 无 `test` 脚本，vite.config.ts 无 vitest 配置。关键路径完全无覆盖。 |
| **C2** | **createVncTransport 不可测** | vncTransport.ts | 直接依赖 `invoke`、`shouldUseVncBridge`、`VncBridgeTransport`，无依赖注入。无法在无 Tauri 环境下单测分支逻辑。 |
| **C3** | **useVnc 不可测** | useVnc.ts | 依赖 RFB（DOM）、`useDeviceStatusStore`、`containerRef`。重连逻辑（指数退避、MAX_RETRIES）内嵌在 Hook 中，无法单独验证。 |
| **C4** | **VncBridgeTransport 不可测** | vncBridge.ts | 依赖 `invoke`、`listen`，connect/send/close 全为异步 Tauri 调用。无法 mock 验证连接/断开流程。 |
| **C5** | **transport 切换时 VncBridgeTransport 可能泄漏** | useVnc.ts | 当 transport 从 A 切换到 B 时，effect 会 doConnect 创建新 RFB，但旧 VncBridgeTransport 的 `close()` 仅在 `disconnect()` 中调用；transport 切换不会触发 disconnect，导致 Bridge 连接累积。 |

---

### Major（重要）

| 编号 | 问题 | 文件 | 描述 |
|------|------|------|------|
| **M1** | **魔法数字与 config 不一致** | useVnc.ts, DeviceDesktopView.tsx, config | `useVnc` 使用 `RETRY_DELAY_MS=2000`，而 `config/WS_CONFIG.VNC_RECONNECT_DELAY` 为 500，语义重叠但数值不同，易混淆。`DeviceDesktopView` 第 116 行 `setTimeout(r, 2000)` 与 `VM_CONFIG.START_WAIT_DELAY: 3000` 不一致，应统一使用 config。 |
| **M2** | **重连参数未集中配置** | useVnc.ts | `RETRY_DELAY_MS`、`MAX_RETRIES`、指数退避基数 2 均在 useVnc 内硬编码。config 已有 `WS_CONFIG.VNC_RECONNECT_DELAY`，但未被使用。建议在 config 中增加 `VNC_RETRY_DELAY_MS`、`VNC_MAX_RETRIES`、`VNC_BACKOFF_BASE`。 |
| **M3** | **renderOverlay 重复实现** | AgentDesktopView.tsx, DeviceDesktopView.tsx | 两处 `renderOverlay` 逻辑几乎相同（connecting/failed/reconnecting/disconnected UI），仅文案略有差异。修改需改两处，易遗漏。应抽取 `VncConnectionOverlay` 组件。 |
| **M4** | **DeviceDesktopView 过于臃肿** | DeviceDesktopView.tsx | 348 行，包含 maindesk 启停、vm_user 工具栏、多种 overlay、startDevice/stopDevice。建议拆分为：`DeviceDesktopMainView`、`DeviceDesktopVmUserView`、`VncConnectionOverlay`、`DeviceStartStopOverlay`。 |
| **M5** | **错误信息过于笼统** | useVnc.ts, vncTransport, AgentDesktopView | "Connection lost, max retries exceeded" 无重试次数、无最后错误详情；"RFB connection failed" 无上下文；"Failed to create transport" 无区分 Bridge vs URL 失败。不利于线上排查。 |
| **M6** | **incrementVnc/decrementVnc effect 可能重复执行** | useVnc.ts | 依赖 `[status, incrementVnc, decrementVnc]`。Zustand selector 返回函数时可能每次新引用，导致 effect 多次执行，`vncConnectionCount` 偏大。 |
| **M7** | **vncTarget 变化时 transport 未立即清空** | DeviceDesktopView.tsx | effect 中 `createVncTransport` 异步，在 resolve 前旧 transport 仍传给 VncCanvas，导致短暂「旧画面 + 新目标」重叠。应在 effect 开头立即 `setTransport(null)`。 |

---

### Minor（轻微）

| 编号 | 问题 | 文件 | 描述 |
|------|------|------|------|
| **m1** | **buildVncTarget 无 JSDoc** | DeviceDesktopView.tsx | `buildVncTarget` 对 vm_user 的 `pcClientId` 可选及 fallback 行为无说明，后续维护者易误解。 |
| **m2** | **VncTarget 类型注释不完整** | types/vnc.ts | `subjectType: 'default'` 的语义及与 main/vm_user 的区别未文档化。 |
| **m3** | **VncCanvas 未使用 React.memo** | VncCanvas.tsx | 父组件重渲染时连带重渲染，`renderOverlay` 常为内联，易导致不必要更新。 |
| **m4** | **useVnc 初始 status 不准确** | useVnc.ts | 初始为 `'connecting'`，但 `transport` 为 null 时实际应为 `'disconnected'`。 |
| **m5** | **VncTransport 类型守卫分散** | useVnc.ts, vncTransport.ts | `typeof t !== 'string' && 'close' in t` 多处重复。应定义 `isBridgeTransport(t)` 类型守卫函数统一使用。 |
| **m6** | **deviceCache 无大小限制** | useAgentDevice.ts | 模块级 Map 无 maxSize、无 LRU，长时间使用可能内存持续增长。 |
| **m7** | **CACHE_TTL_MS 未使用 config** | useAgentDevice.ts | `30_000` 硬编码，config 中无对应项。 |
| **m8** | **Rust vnc_bridge 错误信息可增强** | vnc_bridge.rs | "VNC bridge {id} not found" 可补充 bridge 已关闭的可能原因，便于排查。 |
| **m9** | **DeviceVNCView Linux/Android 分支不对称** | DeviceVNCView.tsx | Linux 直接返回 DeviceDesktopView，Android 在组件内维护 status/start/stop，结构不一致，可读性一般。 |

---

### Info（建议）

| 编号 | 问题 | 文件 | 描述 |
|------|------|------|------|
| **i1** | **doConnect 依赖 containerRef 但 effect 不依赖** | useVnc.ts | 若容器延迟挂载（如 display:none），effect 不会重跑，可能永远不连接。可考虑 ResizeObserver 或 containerReady state。 |
| **i2** | **doConnect 依赖 scaleViewport 等会触发重连** | useVnc.ts | 用户调整 viewOnly 等会触发完整重连。若 RFB 支持运行时更新，可热更新而不重连。 |
| **i3** | **package.json 无 test 脚本** | package.json | 建议增加 `"test": "vitest"`、`"test:run": "vitest run"`。 |
| **i4** | **vite.config 无 vitest 配置** | vite.config.ts | 需添加 `defineConfig` 的 `test` 块，配置 `environment`、`globals`、`include` 等。 |

---

## 三、可测性分析

### 3.1 关键路径可测性

| 路径 | 可测性 | 阻碍因素 |
|------|--------|----------|
| `createVncTransport` 分支（Bridge vs URL） | ❌ 不可测 | 依赖 `invoke`、`shouldUseVncBridge`，无 DI |
| `useVnc` 重连逻辑（2s 起、5 次、指数退避） | ❌ 不可测 | 内嵌在 Hook，依赖 RFB、DOM、store |
| `VncBridgeTransport.connect/close` | ❌ 不可测 | 依赖 `invoke`、`listen` |
| `buildVncTarget` | ⚠️ 可测 | 纯函数，但当前无测试 |
| `bindingToVncTarget` | ⚠️ 可测 | 纯函数，但当前无测试 |

### 3.2 建议的可测性改进

1. **createVncTransport**：抽离 `resolveTransportMode(target) => 'bridge' | 'url'`，将 `invoke` 封装为可注入的 `vncTransportResolver`，便于 mock。
2. **useVnc**：将重连逻辑抽到 `computeRetryDelay(attempt, baseMs, maxRetries)` 纯函数，单独单测；Hook 内仅调用该函数。
3. **VncBridgeTransport**：将 `invoke`/`listen` 通过构造函数注入，或提供 `createMockVncBridgeTransport()` 供测试使用。
4. **buildVncTarget / bindingToVncTarget**：立即补充单元测试，验证 main/vm_user/default 分支。

---

## 四、魔法数字汇总

| 值 | 位置 | 建议 |
|----|------|------|
| 2000 | useVnc RETRY_DELAY_MS | 移至 config，与 WS_CONFIG 对齐或新增 VNC_RETRY_* |
| 5 | useVnc MAX_RETRIES | 移至 config |
| 2 | useVnc 指数退避基数 | 移至 config 或注释说明 |
| 2000 | DeviceDesktopView startDevice 等待 | 使用 VM_CONFIG.START_WAIT_DELAY (3000) 或新增 DEVICE_START_POLL_DELAY |
| 30_000 | useAgentDevice CACHE_TTL_MS | 移至 config |
| 64 | vnc_bridge.rs mpsc channel | 可提取为常量并注释 |
| 4*60, 30 | vnc_proxy.rs CONN_TTL, WS_UPGRADE_TIMEOUT | 已提取，可考虑与 config 对齐 |

---

## 五、错误信息改进建议

| 当前 | 建议 |
|------|------|
| "Connection lost, max retries exceeded" | "VNC connection lost after {n} retries. Last error: {detail}" |
| "RFB connection failed" | "RFB connection failed: {message}. Transport: {bridge|url}" |
| "Failed to create transport" | "Failed to create VNC transport: {message}. Mode: {bridge|url}" |
| "VNC requires credentials (unexpected)" | 保持，或补充 "VNC server requested credentials but none were provided" |
| ctx.errorMsg \|\| 'Connection lost' | 避免空时用通用文案，可显示 "No error details" 或保留最后错误 |

---

## 六、组件拆分建议

| 当前组件 | 建议拆分 |
|----------|----------|
| DeviceDesktopView (348 行) | `DeviceDesktopMainView`（maindesk + start/stop）、`DeviceDesktopVmUserView`（vm_user 工具栏 + VncCanvas）、`VncConnectionOverlay`、`DeviceStartStopOverlay` |
| AgentDesktopView (168 行) | 抽取 `VncConnectionOverlay`，保留主逻辑 |
| renderOverlay 重复 | 统一使用 `VncConnectionOverlay`，通过 props 传入 onRetry、文案差异 |

---

## 七、修复优先级建议

| 优先级 | 问题编号 | 说明 |
|--------|----------|------|
| P0 | C1–C5 | 建立测试基础设施，修复资源泄漏 |
| P1 | M1, M2, M5, M7 | 统一配置、改进错误信息、修复状态清理 |
| P2 | M3, M4, M6 | 抽取重复组件、拆分臃肿组件、修复 store effect |
| P3 | m1–m9, i1–i4 | 注释完善、类型守卫、memo、config 对齐 |

---

## 八、总结

Phase 4 VNC 收敛在架构分层（传输/会话/展示）上设计合理，但**测试与可维护性存在明显短板**：

1. **测试**：无单元测试、无测试脚本、关键路径不可测，回归风险高。
2. **魔法数字**：部分已提取（RETRY_DELAY_MS、MAX_RETRIES），但与 config 不一致，且 DeviceDesktopView 等仍有硬编码。
3. **错误信息**：多数为通用文案，缺少上下文，不利于排查。
4. **组件**：DeviceDesktopView 臃肿，renderOverlay 重复，建议拆分。
5. **可测性**：createVncTransport、useVnc、VncBridgeTransport 均强依赖 Tauri/DOM，需通过依赖注入或纯函数抽取才能单测。

**建议**：优先建立 vitest 配置与 test 脚本，为 `buildVncTarget`、`bindingToVncTarget`、重连延迟计算等纯逻辑补充单测；同时修复 C5 资源泄漏，并将魔法数字统一到 config。
