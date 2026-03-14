# NovAIC 统一优化方案

---

## 总体思路

当前系统的核心矛盾可以归结为三层语义没有对齐：**「谁拥有设备」（Device 归属）**、**「谁在哪运行」（AppInstance / PC Client 拓扑）**、**「连到哪个桌面」（VNC 目标寻址）**。方案的核心是把这三层关系显式建模，让每一层只做一件事，层间通过明确的 ID 映射串联。

改造顺序建议：**Device 模型 → AppInstance / 拓扑 → VNC 统一 → 前端收敛**，原因是后者依赖前者提供的语义基础。

---

## 一、Device 与 Binding 的统一模型

### 1.1 概念澄清与命名规范

当前最大的混乱来源是 `device_id` 在不同上下文中指代不同实体。建议在代码和 API 层面强制区分：

**logical_device_id**（简称 `device_id`）：`devices` 表主键，代表一个逻辑设备配置（Linux VM 或 Android AVD），归属于 User。这是业务层面的「设备」概念，前端 AgentDrawer、DeviceFloatingPanel 等展示的都是它。

**pc_client_id**（原 `pc_clients.device_id`）：物理机的 Ed25519 公钥派生标识，代表一台运行 VmControl 的物理 PC。建议将 `pc_clients` 表的主键列从 `device_id` 重命名为 `pc_client_id`，从源头消除歧义。

**app_instance_id**：一次应用运行实例的 UUID，生命周期等于进程生命周期，每次启动重新生成。它与 `pc_client_id` 是多对一关系（同一台物理机可以多次启动应用）。

在 VNC proxy 路径中，当前用的是物理机的标识来路由到正确的 VmControl 实例。建议路径语义改为 `/vnc/{pc_client_id}/{resource_id}`，让命名与实际含义一致。如果短期不想改路径，至少在代码注释和类型定义中标注清楚当前 `device_id` 参数实际是 `pc_client_id`。

### 1.2 前端数据流重构

当前 `api.devices.list(agentId)` 请求 `/api/agents/{id}/devices` 会 404，应该废弃。正确的前端数据获取模式是两步走：

**第一步：获取 Agent 的绑定关系。** 调用 `api.agents.getAgentBinding(agentId)` 返回 `{ device_id, subject_type, subject_id }`。这告诉前端「这个 Agent 操作哪个设备的哪个桌面」。

**第二步：获取设备详情。** 用 binding 中的 `device_id` 调用 `api.devices.get(device_id)` 获取设备的完整信息（名称、类型、状态、所属 PC 等）。

建议封装一个组合查询 hook `useAgentDevice(agentId)` 来包装这两步，返回 `{ binding, device, isLoading, error }`。这个 hook 内部做缓存和去重（同一个 device_id 被多个 Agent 引用时只请求一次），外部组件无需关心两步的细节。

对于 AgentDrawer 的 Devices tab，它展示的是用户的所有设备，继续使用 `listForUser()` 是正确的。但当用户选择某个 Agent 后，面板中展示的设备详情应该走 `useAgentDevice` 而不是从 `deviceManagerDevices` 列表中按 ID 查找，因为后者是全量列表，在设备很多时做列表扫描不必要，且可能存在时序问题（列表还没刷新但 binding 已经变了）。

### 1.3 subject_type 的前端协作

`subject_type` 决定了 VNC 连接目标的性质：`main` 表示 VM 主桌面，`vm_user` 表示子用户桌面，`default` 表示 Android 默认。建议在 `useAgentDevice` 的返回值中直接暴露一个 `vncTarget` 派生对象：

```typescript
type VncTarget = {
  pcClientId: string;       // 路由到哪台物理机
  resourceId: string;       // maindesk → device_id; subuser → `${deviceId}:${username}`
  subjectType: 'main' | 'vm_user' | 'default';
  deviceId: string;         // 逻辑设备 ID
  username?: string;        // vm_user 时有值
};
```

这样 VNC 组件只需要接收一个 `VncTarget`，不需要自己解析 binding 和拼接 resource_id。subject_type 的差异在这一层就被翻译成了统一的寻址结构。

---

## 二、AppInstance 与 Device 的关系简化

### 2.1 当前问题

`app_instance_id` 的设计意图是标识「当前这个 Tauri 客户端实例」，用于 my-devices 中区分「哪些设备在本机运行」。但实际上 `get_vnc_proxy_url` 和 `vnc_bridge_connect` 调用 my-devices 时没传 `current_device_id`，导致 `is_local` 标记形同虚设。

