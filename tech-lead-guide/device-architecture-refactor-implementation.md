# 设备架构重构 - 实施记录

## 概述

本文档记录 `device-architecture-refactor.md` 方案的实施过程和改动详情。

---

## 任务完成状态

| 任务 | 状态 | 说明 |
|------|------|------|
| 任务 6：清理重复代码 | ✅ 完成 | 删除 `Android/AddAndroidModal.tsx` |
| 任务 1：移除 Agent 类型（后端） | ✅ 完成 | 移除 `agent_type` 参数 |
| 任务 2：移除 Agent 类型（前端） | ✅ 完成 | 移除 `AgentType` 类型 |
| 任务 3：统一数据模型 | ✅ 完成 | AndroidConfig 独立字段 |
| 任务 4：统一 API 路径 | ✅ 完成 | Android API 走 Gateway |
| 任务 5：实现设备删除 | ✅ 完成 | 支持删除 VM/Android |

---

## 详细改动记录

### 任务 6：清理重复代码

**删除的文件：**
- `novaic-app/src/components/Android/AddAndroidModal.tsx`
- `novaic-app/src/components/Android/` 目录

**保留的文件：**
- `novaic-app/src/components/VM/AddAndroidModal.tsx`

---

### 任务 1：移除 Agent 类型（后端）

**修改的文件：**

1. **`novaic-backend/gateway/config/agents_db.py`**
   - `create_agent()` 移除 `agent_type` 参数
   - 移除 `needs_vm`、`needs_android` 逻辑
   - 新 Agent 默认无设备配置

2. **`novaic-backend/gateway/api/agents.py`**
   - `CreateAgentRequest` 简化为只有 `name` 和 `model`
   - 移除所有 `agent_type` 相关逻辑

3. **`novaic-backend/gateway/db/repositories/agent.py`**
   - `create_agent()` 移除 `agent_type` 参数
   - 不再写入 `_agent_type` 到 `vm_config`

---

### 任务 2：移除 Agent 类型（前端）

**修改的文件：**

1. **`novaic-app/src/services/api.ts`**
   - 删除 `AgentType` 类型定义
   - `CreateAgentRequest` 简化为 `{ name: string; model?: string }`

2. **`novaic-app/src/components/Agent/CreateAgentModal.tsx`**
   - 移除 `agent_type: 'chat'` 参数

3. **`novaic-app/src/components/Onboarding/OnboardingFlow.tsx`**
   - 改为两步创建：先 `createAgent`，再 `updateAgent` 添加 VM

---

### 任务 3：统一数据模型

**数据库迁移：**
- Schema 版本：36 → 37
- 新增 `android_config TEXT DEFAULT NULL` 字段
- 迁移函数：`_migrate_android_config_v37()` 将 `vm_config.android` 迁移到 `android_config`

**修改的文件：**

1. **`novaic-backend/gateway/db/schema.py`**
   - 添加 `android_config` 字段
   - 添加数据迁移逻辑

2. **`novaic-backend/gateway/config/agents_db.py`**
   - `VmConfig` 移除 `android` 字段
   - `AICAgent` 添加独立的 `android: Optional[AndroidConfig]` 字段
   - 更新 `get_agent()`、`list_agents()`、`update_agent()` 方法

3. **`novaic-backend/gateway/db/repositories/agent.py`**
   - 支持 `android_config` 字段的 CRUD

4. **`novaic-backend/gateway/vm/manager.py`**
   - `VmConfig` 重命名为 `VmRunConfig`

5. **`novaic-backend/gateway/api/agents.py`**
   - `agent.vm.android` → `agent.android`

6. **`novaic-backend/gateway/api/vm.py`**
   - `agent.vm.android` → `agent.android`

---

### 任务 4：统一 API 路径

**新增 Gateway 端点（`novaic-backend/gateway/api/vm.py`）：**

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/vm/android/devices` | GET | 列出 Android 设备 |
| `/api/vm/android/avds` | GET | 列出 AVD |
| `/api/vm/android/system-image/check` | GET | 检查系统镜像 |
| `/api/vm/android/device-definitions` | GET | 列出设备定义 |
| `/api/vm/android/avd/create` | POST | 创建 AVD |
| `/api/vm/android/avd/{name}` | DELETE | 删除 AVD |
| `/api/vm/android/scrcpy/status` | GET | 检查 scrcpy |

**前端改动：**

1. **`novaic-app/src/services/api.ts`**
   - 新增 `api.android` 对象，包含所有 Android API

2. **`novaic-app/src/components/VM/AddAndroidModal.tsx`**
   - 从 `androidService` 改为使用 `api.android.*`

3. **`novaic-app/src/components/Layout/DeviceSidebar.tsx`**
   - 移除 `androidService` 依赖
   - 使用 `api.android.listDevices()`

**保留的直连：**
- `scrcpyStream.ts` 中的 WebSocket 仍直连 vmcontrol（视频流需要低延迟）

---

### 任务 5：实现设备删除

**新增 API 端点（`novaic-backend/gateway/api/agents.py`）：**

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/agents/{id}/vm` | DELETE | 移除 VM 配置 |
| `/api/agents/{id}/android` | DELETE | 移除 Android 配置 |

**后端实现（`agents_db.py`）：**
- `remove_vm_config()` - 重置 VM 配置为空
- `remove_android_config()` - 将 android_config 设为 None

**前端实现：**
- `api.removeVmConfig(agentId)`
- `api.removeAndroidConfig(agentId)`
- `DeviceSidebar` 中的 `handleDeleteDevice()` 函数

---

## API 协议变更

### 创建 Agent

**之前：**
```json
POST /api/agents
{
  "name": "My Agent",
  "agent_type": "linux",
  "vm_config": { ... },
  "android": { ... }
}
```

