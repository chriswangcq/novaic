# NovAIC 设备管理数据结构与组织报告

> 本报告对 novaic-app 与 novaic-gateway 中的设备管理相关数据结构、API、状态管理和组件层级进行全面梳理。

---

## 1. 数据模型概览

### 1.1 后端表结构（novaic-gateway）

#### devices 表（v38 统一设备模型）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | 设备 UUID |
| user_id | TEXT | 直接归属用户（users.id） |
| type | TEXT | `linux` \| `android` |
| name | TEXT | 显示名称 |
| created_at | TEXT | 创建时间 |
| status | TEXT | `created` \| `setup` \| `ready` \| `running` \| `stopped` \| `error` |
| memory | INTEGER | 内存 MB |
| cpus | INTEGER | CPU 核数 |
| data_path | TEXT | 数据目录 |
| ports | TEXT | JSON `{ssh, vmuse}` |
| backend | TEXT | Linux: qemu |
| os_type, os_version | TEXT | Linux 系统信息 |
| image_path | TEXT | Linux 磁盘镜像路径 |
| cloud_init_complete | INTEGER | Linux cloud-init 完成 |
| avd_name, device_serial | TEXT | Android 相关 |
| managed | INTEGER | Android 是否托管 |
| system_image | TEXT | Android 系统镜像 |
| pc_client_id | TEXT | P2-8: 设备所属物理 PC（多 PC 路由） |

**索引**：`idx_devices_user`, `idx_devices_type`, `idx_devices_status`

#### vm_users 表（v51 多用户 VM）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | vm_user UUID |
| device_id | TEXT FK | 关联 devices.id |
| username | TEXT | Linux 用户名 |
| password | TEXT | 密码 |
| display_num | INTEGER | Xvnc display 号（:11, :12...） |
| created_at | TEXT | 创建时间 |

**约束**：`UNIQUE(device_id, username)`  
**索引**：`idx_vm_users_device`

#### agent_device_bindings 表（v52 Agent 设备绑定）

| 字段 | 类型 | 说明 |
|------|------|------|
| agent_id | TEXT PK FK | 关联 agents.id |
| device_id | TEXT FK | 关联 devices.id |
| subject_type | TEXT | `main` \| `vm_user` \| `default` |
| subject_id | TEXT | main→"main", vm_user→username, default→"default" |
| mounted_tools | TEXT | JSON `{category: [tool, ...]}` |
| created_at, updated_at | TEXT | 时间戳 |

**约束**：`UNIQUE(device_id, subject_type, subject_id)`（同一 subject 仅能绑定一个 agent）  
**索引**：`idx_agent_device_bindings_device`

#### pc_clients 表（v48 物理 PC 注册）

| 字段 | 类型 | 说明 |
|------|------|------|
| pc_client_id | TEXT PK | VmControl Ed25519 标识 |
| user_id | TEXT | 归属用户 |
| name | TEXT | 友好名称 |
| online | INTEGER | 是否开放 Agent 控制 |
| first_seen, last_seen | TEXT | 时间戳 |

---

### 1.2 前端类型定义（novaic-app/src/types/）

#### 核心设备类型

```typescript
// src/types/index.ts

export type DeviceType = 'linux' | 'android';
export type DeviceStatus = 'created' | 'setup' | 'ready' | 'running' | 'stopped' | 'error';

export interface DeviceConfig {
  id: string;
  user_id: string;
  type: DeviceType;
  name: string;
  created_at: string;
  status: DeviceStatus;
  memory: number;
  cpus: number;
  data_path: string;
  ports: Record<string, number>;
  pc_client_id?: string;
}

export interface LinuxDevice extends DeviceConfig {
  type: 'linux';
  backend: string;
  os_type: string;
  os_version: string;
  image_path: string;
  cloud_init_complete: boolean;
}

export interface AndroidDevice extends DeviceConfig {
  type: 'android';
  avd_name: string;
  device_serial: string;
  managed: boolean;
  system_image: string;
}

export type Device = LinuxDevice | AndroidDevice;

export interface VmUser {
  id: string;
  device_id: string;
  username: string;
  display_num: number;
  created_at: string;
}
```

#### VNC 寻址类型

```typescript
// src/types/vnc.ts

export interface VncTarget {
  pcClientId?: string;   // 物理 PC 标识，多 PC 路由
  resourceId: string;   // vm_id（deviceId）
  subjectType: 'main' | 'vm_user' | 'default';
  deviceId: string;
  username: string;     // maindesk 传 ""，subuser 传实际用户名
}
```