更根本的问题是层级关系不清晰。当前 my-devices 返回的数据混合了两个维度：「用户有哪些 PC Client 在线」和「每个 PC Client 上有哪些逻辑设备」。前端消费时需要同时理解这两个维度，增加了复杂度。

### 2.2 简化方案

建议将 my-devices 的语义收敛为**拓扑查询**——回答「我的设备分布在哪些物理机上，哪些在本机」这个问题。具体改动：

**Gateway 侧**：my-devices API 改为接受 `current_app_instance_id`（而非 `current_device_id`）作为查询参数，因为前端最容易拿到的就是自己的 app_instance_id。Gateway 通过 DeviceRegistry 查到该 app_instance_id 对应的 pc_client_id，然后标记 `is_local`。这避免了前端需要额外查询自己的 pc_client_id 的问题。

**前端侧**：Tauri setup 阶段生成 app_instance_id 后，存入一个全局 atom 或 context。所有需要判断「是否本机」的地方（VNC proxy URL 选择、bridge vs local 判断）统一从这个全局状态读取，调用 my-devices 时带上。`get_vnc_proxy_url` 和 `vnc_bridge_connect` 的调用方负责传入这个参数。

**职责边界**：`app_instance_id` 只用于标识「这次运行」和关联「哪台物理机」，不参与业务逻辑。`pc_client_id` 用于 VNC 路由和 P2P 寻址。`device_id` 用于一切业务操作（启动、停止、状态查询）。三者的映射关系通过 my-devices 拓扑查询一次获得，缓存在前端，设备上下线时通过 WebSocket 事件增量更新。

---

## 三、VNC 统一入口

### 3.1 核心思路：差异下沉到 VmControl

当前 maindesk 和 subuser 的差异分散在三个地方：前端组件（不同的 View 和 hook）、Tauri 命令层（vnc_proxy 路由）、VmControl（find_vnc_target）。目标是让前端和 Tauri 命令层完全不感知 maindesk/subuser 的区别，差异全部由 VmControl 内部处理。

**VmControl 改造**：引入一个统一的 VNC endpoint 分配机制。无论 maindesk 还是 subuser，VmControl 对外都暴露一个 Unix socket（或者统一为 TCP port），路径规范为 `/tmp/novaic/vnc-{resource_id}.sock`。对于 maindesk，这个 socket 直接连到 QEMU VNC；对于 subuser，VmControl 内部负责等待 Xvnc 启动、读取 port 文件、然后创建一个代理 socket。这样 tunnel 层的 `find_vnc_target` 逻辑简化为：根据 resource_id 查找对应的 socket，不再区分两种类型。

**具体实现**：VmControl 增加一个 `ensure_vnc_endpoint(resource_id) -> Result<SocketPath>` 方法，由它处理等待、重试、超时的逻辑。对于 subuser 场景，这个方法内部做轮询等待 port 文件出现（最多 30s，间隔 500ms），然后建立本地 socket 代理。失败时返回明确的错误（Xvnc 未启动、超时等），而不是让上层盲目重试。

**tunnel.rs 改造**：`find_vnc_target` 简化为调用 `ensure_vnc_endpoint`，拿到 socket path 后做通用的流转发。不再有 `if resource_id.contains(':')` 这样的分支。

### 3.2 前端统一连接策略

有了后端的统一 endpoint，前端的 VNC 连接逻辑可以大幅简化。统一的连接流程如下：

**阶段一：传输层建立。** 根据 `VncTarget` 中的 `pcClientId` 判断本机还是远程。本机走 `ws://localhost:{port}/vnc/{pc_client_id}/{resource_id}`（vnc_proxy），远程走 VNC Bridge（Cloud Relay）或 P2P QUIC。这个判断逻辑封装在一个 `createVncTransport(target: VncTarget)` 函数中，返回一个 WebSocket 或等效的双向流。

**阶段二：VNC 会话建立。** 传输层建立后，统一使用相同的 RFB 参数进行 VNC 握手。建议统一为：`shared: true`（允许多客户端观看）、`wsProtocols: ['binary']`、`credentials` 根据设备配置决定（有密码则传，无则不传）、`clipViewport: true`。当前 subuser 缺少 `shared` 和 `credentials` 是遗漏，应该补上。

