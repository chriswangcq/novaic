# NovAIC Agent 与 Device 关系与数据模型研究报告

## 1. 数据模型

### 1.1 agents 表

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    vm_config TEXT NOT NULL DEFAULT '{}',
    ports TEXT NOT NULL DEFAULT '{}',
    setup_complete INTEGER DEFAULT 0,
    model_id TEXT,
    cloud_init_complete INTEGER DEFAULT 0,
    android_config TEXT DEFAULT NULL
);
```

- **语义**：AI Agent 配置实体，归属于用户
- **关键字段**：`user_id`（所属用户）、`vm_config`/`android_config`（历史遗留配置，v38 后设备迁移至 `devices` 表）
- **无 device 外键**：Agent 不直接引用 Device，通过 `agent_device_bindings` 关联

---

### 1.2 devices 表

```sql
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL CHECK(type IN ('linux', 'android')),
    name TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    status TEXT CHECK(status IN ('created', 'setup', 'ready', 'running', 'stopped', 'error')),
    memory INTEGER, cpus INTEGER, data_path TEXT, ports TEXT,
    -- Linux
    backend TEXT, os_type TEXT, os_version TEXT, image_path TEXT, cloud_init_complete INTEGER,
    -- Android
    avd_name TEXT, device_serial TEXT, managed INTEGER, system_image TEXT,
    pc_client_id TEXT DEFAULT NULL  -- 物理 PC 标识，多 PC 路由用
);
```

- **语义**：执行环境实体（Linux VM 或 Android AVD），归属于用户
- **关键字段**：`user_id`（直接所有者）、`type`（linux/android）、`status`、`pc_client_id`（所属物理 PC）
- **按 User 组织**：Device 与 Agent 解耦，创建时无需指定 Agent

---

### 1.3 agent_device_bindings 表

```sql
CREATE TABLE agent_device_bindings (
    agent_id      TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    device_id     TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    subject_type  TEXT NOT NULL CHECK(subject_type IN ('main', 'vm_user', 'default')),
    subject_id    TEXT NOT NULL DEFAULT '',
    mounted_tools TEXT NOT NULL DEFAULT '[]',
    created_at TEXT, updated_at TEXT,
    UNIQUE(device_id, subject_type, subject_id)
);
```

- **语义**：Agent 与 Device Subject 的绑定关系
- **约束**：
  - `agent_id` 为主键 → **一个 Agent 最多一个 Binding**
  - `UNIQUE(device_id, subject_type, subject_id)` → **一个 Device Subject 只能被一个 Agent 绑定**

---

## 2. 关系图（文字描述）

```
┌─────────────┐         ┌──────────────────────────┐         ┌─────────────┐
│   agents    │         │  agent_device_bindings    │         │   devices   │
├─────────────┤         ├──────────────────────────┤         ├─────────────┤
│ id (PK)     │───1:1───│ agent_id (PK, FK)        │         │ id (PK)     │
│ user_id     │         │ device_id (FK)           │───N:1───│ user_id     │
│ name        │         │ subject_type             │         │ type        │
│ ...         │         │ subject_id               │         │ status      │
└─────────────┘         │ mounted_tools            │         │ ...         │
                        └──────────────────────────┘         └─────────────┘
                                    │
                                    │ 引用 (device_id, subject_type, subject_id)
                                    ▼
                        ┌──────────────────────────┐
                        │  Device Subject 概念     │
                        │  - main: Linux 主桌面    │
                        │  - vm_user: Linux 子用户 │
                        │  - default: Android 默认  │
                        └──────────────────────────┘