#### API 层类型（api.ts）

```typescript
export type DeviceSubjectType = 'main' | 'vm_user' | 'default';
export type MountedToolsByCategory = Record<string, string[]>;

export interface AgentDeviceBinding {
  agent_id: string;
  device_id: string;
  subject_type: DeviceSubjectType;
  subject_id: string;
  mounted_tools: MountedToolsByCategory;
  created_at: string;
  updated_at: string;
  device_type?: string | null;
  device_name?: string | null;
  subject_label?: string | null;
  desktop_resource_id?: string | null;
  supported_tools?: MountedToolsByCategory;
}

export interface DeviceSubject {
  device_id: string;
  device_type: string;
  subject_type: DeviceSubjectType;
  subject_id: string;
  label: string;
  desktop_resource_id: string;
  supported_tools: MountedToolsByCategory;
  username?: string;
  display_num?: number;
  linux_user?: string;
  home_path?: string;
  android_serial?: string;
}
```

---

## 2. API 层

### 2.1 Gateway 设备 API（/api/devices）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/devices | 列出当前用户所有设备 |
| POST | /api/devices/linux | 创建 Linux 设备 |
| POST | /api/devices/android | 创建 Android 设备 |
| GET | /api/devices/{id} | 获取单个设备 |
| PATCH | /api/devices/{id} | 更新设备 |
| DELETE | /api/devices/{id} | 删除设备（支持 ?pc_client_id） |
| GET | /api/devices/{id}/subjects | 列出设备可执行 subject |
| GET | /api/devices/{id}/tool-capabilities | 获取工具能力 |
| POST | /api/devices/{id}/setup | 初始化设备 |
| POST | /api/devices/{id}/start | 启动设备 |
| POST | /api/devices/{id}/stop | 停止设备 |
| GET | /api/devices/{id}/status | 获取运行时状态 |
| POST | /api/devices/{id}/vmuse/sync | Linux VM 热同步 vmuse |

### 2.2 Agent Binding API（/api/agents/{id}）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/agents/{id}/binding | 获取 Agent 绑定 |
| PUT | /api/agents/{id}/binding | 设置/更新绑定 |
| DELETE | /api/agents/{id}/binding | 清除绑定 |

### 2.3 VM Users API（/api/devices/{id}/vm-users）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/devices/{id}/vm-users | 列出 VM 子用户 |
| POST | /api/devices/{id}/vm-users | 创建子用户 |
| DELETE | /api/devices/{id}/vm-users/{username} | 删除子用户 |
| POST | /api/devices/{id}/vm-users/{username}/restart | 重启 VNC 会话 |

### 2.4 前端 api.ts 设备方法

```typescript
api.devices.listForUser()           // 用户所有设备
api.devices.get(deviceId)           // 单个设备
api.devices.getSubjects(deviceId)   // 设备 subjects
api.devices.getToolCapabilities()   // 工具能力
api.devices.createLinuxForUser()    // 创建 Linux
api.devices.createAndroidForUser()  // 创建 Android
api.devices.update()                // 更新
api.devices.delete()                // 删除
api.devices.setup()                 // 初始化
api.devices.start()                 // 启动
api.devices.stop()                  // 停止
api.devices.status()                // 状态

api.getAgentBinding(agentId)        // Agent 绑定
api.setAgentBinding(agentId, data)  // 设置绑定
api.clearAgentBinding(agentId)      // 清除绑定

api.vmUsers.list(deviceId)          // VM 用户列表
api.vmUsers.create(deviceId, user, pass)
api.vmUsers.delete(deviceId, username)
api.vmUsers.restartVnc(deviceId, username)
```

---

## 3. 前端状态管理

### 3.1 存储位置

| 存储 | 文件 | 内容 |
|------|------|------|
| **Zustand** | `application/store.ts` | `deviceManagerDevices`, `selectedDeviceId`, `selectedVmUser`, 添加设备弹窗状态 |
| **Zustand** | `stores/deviceStatusStore.ts` | 设备状态 Map（deviceId/pcClientId → status） |
| **内存缓存** | `useAgentDevice.ts` | `deviceCache` Map，TTL 30s |
| **组件本地** | 各页面 | devices 列表、loading、error |

### 3.2 DeviceStatusStore

