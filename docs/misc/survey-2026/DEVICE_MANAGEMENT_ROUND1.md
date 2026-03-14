# NovAIC Device 管理数据流与组件调研（Round 1）

**调研日期**：2026-03-12  
**输入范围**：`api.ts`（devices）、`components/VM/`、`hooks/useDevice*.ts`、`stores/deviceStatusStore.ts`

---

## 1. 数据模型

### 1.1 Device 按 User 组织

- **Device** 归属当前用户（User），不直接归属 Agent
- 列表 API：`api.devices.listForUser()` → `GET /api/devices`，返回当前用户下所有设备
- 创建 API：`createLinuxForUser`、`createAndroidForUser`，无需 agentId

### 1.2 Agent 通过 Binding 引用 Device

- **AgentDeviceBinding**：Agent 与 Device 的关联，包含：
  - `agent_id`, `device_id`
  - `subject_type`: `'main' | 'vm_user' | 'default'`（主桌面 / VM 子用户 / Android）
  - `subject_id`: vm_user 时为 username
  - `mounted_tools`, `supported_tools`
- API：
  - `api.getAgentBinding(agentId)` → `GET /api/agents/{id}/binding`
  - `api.setAgentBinding(agentId, data)` → `PUT /api/agents/{id}/binding`
  - `api.clearAgentBinding(agentId)` → `DELETE /api/agents/{id}/binding`
- **已废弃**：`AICAgent.devices`、`api.devices.list(agentId)`（该 API 不存在 404）

### 1.3 Device 类型与 Subject

| 类型 | subject_type | 说明 |
|------|--------------|------|
| Linux | main | 主桌面 |
| Linux | vm_user | 子用户桌面（需 subject_id=username） |
| Android | default | Scrcpy 投屏 |

---

## 2. API 调用链

### 2.1 设备列表

| API | 路径 | 用途 |
|-----|------|------|
| `devices.listForUser()` | `GET /api/devices` | 当前用户所有设备，DeviceManagerPage / AgentDrawer 主数据源 |

### 2.2 设备详情

| API | 路径 | 用途 |
|-----|------|------|
| `devices.get(deviceId)` | `GET /api/devices/{id}` | 单设备详情，useDeviceVncTarget / useAgentDevice 使用 |

### 2.3 设备生命周期

| API | 路径 | 用途 |
|-----|------|------|
| `devices.start(deviceId, pcClientId?)` | `POST /api/devices/{id}/start` | 启动设备 |
| `devices.stop(deviceId, pcClientId?)` | `POST /api/devices/{id}/stop` | 停止设备 |
| `devices.status(deviceId, pcClientId?)` | `GET /api/devices/{id}/status` | 获取状态（轮询用） |
| `devices.setup(deviceId, data?, pcClientId?)` | `POST /api/devices/{id}/setup` | 初始化 |
| `devices.delete(deviceId, pcClientId?)` | `DELETE /api/devices/{id}` | 删除 |

### 2.4 其他

| API | 路径 | 用途 |
|-----|------|------|
| `vmUsers.list(deviceId)` | `GET /api/devices/{id}/vm-users` | Linux 设备子用户列表 |
| `vmUsers.create/delete/restartVnc` | - | VM 子用户管理 |
| `devices.getSubjects(deviceId)` | `GET /api/devices/{id}/subjects` | 设备 subjects |
| `devices.getToolCapabilities(...)` | - | 工具能力 |

---

## 3. 组件与数据源

### 3.1 DeviceManagerPage

- **路径**：`components/VM/DeviceManagerPage.tsx`
- **数据源**：
  - 设备列表：`api.devices.listForUser()`，load 后写入 `deviceManagerDevices`（AppStore）
  - 选中设备：`selectedDeviceId`（AppStore）→ 优先从 devices 查找，否则 `api.devices.get(selectedDeviceId)`
- **状态轮询**：`useDeviceStatusPolling(devices)`，自驱动，不依赖 AgentDrawer
- **状态展示**：`useDeviceStatus(deviceId, pcClientId)` 覆盖 device.status（避免 listForUser 缓存滞后）
- **子组件**：DeviceListPanel、DeviceVNCView、DeviceDesktopView、AddLinuxVMUserModal、AddAndroidModal

### 3.2 DeviceFloatingPanel

- **路径**：`components/Layout/DeviceFloatingPanel.tsx`
- **两种模式**：
  1. **Agent 模式**：`useAgentBinding(agentId, agent.binding)` → binding + `devices.get(binding.device_id)`
  2. **deviceMode**：`useDeviceVncTarget(deviceId, subjectType, subjectId)` → 纯 Device 体系，不依赖 Agent
- **状态**：`useDeviceStatusPolling(device ? [device] : [])` + `useDeviceStatus`
- **渲染**：main → VNCViewShared，vm_user → DeviceDesktopView，default → ScrcpyView

### 3.3 useDeviceVncTarget

- **路径**：`hooks/useDeviceVncTarget.ts`
- **用途**：纯 Device 体系的 VncTarget 获取，不依赖 Agent
- **输入**：`deviceId`, `subjectType`, `subjectId?`
- **数据流**：`api.devices.get(id)` → 构造 `VncTarget { resourceId, subjectType, deviceId, username?, pcClientId? }`
- **使用方**：DeviceFloatingPanel（deviceMode）、DeviceManagerPage 间接通过 DeviceVNCView

### 3.4 useAgentDevice

