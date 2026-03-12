# docs/UNIFIED_CURRENT_STATE_AND_RESEARCH.md 二、Device 管理 审核报告

> 对照实际代码逐条核对，标注「正确」「错误」「需补充」及具体代码位置。

---

## 1. Device 是否按 User 组织？listForUser / GET /api/devices 的实现

**结论：正确**

| 项目 | 代码位置 | 说明 |
|------|----------|------|
| 后端 `GET /api/devices` | `novaic-gateway/gateway/api/devices.py` L217-224 | `list_all_user_devices` 使用 `repo.list_by_user(user_id)` |
| 后端 `list_by_user` | `novaic-gateway/gateway/db/repositories/device.py` L61-67 | `SELECT * FROM devices WHERE user_id = ? ORDER BY created_at` |
| 前端 `listForUser` | `novaic-app/src/services/api.ts` L749-751 | `invoke('gateway_get', { path: '/api/devices' })` |

---

## 2. Agent 是否只通过 Binding 引用？agent_device_bindings 表结构、getAgentBinding API

**结论：正确**

| 项目 | 代码位置 | 说明 |
|------|----------|------|
| 表结构 `agent_device_bindings` | `novaic-gateway/gateway/db/repositories/agent_device_binding.py` L34-37, L95-109 | 字段：agent_id, device_id, subject_type, subject_id, mounted_tools, created_at, updated_at |
| Binding 语义 | 同上 L33-37 | `get(agent_id)` 返回单条 binding，Agent 只引用一个 device+subject |
| 后端 `GET /api/agents/{id}/binding` | `novaic-gateway/gateway/api/agents.py` L451-459 | `get_agent_binding` → `AgentDeviceBindingRepository(db).get(agent_id)` |
| 前端 `getAgentBinding` | `novaic-app/src/services/api.ts` L373-377 | `invoke('gateway_get', { path: \`/api/agents/${agentId}/binding\` })` |

---

## 3. 是否存在 list_by_agent、GET /api/agents/{id}/devices？是否真的 404 或不存在

**结论：正确（均不存在）**

| 项目 | 代码位置 | 说明 |
|------|----------|------|
| `list_by_agent` | `novaic-gateway/gateway/db/repositories/device.py` | DeviceRepository 仅有 `list_by_user`、`list_by_type`，**无** `list_by_agent` |
| `GET /api/agents/{id}/devices` | `novaic-gateway/gateway/api/agents.py` | 仅有 `/{agent_id}/binding`，**无** `/{agent_id}/devices` 路由 |
| 前端 `devices.list(agentId)` | `novaic-app/src/services/api.ts` L768-770 | 调用 `GET /api/agents/${agentId}/devices`，**会 404** |

**需补充**：前端 `api.devices.list(agentId)` 仍存在，但对应后端路由不存在，调用会 404。文档应注明：前端应移除或废弃 `devices.list(agentId)`，改用 `listForUser` + `getAgentBinding`。

---

## 4. devices 表 vs pc_clients 的 device_id 语义

**结论：正确，可补充细节**

| 表 | 主键/device_id 语义 | 代码位置 |
|----|---------------------|----------|
| `devices` | 逻辑 device_id（VM/AVD 配置），主键为 `id` | `device.py` L28-34, L59 |
| `pc_clients` | 物理 device_id（VmControl Ed25519 / x-device-id），主键为 `device_id` | `pc_client.py` L36-40, L54-55 |
| `agent_device_bindings.device_id` | 引用 `devices.id`（逻辑设备） | `agent_device_binding.py` L18, L77 |

文档描述正确。可补充：`devices` 表主键字段名为 `id`，`pc_clients` 主键为 `device_id`；VNC proxy 使用的 resource_id 中 device_id 为逻辑设备 ID（devices.id），而 my-devices 返回的 device_id 为物理 PC ID（pc_clients.device_id）。

---

## 5. get_pc_client_manager 是否始终用第一个设备

**结论：正确（devices API 调用方确实如此）**

| 调用方 | 代码位置 | 传参 | 行为 |
|--------|----------|------|------|
| `get_pc_client_manager` 实现 | `novaic-gateway/gateway/api/internal/pc_client.py` L362-380 | `user_id=None` 或 `user_id=xxx` | `user_id=None`：返回任意已连接设备（遍历取第一个）；`user_id=xxx`：返回该用户第一台已连接设备 |
| devices.py 所有调用 | devices.py L551, 586, 629, 662, 706, 728, 779, 796, 812 | **无参数** | `user_id=None` → 始终用第一个连接的设备（任意用户） |
| vm.py 部分调用 | vm.py L149, 169, 192, 230 | `user_id` | 按用户过滤后取第一个 |
| vm.py 其他调用 | vm.py L266, 345, 387, ... | 无参数 | 同 devices.py |

文档「`get_pc_client_manager` 始终用第一个连接的设备，无法指定目标 PC」对 **devices API**（start/stop/setup/status/vmuse sync 等）准确。部分 vm.py 调用会传 user_id 做用户过滤，但仍是「该用户的第一台」，多 PC 场景下仍无法指定目标。

---

## 修正建议汇总

1. **需补充**：在 2.3 后端 API 表格后增加说明：
   > 前端 `api.devices.list(agentId)` 调用 `GET /api/agents/{id}/devices`，该路由不存在会 404。应移除或废弃 `devices.list`，统一使用 `listForUser` + `getAgentBinding`。

2. **可选补充**：在 device_id 语义处注明 `devices` 主键为 `id`，`pc_clients` 主键为 `device_id`，避免混淆。

3. **可选补充**：`get_pc_client_manager` 在传 `user_id` 时会按用户过滤，但 devices API 未传 user_id，故对设备操作而言仍为「第一个设备」。