```typescript
// stores/deviceStatusStore.ts

interface DeviceStatusEntry {
  deviceId: string;
  pcClientId?: string;
  status: DeviceStatusValue;
  updatedAt: number;
}

// 复合 key：多 PC 时 deviceId:pcClientId
statusKey(deviceId, pcClientId) → "deviceId" 或 "deviceId:pcClientId"
```

### 3.3 缓存与 Key 约定

| Key 类型 | 格式 | 用途 |
|----------|------|------|
| **statusKey** | `deviceId` 或 `deviceId:pcClientId` | DeviceStatusStore、useDeviceStatus |
| **deviceCache** | `statusKey(deviceId, pcClientId)` | useAgentDevice 设备缓存 |
| **VNC pool_key** | `vm_id:username` | vnc_stream 连接池（maindesk username=""） |
| **desktop_resource_id** | `deviceId` 或 `deviceId:username` | VNC 寻址 |

---

## 4. 组件树与数据流

### 4.1 组件层级

```
App
├── LayoutContainer
│   ├── DeviceSidebar          # 按 Agent 显示设备（agent.devices）
│   │   ├── DeviceCard
│   │   ├── DeviceDisplayModal
│   │   └── AddLinuxVMModal / AddAndroidModal
│   │
│   ├── DeviceFloatingPanel    # 按 Agent binding 显示浮窗
│   │   ├── DeviceCard (main/vm_user → DeviceDesktopView, default → ScrcpyView)
│   │   └── StoppedDeviceChip
│   │
│   └── AgentDrawer
│       └── DeviceManagerPage  # 设备管理主页面
│           ├── DeviceListPanel
│           │   ├── DeviceRow
│           │   └── VmUsersSection
│           ├── DeviceVNCView   # Linux→DeviceDesktopView, Android→ScrcpyView
│           └── DeviceDesktopView (vm_user 时)
```

### 4.2 数据流概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend (Gateway)                                                        │
│  devices ← user_id    agent_device_bindings ← agent_id    vm_users       │
└─────────────────────────────────────────────────────────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  API Layer (api.ts)                                                       │
│  devices.listForUser()   getAgentBinding()   vmUsers.list()               │
│  devices.get()           setAgentBinding()   vmUsers.create()            │
│  devices.status()                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│ DeviceManagerPage│    │ useAgentDevice        │    │ DeviceFloatingPanel │
│ api.listForUser()│    │ getBinding + get      │    │ useAgentBinding     │
│ → devices 列表   │    │ → binding, device,     │    │ useDeviceVncTarget  │
│ useDeviceStatus  │    │   vncTarget           │    │ (deviceMode)        │
│ Polling          │    │                       │    │                     │
└──────────────────┘    └──────────────────────┘    └─────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│ DeviceStatusStore│    │ DeviceDesktopView    │    │ createVncTransport  │
│ 5s 轮询更新      │    │ VncTarget → create   │    │ VncTarget → QUIC    │
│ statusKey 索引   │    │ VncTransport         │    │ pool_key=vm_id:user │
└──────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### 4.3 设备列表 vs 设备详情 vs 绑定

| 场景 | 数据来源 | 组件 |
|------|----------|------|
| **设备列表** | `api.devices.listForUser()` | DeviceManagerPage、DeviceListPanel |
| **设备详情** | `api.devices.get(id)` 或列表内查找 | DeviceVNCView、DeviceDesktopView |
| **Agent 绑定设备** | `api.getAgentBinding(agentId)` + `api.devices.get(binding.device_id)` | DeviceFloatingPanel、useAgentDevice |
| **设备状态** | `api.devices.status()` + DeviceStatusStore 轮询 | useDeviceStatus、useDeviceStatusPolling |

### 4.4 设备数据来源差异

| 组件 | 设备来源 | 说明 |
|------|----------|------|
| **DeviceSidebar** | `currentAgent?.devices` | 依赖 Agent 列表中的 devices（可能已废弃） |
| **DeviceFloatingPanel** | `useAgentBinding` 或 `useDeviceVncTarget` | binding → device，或 deviceMode 直接 deviceId |
| **DeviceManagerPage** | `api.devices.listForUser()` | 按 User 组织，与 Agent 解耦 |
| **AgentDesktopView** | `useAgentDevice` | binding → device → vncTarget |

---

## 5. 核心关系

### 5.1 Agent ↔ Device ↔ Binding ↔ VmUser

