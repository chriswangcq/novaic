# Device 管理数据流概览（第一轮调研·浅层）

## 1. Device 相关 API

| API | 前端调用 | Gateway 路径 | Tauri Invoke |
|-----|----------|-------------|--------------|
| **listForUser** | `api.devices.listForUser()` | `GET /api/devices` | `gateway_get` |
| **devices.get** | `api.devices.get(deviceId)` | `GET /api/devices/{device_id}` | `gateway_get` |
| **devices.start** | `api.devices.start(deviceId, pcClientId?)` | `POST /api/devices/{device_id}/start` | `gateway_post` |
| **devices.stop** | `api.devices.stop(deviceId, pcClientId?)` | `POST /api/devices/{device_id}/stop` | `gateway_post` |
| **devices.status** | `api.devices.status(deviceId, pcClientId?)` | `GET /api/devices/{device_id}/status` | `gateway_get` |

**代码位置**：
- 前端 API 定义：`novaic-app/src/services/api.ts` L1040-1163
- Gateway 路由：`novaic-gateway/gateway/api/devices.py` L228-524
- Tauri 命令：`novaic-app/src-tauri/src/commands/gateway.rs`（gateway_get/post/patch/delete）

---

## 2. Device 数据来源

### 2.1 Gateway 路径

| 用途 | 路径 | 方法 |
|------|------|------|
| 用户设备列表 | `/api/devices` | GET |
| 设备详情 | `/api/devices/{device_id}` | GET |
| 启动设备 | `/api/devices/{device_id}/start` | POST |
| 停止设备 | `/api/devices/{device_id}/stop` | POST |
| 设备状态 | `/api/devices/{device_id}/status` | GET |

### 2.2 Tauri Invoke 链路

```
前端 api.ts
    ↓ invoke('gateway_get', { path: '/api/devices' })
    ↓ invoke('gateway_post', { path: '/api/devices/{id}/start' })
Tauri commands/gateway.rs
    ↓ gateway_get_impl(url, token, path)
    ↓ make_gateway_client(url, token).get/post(path)
Gateway (gateway_url.txt 或默认 https://api.gradievo.com)
```

- **gateway_get**：`path` → `{base_url}{path}`，带 JWT
- **gateway_post**：同上，带 body

---

## 3. Device 管理相关组件

| 组件 | 文件路径 | 数据源 | 说明 |
|------|----------|--------|------|
| **DeviceManagerPage** | `novaic-app/src/components/VM/DeviceManagerPage.tsx` | `listForUser` + `devices.get` | Main 区设备管理页，列表 + 详情 + VNC |
| **DeviceFloatingPanel** | `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | `useAgentBinding` → `getAgentBinding` + `devices.get` | Agent 绑定设备浮窗，start/stop/status |
| **DeviceListPanel** | `novaic-app/src/components/VM/DeviceManagerPage.tsx` L254 | 父组件传入 `devices` | DeviceManagerPage 内左侧设备列表子组件 |
| **AgentDrawer Devices tab** | `novaic-app/src/components/Layout/AgentDrawer.tsx` | `listForUser` | 抽屉内 Devices 标签，设备列表 + 高亮当前 Agent 绑定 |

**说明**：
- `DeviceListPanel` 为 `DeviceManagerPage` 的子组件，接收 `devices` 等 props，无独立数据拉取
- `DeviceFloatingPanel` 已实现，但当前未被任何父组件渲染（文档称「已实现未接入」）

---

## 4. Device 数据流简图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Gateway API                                         │
│  GET /api/devices          GET /api/devices/{id}     POST .../start|stop|status   │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                              │                            │
         │ gateway_get                  │ gateway_get                 │ gateway_post
         ▼                              ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Tauri: gateway_get / gateway_post                         │
│                    (JWT + path → Cloud / 本地 Gateway)                            │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                              │                            │
         ▼                              ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         api.devices (api.ts)                                     │
│  listForUser()           get(deviceId)            start/stop(deviceId, pc?)     │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                              │                            │
         │                              │                            │
    ┌────┴────┬────────────────────┬───┴───┬────────────────────────┴────────────┐
    ▼         ▼                    ▼       ▼                                       ▼
┌─────────┐ ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐
│AgentDrawer│ │DeviceManager│  │useAgentBinding│  │DeviceManagerPage│  │DeviceFloatingPanel│
│Devices tab│ │   Modal     │  │  devices.get  │  │ devices.get     │  │ start/stop/status │
│listForUser│ │ listForUser │  │               │  │ (effectiveDev)  │  │ devices.get      │
└────┬─────┘ └──────────────┘  └───────┬──────┘  └────────┬─────────┘  └──────────────────┘
    │                                   │                      │
    │ patchState(deviceManagerDevices)   │                      │
    ▼                                   ▼                      │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    useAppStore: deviceManagerDevices, selectedDeviceId           │
└─────────────────────────────────────────────────────────────────────────────────┘
    │                                   │                      │
    └──────────────────────────────────┼──────────────────────┘
                                       │
                              DeviceManagerPage 加载失败时
                              从 store.deviceManagerDevices 回退
```

---

## 5. 组件依赖关系

```
LayoutContainer
├── PrimaryNav (agents | devices | setting)
├── AgentDrawer
│   ├── Agents tab
│   └── Devices tab  ← listForUser → patchState(deviceManagerDevices)
│       └── 设备列表、selectedDeviceId、高亮 agentDevice (useAgentDevice)
├── DeviceManagerPage  ← activeView=devices 时渲染
│   ├── listForUser → devices, patchState(deviceManagerDevices)
│   ├── devices.get(selectedDeviceId) → effectiveSelectedDevice
│   ├── DeviceListPanel(devices, ...)  ← 左侧列表
│   └── DeviceVNCView / DeviceDesktopView  ← 右侧 VNC
│
├── ChatPanel (activeView=chat)
│   └── (DeviceFloatingPanel 未接入)
│
DeviceManagerModal  ← 独立弹窗
└── listForUser → devices, start/stop/delete
```

**Hooks 依赖**：
- `useAgentBinding(agentId)` → `getAgentBinding` + `devices.get` → DeviceFloatingPanel
- `useAgentDevice(agentId)` → `getAgentBinding` + `devices.get` → AgentDrawer 高亮、VisualPanel
- `useDeviceStatusPolling(devices)` → `devices.status` → DeviceStatusStore
- `useDeviceStatus(deviceId)` → 订阅 DeviceStatusStore

---

## 6. 小结

| 维度 | 结论 |
|------|------|
| **列表数据** | `listForUser` 被 DeviceManagerPage、AgentDrawer、DeviceManagerModal 三处独立调用，均写入 `deviceManagerDevices` |
| **详情数据** | `devices.get` 用于单设备详情：DeviceManagerPage 选中设备、useAgentBinding、useAgentDevice |
| **操作 API** | `start/stop/status` 被 DeviceManagerPage、DeviceFloatingPanel、DeviceManagerModal、DeviceVNCView、DeviceDesktopView 等调用 |
| **重复加载** | DeviceManagerPage 与 AgentDrawer 均调用 listForUser 并写入 store，存在重复 |
| **DeviceFloatingPanel** | 已实现，数据源为 useAgentBinding，当前未被渲染 |
