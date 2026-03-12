# 激进修复设计：Agent 与 Device 体系分离

> 核心原则：**Agent 是一套独立的体系**，Device/VNC 层不应混用 Agent 语义。当前代码中 agentId 被滥用为 resourceId，导致概念混淆。

---

## 一、问题现状

### 1.1 语义混淆

| 层级 | 当前命名 | 实际含义 | 问题 |
|------|----------|----------|------|
| **业务层** | agentId | Agent 实体 ID（agents 表） | 正确 |
| **VNC 层** | agentId | resourceId（device_id 或 device_id:username） | **错误** |
| **Tauri** | agentId 参数 | resourceId | **错误** |
| **vncStream** | agentId | stream key（= resourceId） | **错误** |
| **vm.ts** | agentId | 混用：start/stop 用 agentId；getVncUrl 用 resourceId | **错误** |

### 1.2 依赖错位

| 组件 | 当前依赖 | 问题 |
|------|----------|------|
| **DeviceManagerPage** | useAgentDevice | 设备管理应 Device 优先，Agent 仅作「高亮」 |
| **DeviceFloatingPanel** | useAgentBinding | 完全依赖 Agent，无 Agent 则不渲染 |
| **vncStream** | 参数名 agentId | 语义为 resourceId，与 Agent 无关 |

### 1.3 边界不清

- **Agent 体系**：Agent 列表、Chat、Binding、模型、技能、日志等
- **Device 体系**：设备列表、设备详情、启动/停止、VNC、Scrcpy
- **当前**：Device 管理入口依赖 currentAgentId；VNC 层参数名 agentId

---

## 二、设计原则

### 2.1 体系分离

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Agent 体系（独立）                    Device 体系（独立）                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • agents 表                           • devices 表                               │
│  • getAgentBinding(agentId)            • listForUser() / devices.get(deviceId)  │
│  • Agent 列表、Chat、Binding           • 设备列表、启动/停止、VNC、Scrcpy          │
│  • 仅通过 Binding 引用 Device          • 不依赖 Agent 的 device_id               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 桥接层
                                    ▼
                    ┌───────────────────────────────────┐
                    │  bindingToVncTarget(binding, device)│
                    │  仅在「Agent 上下文」需要时调用      │
                    └───────────────────────────────────┘