**之后：**
```json
POST /api/agents
{
  "name": "My Agent",
  "model": "optional-model-id"
}
```

### Agent 数据结构

**之前：**
```json
{
  "id": "...",
  "name": "...",
  "vm": {
    "backend": "qemu",
    "image_path": "...",
    "android": {
      "device_serial": "...",
      "managed": true
    }
  }
}
```

**之后：**
```json
{
  "id": "...",
  "name": "...",
  "vm": {
    "backend": "qemu",
    "image_path": "..."
  },
  "android": {
    "device_serial": "...",
    "managed": true
  }
}
```

### 新增 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/agents/{id}/vm` | DELETE | 移除 VM 配置 |
| `/api/agents/{id}/android` | DELETE | 移除 Android 配置 |
| `/api/vm/android/devices` | GET | 列出 Android 设备 |
| `/api/vm/android/avds` | GET | 列出 AVD |
| `/api/vm/android/system-image/check` | GET | 检查系统镜像 |
| `/api/vm/android/device-definitions` | GET | 列出设备定义 |
| `/api/vm/android/avd/create` | POST | 创建 AVD |
| `/api/vm/android/avd/{name}` | DELETE | 删除 AVD |
| `/api/vm/android/scrcpy/status` | GET | 检查 scrcpy |

---

## 数据库迁移

### 版本 37 迁移

1. 添加 `android_config` 列到 `agents` 表
2. 将现有数据中 `vm_config.android` 迁移到 `android_config`
3. 从 `vm_config` 中移除 `android` 字段

**迁移是自动的**，在 Gateway 启动时执行。

---

## 测试清单

### 代码检查（已完成）

- [x] 后端 Python 语法检查通过
- [x] 后端模块导入测试通过
- [x] 前端 TypeScript 编译通过
- [x] Agent 列表 API 正常（`android` 已是独立字段）
- [x] 旧 Agent 数据正常加载

### 功能测试（需重启服务后验证）

> **注意**：以下测试需要重启后端服务才能验证新功能

- [ ] 创建新 Agent（无设备）- 代码已更新，需重启服务
- [ ] 新增 Android Gateway API - 代码已更新，需重启服务
- [ ] 添加 Linux VM
- [ ] 启动/停止 VM
- [ ] VNC 显示正常
- [ ] 添加 Android（托管模式）
- [ ] 添加 Android（外部模式）
- [ ] 启动/停止 Android
- [ ] Scrcpy 显示正常
- [ ] 删除 Linux VM
- [ ] 删除 Android
- [ ] 删除后可重新添加

---

## 风险与注意事项

1. **数据迁移**：首次启动 Gateway 会自动执行迁移，建议先备份数据库
2. **不再兼容旧数据**：已移除所有兼容代码，旧 Agent 数据需要删除重建
3. **vmcontrol 依赖**：所有 Android 操作现在都经过 Gateway，vmcontrol 故障会影响所有 Android 功能
4. **WebSocket**：Scrcpy 视频流仍直连 vmcontrol，这是有意设计

---

## 旧代码清理记录（2026-02-14）

### 后端清理

| 清理项 | 文件 | 说明 |
|--------|------|------|
| `UpdateAgentRequest.vm` | `gateway/api/agents.py` | 移除兼容字段和处理逻辑 |
| `vm_config.pop("android")` | `gateway/config/agents_db.py` | 移除两处兼容代码 |
| `image_path` 空值修复 | `gateway/config/agents_db.py` | 有端口时自动设置 image_path |

### 前端清理

| 清理项 | 文件 | 说明 |
|--------|------|------|
| `androidService` | `services/android.ts` | 删除整个文件，由 `api.android` 替代 |
| `VNCView.old.tsx` | `components/Visual/` | 删除旧 VNC 实现 |
| `VmConfig.android` | `types/index.ts`, `api.ts` | 移除类型定义 |
| `ANDROID_DEVICE_FOR_TEST` | `VisualPanel.tsx` | 移除硬编码测试数据 |
| `AvailableModel` | `types/index.ts` | 移除类型别名 |
| `quickDeployAgent` | `services/setup.ts` | 移除废弃函数 |
| `WEBSOCKIFY_PORT` | `config/index.ts` | 移除旧端口配置 |

### image_path 为空的根本原因

**原因**：`create_agent()` 创建的是无设备的 Agent，`VmConfig()` 中 `image_path=""` 是默认值。只有在 `update_agent` 时传入 `vm_config` 且当前无端口时才会设置 `image_path`。

**修复**：在 `update_agent` 中添加逻辑，当已有端口但 `image_path` 为空时，自动设置正确的路径。

---

## 文件变更清单

### 后端

| 文件 | 变更类型 |
|------|----------|
| `gateway/db/schema.py` | 修改 |
| `gateway/config/agents_db.py` | 修改 |
| `gateway/config/agents.py` | 修改 |
| `gateway/db/repositories/agent.py` | 修改 |
| `gateway/api/agents.py` | 修改 |
| `gateway/api/vm.py` | 修改 |
| `gateway/api/internal/agent.py` | 修改 |
| `gateway/vm/manager.py` | 修改 |

### 前端

| 文件 | 变更类型 |
|------|----------|
| `src/services/api.ts` | 修改 |
| `src/components/Agent/CreateAgentModal.tsx` | 修改 |
| `src/components/Onboarding/OnboardingFlow.tsx` | 修改 |
| `src/components/VM/AddAndroidModal.tsx` | 修改 |
| `src/components/Layout/DeviceSidebar.tsx` | 修改 |
| `src/components/Android/AddAndroidModal.tsx` | 删除 |
| `src/components/Android/` | 删除目录 |