```

**关系说明**：

| 关系 | 说明 |
|------|------|
| Agent → Binding | **1:1**：每个 Agent 最多有一个 Binding |
| Binding → Device | **N:1**：多个 Binding 可指向同一 Device |
| Device Subject → Binding | **1:1**：同一 (device_id, subject_type, subject_id) 只能被一个 Agent 绑定 |
| Agent → User | **N:1**：多个 Agent 属于同一用户 |
| Device → User | **N:1**：多个 Device 属于同一用户 |

---

## 3. Subject 类型

| subject_type | subject_id | 含义 | 设备类型 |
|--------------|------------|------|----------|
| `main` | `"main"` | Linux VM 主桌面（display :10） | linux |
| `vm_user` | `username` | Linux VM 子用户（display :11, :12...） | linux |
| `default` | `"default"` | Android 默认会话 | android |

- **Linux**：一个 Device 可有多个 Subject（main + 若干 vm_user）
- **Android**：一个 Device 仅有一个 Subject（default）

---

## 4. 业务语义

### 4.1 Agent 代表什么？

- **AI 助手实体**：具有名称、模型、VM/Android 配置等
- **归属于用户**：`user_id` 标识所有者
- **执行环境**：通过 Binding 绑定到某个 Device Subject，在该 Subject 上执行工具（screenshot、shell、file 等）
- **一个 Agent 绑定一个 Device Subject**：通过 `agent_device_bindings` 表实现

### 4.2 Device 代表什么？

- **执行环境实体**：Linux VM 或 Android AVD
- **归属于用户**：`user_id` 标识所有者，与 Agent 解耦
- **可被多个 Agent 使用**：同一 Device 的不同 Subject 可分别绑定不同 Agent
  - 例：Device A 的 main 绑定 Agent 1，vm_user alice 绑定 Agent 2

### 4.3 绑定规则

| 问题 | 答案 |
|------|------|
| 一个 Agent 是否绑定一个 Device？ | **是**，且绑定的是 Device 的**某个 Subject**（main/vm_user/default） |
| 一个 Device 是否可被多个 Agent 使用？ | **是**，不同 Subject 可绑定不同 Agent；同一 Subject 只能绑定一个 Agent |
| Binding 是否必填？ | **否**，Agent 可无 Binding（新建 Agent 默认无绑定） |

---

## 5. 关键 API 与用途

### 5.1 Agents API (`/api/agents`)

| 方法 | 路径 | 用途 | 返回结构 |
|------|------|------|----------|
| GET | `/api/agents` | 列出当前用户的所有 Agent | `{ agents: AICAgent[] }`，每个含 `binding` |
| GET | `/api/agents/{id}` | 获取单个 Agent | `AICAgent`，含 `binding` |
| POST | `/api/agents` | 创建 Agent | `AICAgent` |
| PATCH | `/api/agents/{id}` | 更新 Agent | `AICAgent` |
| GET | `/api/agents/{id}/binding` | 获取 Agent 的 Binding | `AgentDeviceBinding \| null` |
| PUT | `/api/agents/{id}/binding` | 设置/更新 Binding | `AgentDeviceBinding` |
| DELETE | `/api/agents/{id}/binding` | 清除 Binding | 204 |

**Agent 列表/详情**：`_agent_to_response` 会从 `AgentDeviceBindingRepository.get(agent.id)` 填充 `binding`，故 `GET /api/agents` 和 `GET /api/agents/{id}` 已包含 binding，无需额外调用 `getAgentBinding`。

---

### 5.2 Devices API (`/api/devices`)

| 方法 | 路径 | 用途 | 返回结构 |
|------|------|------|----------|
| GET | `/api/devices` | 列出当前用户的所有 Device | `{ devices: Device[] }` |
| GET | `/api/devices/{id}` | 获取单个 Device | `Device` |
| POST | `/api/devices/linux` | 创建 Linux Device | `Device` |
| POST | `/api/devices/android` | 创建 Android Device | `Device` |
| PATCH | `/api/devices/{id}` | 更新 Device | `Device` |
| DELETE | `/api/devices/{id}` | 删除 Device | `{ status, message }` |
| GET | `/api/devices/{id}/subjects` | 列出 Device 的 Subject | `{ subjects: DeviceSubject[] }` |
| GET | `/api/devices/{id}/tool-capabilities` | 获取工具能力 | `DeviceToolCapabilitiesResponse` |
| POST | `/api/devices/{id}/setup` | 初始化 Device | `{ status, message }` |
| POST | `/api/devices/{id}/start` | 启动 Device | `{ status, message }` |
| POST | `/api/devices/{id}/stop` | 停止 Device | `{ status, message }` |
| GET | `/api/devices/{id}/status` | 获取运行状态 | 状态信息 |

---

### 5.3 前端 API 封装（`api.ts`）

| 前端方法 | 后端路径 | 说明 |
|----------|----------|------|
| `api.agents.listAgents()` | `GET /api/agents` | 含 binding |
| `api.agents.getAgent(agentId)` | `GET /api/agents/{id}` | 含 binding |
| `api.agents.getAgentBinding(agentId)` | `GET /api/agents/{id}/binding` | 单独获取 binding |
| `api.agents.setAgentBinding(agentId, data)` | `PUT /api/agents/{id}/binding` | 设置 binding |
| `api.agents.clearAgentBinding(agentId)` | `DELETE /api/agents/{id}/binding` | 清除 binding |
| `api.devices.listForUser()` | `GET /api/devices` | 按用户列出设备 |
| `api.devices.get(deviceId)` | `GET /api/devices/{id}` | 获取设备详情 |
| `api.devices.list(agentId)` | `GET /api/agents/{id}/devices` | **已废弃，会 404** |

**注意**：`GET /api/agents/{id}/devices` 不存在。正确用法为 `listForUser()` + `getAgentBinding(agentId)` 或直接使用 Agent 列表/详情中的 `binding` 字段。

---

## 6. Binding 返回结构

```typescript
interface AgentDeviceBinding {
  agent_id: string;
  device_id: string;
  subject_type: 'main' | 'vm_user' | 'default';
  subject_id: string;
  mounted_tools: Record<string, string[]>;  // { category: [tool, ...] }
  created_at: string;
  updated_at: string;
  // 扩展字段（API 填充）
  device_type?: string | null;
  device_name?: string | null;
  subject_label?: string | null;
  desktop_resource_id?: string | null;
  supported_tools?: Record<string, string[]>;
}
```

---

## 7. 运行时解析

`resolve_agent_runtime_context(db, agent_id)`（`gateway/agent_binding.py`）用于执行时解析 Agent 的运行时上下文：

1. 从 `agent_device_bindings` 取 binding
2. 从 `devices` 取 device
3. 从 `get_device_subject` 取 subject 信息
4. 构建 `runtime_context`（Linux：display、home_path、shell；Android：android_serial、adb 等）
5. 返回 `{ binding, device, subject, runtime_context, mounted_tools, supported_tools }`

Tools Server、VMUSE、Mobile Proxy 等执行层依赖该上下文确定目标 Device 与 Subject。

---

## 8. 总结

| 维度 | 结论 |
|------|------|
| **数据组织** | Device 按 User 组织；Agent 按 User 组织；Binding 连接 Agent 与 Device Subject |
| **Agent–Device 关系** | 多对多（通过 Subject 维度）：一个 Agent 绑定一个 Subject；一个 Device 的多个 Subject 可绑定不同 Agent |
| **核心 API** | `GET /api/agents`、`GET /api/devices`、`GET /api/agents/{id}/binding`、`PUT /api/agents/{id}/binding` |
| **前端数据流** | `listForUser()` → 设备列表；`getAgentBinding(agentId)` 或 Agent 详情的 `binding` → 当前 Agent 绑定的设备与 Subject |