```

### 2.2 命名规范

| 语义 | 正确命名 | 禁止命名 |
|------|----------|----------|
| Agent 实体 ID | agentId | - |
| 逻辑设备 ID | deviceId | - |
| VNC 资源标识 | resourceId | agentId |
| 物理 PC 标识 | pcClientId | deviceId（在 VNC 路由上下文中） |
| stream 键 | streamKey / resourceId | agentId |

---

## 三、激进修复方案

### 3.1 阶段一：VNC 层去 agentId 化（P0）

**目标**：VNC/Device 相关代码中，凡与 Agent 无关的，一律改用 resourceId / streamKey / pcClientId。

#### 3.1.1 Tauri 命令

| 文件 | 当前 | 修改 |
|------|------|------|
| vnc_urls.rs | `agentId`, `deviceId` | `resourceId`, `pcClientId` |
| vnc_bridge.rs | `agentId`, `deviceId` | `resourceId`, `pcClientId` |
| vnc_proxy.rs | 路径 `agent_id` | 路径 `resource_id`（注释已说明 device_id=pc_client_id） |

**兼容**：前端 invoke 时参数名改为 resourceId/pcClientId；旧参数名保留 1 个版本周期后删除。

#### 3.1.2 前端服务

| 文件 | 修改 |
|------|------|
| vncTransport.ts | createVncTransport(target) 已用 VncTarget，无需改 |
| vncBridge.ts | `VncBridgeTransport(resourceId, pcClientId)`，构造函数参数名 |
| vncStream.ts | `subscribeToVNCStream(streamKey, subscriber, pcClientId)`，全部 API 参数名 |
| vm.ts | `getVncUrl(resourceId, pcClientId)`，`getVncTransport(resourceId, pcClientId)`，注释明确 agentId 仅用于 start/stop（Gateway 解析） |

#### 3.1.3 vm.ts 的 agentId 澄清

- **start(agentId)**、**stop(agentId)**、**getStatus(agentId)**：Gateway 的 `/api/vm/status/{agentId}` 等，**这里 agentId 是业务 Agent**，Gateway 通过 binding 解析 device_id。保留。
- **getVncUrl(resourceId, pcClientId)**、**getVncTransport(resourceId, pcClientId)**：VNC 层，参数改为 resourceId/pcClientId。

### 3.2 阶段二：Device 管理去 Agent 优先（P1）

**目标**：Device 管理入口以 Device 为主，Agent 仅作「高亮/回退」辅助。

#### 3.2.1 DeviceManagerPage

| 当前 | 修改 |
|------|------|
| 数据源：`selectedDeviceId` + `useAgentDevice` 回退 | 数据源：`selectedDeviceId` + `devices.get` 为主 |
| 当 selectedDeviceId === agentDevice?.id 时用 agentDevice | 改为：`devices.get(selectedDeviceId)` 为主；`useAgentDevice` 仅用于 `isAgentDevice` 高亮，不替代数据源 |

**理由**：设备详情应来自 devices API，不依赖 Agent 绑定。Agent 的 agentDevice 仅用于「这是当前 Agent 绑定的设备」的 UI 标识。

#### 3.2.2 DeviceFloatingPanel

| 当前 | 修改 |
|------|------|
| 完全依赖 useAgentBinding，无 Agent 不渲染 | **选项 A**：保持 Agent 上下文，但明确命名为「Agent 绑定设备预览」 |
| | **选项 B**：支持 Device 模式，传入 deviceId + subjectType + subjectId，不依赖 Agent |

**建议**：选项 B。新增 `DeviceFloatingPanel` 的 `deviceMode`：当 `deviceId` 直接传入时，用 `devices.get(deviceId)` + subject 构造 VncTarget，不查 AgentBinding。

#### 3.2.3 Agent 上下文组件

**保留 Agent 依赖**的组件（明确为 Agent 体系）：

- AgentDesktopView：`useAgentDevice(agentId)` → 展示「当前 Agent 绑定的设备桌面」
- VisualPanel：Agent 的 Chat 主区，需知道当前 Agent 绑定的设备类型
- AgentDrawer Devices tab：高亮「当前 Agent 绑定的设备」

这些组件的**数据源**是 Agent → Binding → Device，是合理的 Agent 体系逻辑。

### 3.3 阶段三：新增 Hook 与 API 分离（P2）

#### 3.3.1 useDeviceVncTarget

**新增**：`useDeviceVncTarget(deviceId, subjectType, subjectId?)` — 纯 Device 体系，不依赖 Agent。

```typescript
// 输入：deviceId, subjectType, subjectId (vm_user 时)
// 输出：Device | null, VncTarget | null, isLoading, error
// 数据源：devices.get(deviceId) → 构造 VncTarget
```

用于：DeviceManagerPage 的 Device 模式、DeviceFloatingPanel 的 deviceMode。

#### 3.3.2 useAgentDevice 保留

**用途**：仅 Agent 体系。输入 agentId，输出 binding + device + vncTarget。用于 AgentDesktopView、VisualPanel、AgentDrawer 高亮。

#### 3.3.3 API 命名

| 当前 | 修改 |
|------|------|
| vmService.getVncTransport(agentId, deviceId?) | vmService.getVncTransport(resourceId, pcClientId?) |
| vmService.getVncUrl(agentId, deviceId?) | vmService.getVncUrl(resourceId, pcClientId?) |
| subscribeToVNCStream(agentId, ...) | subscribeToVNCStream(streamKey, ..., pcClientId?) |
| reconnectVNCStream(agentId, deviceId?) | reconnectVNCStream(streamKey, pcClientId?) |

---

## 四、实施顺序

| 阶段 | 内容 | 风险 |
|------|------|------|
| **P0** | 重命名：vncStream、vncBridge、vm、Tauri 的 agentId→resourceId | 低，主要是参数名 |
| **P1** | DeviceManagerPage 数据源改为 devices.get 为主 | 中，需验证缓存与 freshness |
| **P2** | 新增 useDeviceVncTarget，DeviceFloatingPanel 支持 deviceMode | 中 |

---

## 五、命名对照表（实施后）

| 上下文 | 参数/变量 | 含义 |
|--------|----------|------|
| Agent 体系 | agentId | Agent 实体 ID |
| Device 体系 | deviceId | 逻辑设备 ID |
| VNC 层 | resourceId | maindesk: device_id；subuser: device_id:username |
| VNC 层 | pcClientId | 物理 PC 标识 |
| vncStream | streamKey | 与 resourceId 同义，用于 stream 管理 |
| Tauri | resource_id | URL 路径，VNC 资源 |
| Tauri | pc_client_id | 路由目标 |

---

## 六、附录：需修改文件清单

### P0
- `novaic-app/src/services/vncStream.ts` — 参数 agentId → streamKey
- `novaic-app/src/services/vncBridge.ts` — agentId → resourceId
- `novaic-app/src/services/vm.ts` — getVncUrl/getVncTransport 参数
- `novaic-app/src-tauri/src/commands/vnc_urls.rs` — 参数名
- `novaic-app/src-tauri/src/commands/vnc_bridge.rs` — 参数名
- `novaic-app/src/components/Visual/VNCViewShared.tsx` — subscribeToVNCStream 调用处

### P1
- `novaic-app/src/components/VM/DeviceManagerPage.tsx` — 数据源逻辑
- `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` — 可选 deviceMode

### P2
- 新增 `novaic-app/src/hooks/useDeviceVncTarget.ts`