**阶段三：生命周期管理。** 统一的重连策略——连接断开后等待 2s 重试，最多 5 次，指数退避。当前 maindesk 有自动重连但 subuser 没有，统一后都有。同时统一状态上报：`connecting → connected → disconnected → reconnecting → failed`，前端 UI 根据状态渲染，不关心是 maindesk 还是 subuser。

### 3.3 WebSocket 探测（Readiness Check）

当前 maindesk 有 WebSocket 探测（先探测 ws 是否可用再建立 VNC），subuser 没有。统一方案是：取消前端的 WebSocket 探测，改为依赖后端的 `ensure_vnc_endpoint` 返回。具体来说，传输层建立时如果后端 endpoint 还没 ready，WebSocket 连接会被后端 hold 住或拒绝。前端只需要处理连接失败然后重试，不需要额外的探测步骤。这样减少了一个不必要的网络往返，也消除了探测成功但实际连接失败的时序窗口。

如果考虑到用户体验（想在 VNC 画面出来之前就显示「正在等待设备启动」），可以让前端在连接前先查询 device status，status 为 running 时再发起 VNC 连接。这个 status 查询用统一的 `useDeviceStatus(deviceId)` hook 做轮询，而不是在 VNC 连接 hook 内部自己轮询。

---

## 四、前端组件收敛

### 4.1 目标架构

收敛为两层：

**通用层（与业务无关）**：一个 `useVnc(transport, rfbOptions)` hook，接收一个已建立的传输流和 RFB 参数，管理 VNC 会话生命周期（连接、重连、断开、状态上报）。一个 `<VncCanvas>` 纯展示组件，接收 vnc 会话对象，渲染画面和处理输入事件。

**业务层（与 Agent/Device 相关）**：一个 `<AgentDesktopView agentId={...}>` 组件，内部使用 `useAgentDevice(agentId)` 获取 VncTarget，用 `createVncTransport(target)` 建立传输，用 `useVnc` 管理会话，最终渲染 `<VncCanvas>`。它取代当前的 VNCView、DeviceVNCView、VmUserVNCView 三个组件。如果需要脱离 Agent 上下文直接查看某个设备（比如 DeviceFloatingPanel 场景），提供一个 `<DeviceDesktopView deviceId={...} subjectType={...} subjectId={...}>` 组件，逻辑类似但跳过 binding 查询，直接构造 VncTarget。

### 4.2 Hook 收敛映射

| 现有 | 收敛后 | 说明 |
|------|--------|------|
| `useVNCConnection` | `useVnc` | 通用 VNC 会话管理 |
| `useDeviceVNCConnection` | `useVnc` | 合并，传输层建立逻辑移到 `createVncTransport` |
| `vncStream` (共享流) | 保留但重构 | 作为 `createVncTransport` 的一种模式（共享同一个底层 WS） |
| `vmService.getVncTransport` | `createVncTransport` | 统一传输层工厂函数 |
| `vncBridge.shouldUseVncBridge` | 合并进 `createVncTransport` | 内部决策，不暴露给组件层 |

### 4.3 DeviceSidebar / DeviceFloatingPanel

这两个组件目前未实现。建议根据实际产品需求决定是否需要：如果产品需要一个常驻的设备侧边栏（类似 IDE 的文件树），实现 DeviceSidebar，数据源为 `listForUser()` + my-devices 拓扑（标注在线/离线/本机）。如果只需要在 Agent 上下文中快速查看设备信息，DeviceFloatingPanel 用一个 Popover 实现即可，数据源为 `useAgentDevice`。两者不应该有独立的轮询逻辑，而是订阅全局的设备状态 store。

### 4.4 状态轮询收敛

当前有三处独立的 status 轮询（5s、5s、3s），应该合并为一个全局的设备状态管理：

建议用一个 `DeviceStatusStore`（Zustand 或 Jotai atom）管理所有活跃设备的状态。该 store 维护一个 `Map<deviceId, DeviceStatus>`，通过一个统一的轮询循环（或 WebSocket 推送）更新。各组件通过 selector 订阅自己关心的 deviceId 的状态变化，不再各自起定时器。轮询间隔统一为 5s，VNC 连接期间可以降为 3s（通过 store 的 subscription count 动态调整）。

---

## 五、改造顺序与依赖关系

### Phase 1：Device 模型对齐（约 1-2 周）