```
┌─────────┐      1:1       ┌──────────────────────┐      N:1      ┌─────────┐
│  Agent  │◄──────────────►│ agent_device_bindings│◄─────────────►│ Device  │
│         │                 │ agent_id (PK)        │               │         │
│         │                 │ device_id (FK)       │               │ user_id │
│         │                 │ subject_type         │               │ type    │
│         │                 │ subject_id           │               │         │
└─────────┘                 └──────────────────────┘               └────┬────┘
                                                                       │
                                                                       │ 1:N
                                                                       ▼
                                                                ┌─────────────┐
                                                                │  vm_users   │
                                                                │ device_id   │
                                                                │ username    │
                                                                │ display_num │
                                                                └─────────────┘
```

- **Agent**：一个 Agent 最多绑定一个 device subject（main/vm_user/default）
- **Device**：一个 Device 可被多个 Agent 绑定不同 subject（main/vm_user 互斥）
- **vm_users**：Linux Device 下可有多个子用户，每个有独立 TigerVNC 会话

### 5.2 Subject 类型与 VNC 寻址

| subject_type | subject_id | VncTarget.username | desktop_resource_id | VNC pool_key |
|--------------|------------|--------------------|---------------------|--------------|
| main | "main" | "" | deviceId | deviceId: |
| vm_user | username | username | deviceId:username | deviceId:username |
| default | "default" | "" | deviceId | deviceId: |
| (Android) |  |  |  |  |

### 5.3 多 PC 路由（P2-8）

- `devices.pc_client_id`：设备在 setup 时记录所属物理 PC
- `pc_clients`：物理 PC 注册表
- `statusKey(deviceId, pcClientId)`：多 PC 时区分同一 device 的多个状态
- API 支持 `?pc_client_id=` 指定目标物理机

---

## 6. 关键文件索引

| 职责 | 文件路径 |
|------|----------|
| 设备类型 | `novaic-app/src/types/index.ts` |
| VNC 类型 | `novaic-app/src/types/vnc.ts` |
| API 客户端 | `novaic-app/src/services/api.ts` |
| 设备状态 Store | `novaic-app/src/stores/deviceStatusStore.ts` |
| 状态 Key 工具 | `novaic-app/src/utils/deviceStatusKey.ts` |
| useAgentDevice | `novaic-app/src/hooks/useAgentDevice.ts` |
| useAgentBinding | `novaic-app/src/hooks/useAgentBinding.ts` |
| useDeviceVncTarget | `novaic-app/src/hooks/useDeviceVncTarget.ts` |
| useDeviceStatus | `novaic-app/src/hooks/useDeviceStatus.ts` |
| useDeviceStatusPolling | `novaic-app/src/hooks/useDeviceStatusPolling.ts` |
| DeviceManagerPage | `novaic-app/src/components/VM/DeviceManagerPage.tsx` |
| DeviceSidebar | `novaic-app/src/components/Layout/DeviceSidebar.tsx` |
| DeviceFloatingPanel | `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` |
| DeviceVNCView | `novaic-app/src/components/Visual/DeviceVNCView.tsx` |
| DeviceDesktopView | `novaic-app/src/components/Visual/DeviceDesktopView.tsx` |
| Device 表 Schema | `novaic-gateway/gateway/db/schema.py` |
| Device Repository | `novaic-gateway/gateway/db/repositories/device.py` |
| Binding Repository | `novaic-gateway/gateway/db/repositories/agent_device_binding.py` |
| Device API | `novaic-gateway/gateway/api/devices.py` |
| VM Users API | `novaic-gateway/gateway/api/vm_users.py` |
| Agent Binding API | `novaic-gateway/gateway/api/agents.py` |
| Binding 逻辑 | `novaic-gateway/gateway/agent_binding.py` |
| Device Config | `novaic-gateway/gateway/config/devices.py` |

---

## 7. 已知差异与注意事项

1. **DeviceSidebar** 仍使用 `agent.devices`，而 Device 已按 User 组织，Agent 通过 binding 引用。存在数据源不一致风险。
2. **api.devices.list(agentId)** 已废弃（404），应使用 `listForUser()` + `getAgentBinding()`。
3. **VNC pool_key**：maindesk 为 `vm_id:`（username 空），subuser 为 `vm_id:username`。
4. **DeviceStatusStore** 轮询间隔：无 VNC 连接时 5s，有 VNC 时 3s（`VM_STATUS_FAST_INTERVAL`）。