- **路径**：`hooks/useAgentDevice.ts`
- **用途**：Agent 绑定设备与 VncTarget 的组合查询
- **数据流**：`api.getAgentBinding(agentId)` → `api.devices.get(binding.device_id)`（带 30s 缓存）→ `bindingToVncTarget`
- **使用方**：AgentDesktopView、VisualPanel、AgentDrawer（Devices 列表高亮）

### 3.5 useAgentBinding

- **路径**：`hooks/useAgentBinding.ts`
- **用途**：获取 Agent 的 binding + device，可复用 agent 列表中的 initialBinding 避免额外请求
- **数据流**：`initialBinding ?? getAgentBinding` → `devices.get(binding.device_id)`
- **使用方**：DeviceFloatingPanel（Agent 模式）

---

## 4. DeviceStatusStore 与 useDeviceStatusPolling 现状

### 4.1 DeviceStatusStore

- **路径**：`stores/deviceStatusStore.ts`
- **职责**：统一设备状态管理，将分散的 status 轮询收敛到此 store
- **状态**：
  - `statuses: Map<string, DeviceStatusEntry>`，key 为 `deviceId` 或 `deviceId:pcClientId`（多 PC）
  - `subscriberCount`：订阅计数（当前未用于动态间隔）
  - `vncConnectionCount`：VNC 连接数，>0 时轮询间隔降为 3s
- **方法**：`setStatus`、`setStatuses`、`getStatus`、`subscribeDevice`、`incrementVncConnectionCount`、`decrementVncConnectionCount`

### 4.2 useDeviceStatusPolling

- **路径**：`hooks/useDeviceStatusPolling.ts`
- **输入**：`devices: Device[]`，`enabled = true`
- **行为**：
  - 对每个 device 调用 `api.devices.status(id, pc_client_id)`
  - 结果写入 `DeviceStatusStore.setStatuses`
  - 间隔：`vncConnectionCount > 0` → 3s，否则 5s（`POLL_CONFIG.VM_STATUS_FAST/NORMAL_INTERVAL`）
- **使用方**：
  - DeviceManagerPage：`useDeviceStatusPolling(devices, devices.length > 0)`
  - DeviceFloatingPanel：`useDeviceStatusPolling(device ? [device] : [], !!device)`
  - AgentDrawer：`useDeviceStatusPolling(devices, isOpen && devices.length > 0)`

### 4.3 useDeviceStatus

- **路径**：`hooks/useDeviceStatus.ts`
- **用途**：从 DeviceStatusStore 读取单个设备状态
- **输入**：`deviceId`, `pcClientId?`
- **使用方**：DeviceManagerPage（DeviceRow、VmUsersSection）、DeviceFloatingPanel

### 4.4 现状小结

| 项目 | 现状 |
|------|------|
| 轮询入口 | 多处独立：DeviceManagerPage、DeviceFloatingPanel、AgentDrawer 各自传入 devices 并启动轮询 |
| 数据源 | 列表来自 `listForUser`，AgentDrawer 与 DeviceManagerPage 各自 load，通过 `deviceManagerDevices` 共享 |
| 状态覆盖 | 组件优先用 `useDeviceStatus`（Store）覆盖 device.status，避免 listForUser 30s 缓存滞后 |
| VNC 加速 | `vncConnectionCount` 控制轮询间隔，需在 VNC 连接时 increment、断开时 decrement |

---

## 5. 数据流简图

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    api.devices                            │
                    │  listForUser / get / start / stop / status                 │
                    └─────────────────────────────────────────────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         │                                │                                │
         ▼                                ▼                                ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ DeviceManagerPage│            │ DeviceFloatingPanel          │   AgentDrawer   │
│ listForUser()    │            │ agentBinding / deviceVncTarget│ listForUser()   │
│ useDeviceStatus  │            │ useDeviceStatus               │ useAgentDevice  │
│ Polling          │            │ Polling                       │ Polling        │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                               │                              │
         └───────────────────────────────┼──────────────────────────────┘
                                         ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │              DeviceStatusStore                           │
                    │  statuses Map / setStatuses / getStatus                  │
                    └─────────────────────────────────────────────────────────┘
                                         ▲
                                         │
                    ┌────────────────────┴────────────────────┐
                    │     useDeviceStatusPolling              │
                    │  api.devices.status() → setStatuses()    │
                    └─────────────────────────────────────────┘
```

---

## 6. 相关文件索引

| 文件 | 说明 |
|------|------|
| `novaic-app/src/services/api.ts` | Device / Binding API 定义 |
| `novaic-app/src/types/index.ts` | Device、DeviceStatus、VmUser 类型 |
| `novaic-app/src/components/VM/DeviceManagerPage.tsx` | 设备管理主页面 |
| `novaic-app/src/components/VM/DeviceManagerModal.tsx` | 设备管理弹窗（旧） |
| `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | 设备浮窗 |
| `novaic-app/src/components/Layout/AgentDrawer.tsx` | 侧边抽屉（含 Devices 列表） |
| `novaic-app/src/hooks/useDeviceVncTarget.ts` | 纯 Device VncTarget |
| `novaic-app/src/hooks/useDeviceStatus.ts` | 从 Store 读状态 |
| `novaic-app/src/hooks/useDeviceStatusPolling.ts` | 统一轮询 |
| `novaic-app/src/hooks/useAgentDevice.ts` | Agent 绑定设备 + VncTarget |
| `novaic-app/src/hooks/useAgentBinding.ts` | Agent binding + device |
| `novaic-app/src/stores/deviceStatusStore.ts` | 设备状态 Store |
| `novaic-app/src/config/index.ts` | POLL_CONFIG 轮询间隔 |