这是基础，后续所有改动都依赖它。具体工作包括：后端将 `pc_clients.device_id` 列重命名为 `pc_client_id`，或至少在 API 响应和类型定义中使用 `pc_client_id` 字段名。前端引入 `VncTarget` 类型和 `useAgentDevice` hook。废弃 `api.devices.list(agentId)`，前端所有获取 Agent 关联设备的地方改用 `useAgentDevice`。引入全局 `DeviceStatusStore`，将分散的轮询合并。

**产出**：设备模型语义清晰，前端数据流统一，轮询收敛。
**风险**：改动面广但逻辑简单，主要是查找替换和类型调整。

### Phase 2：AppInstance / 拓扑（约 0.5-1 周）

依赖 Phase 1 的 `pc_client_id` 命名规范。修改 my-devices API 接受 `current_app_instance_id`。前端全局存储 app_instance_id，所有调用 my-devices 的地方带上该参数。验证 `is_local` 标记正确生效。修复 `get_pc_client_manager` 始终用第一个设备的问题——改为通过 `VncTarget.pcClientId` 显式指定目标。

**产出**：本机标注生效，多 PC 路由正确。
**风险**：较小，主要是参数传递链路的补全。

### Phase 3：VNC 后端统一（约 1-2 周）

依赖 Phase 1 的 `resource_id` 规范。VmControl 实现 `ensure_vnc_endpoint`，subuser 场景增加内部等待和代理。tunnel.rs 简化 `find_vnc_target`。统一 RFB 参数（后端配置化或者前端统一传入）。

**产出**：后端 VNC 入口统一，subuser 可靠性提升。
**风险**：中等，涉及 VmControl Rust 代码改动和 Xvnc 启动时序的处理，需要充分测试。

### Phase 4：前端 VNC 收敛（约 1-2 周）

依赖 Phase 3 的统一后端。实现 `createVncTransport`、`useVnc`、`<VncCanvas>`。实现 `<AgentDesktopView>` 和 `<DeviceDesktopView>`。迁移现有三个 VNC View 组件到新架构。删除旧的 `useVNCConnection`、`useDeviceVNCConnection`。根据产品需求决定 DeviceSidebar / DeviceFloatingPanel 的实现。

**产出**：前端 VNC 代码量减少约 40-50%，新增场景（如未来的 Android Scrcpy 桌面）只需实现新的 transport 类型。
**风险**：较大的前端重构，建议按组件逐个迁移并做 A/B 验证。

### 依赖关系图

```
Phase 1 (Device 模型)
  ├──→ Phase 2 (AppInstance)
  └──→ Phase 3 (VNC 后端)
            └──→ Phase 4 (前端收敛)
```

Phase 2 和 Phase 3 可以并行推进，Phase 4 需要等 Phase 3 完成。整体周期约 4-6 周，取决于团队并行度和测试周期。

---

## 六、关键设计决策摘要

**Q: 是否需要新的 API endpoint？**
不需要新增 endpoint，但需要修改 my-devices 的查询参数（加 `current_app_instance_id`），以及对 `pc_clients` 的字段命名做调整。现有的 `GET /api/devices`、`GET /api/devices/{id}`、`GET /api/agents/{id}/binding` 已经足够。

**Q: vncStream（共享流）是否保留？**
保留概念但重构实现。共享流的本质是「同一个 VNC 目标只建一条底层连接」，这在多个 UI 组件需要同时显示同一个桌面时有价值。将其作为 `createVncTransport` 的内部优化（引用计数 + 连接复用），外部不感知。

**Q: P2P vs Cloud Bridge 的选择逻辑放在哪里？**
放在 `createVncTransport` 内部。它先通过 my-devices 拓扑判断目标 PC 是否可 P2P 直连，不行则 fallback 到 Cloud Bridge。这个决策过程对 VNC 组件层完全透明。

**Q: Android（Scrcpy）场景如何适配？**
当前方案主要覆盖 Linux VM 的 VNC。Android/Scrcpy 是不同的协议，但 `VncTarget` 结构可以扩展为更通用的 `RemoteDisplayTarget`，增加 `protocol: 'vnc' | 'scrcpy'` 字段。`createVncTransport` 改为 `createDisplayTransport`，根据 protocol 走不同的传输层实现。组件层对应地从 `<VncCanvas>` 扩展为 `<RemoteDisplay>` 内部分发。这是未来扩展方向，当前阶段不需要实现，但架构上预留即可。
