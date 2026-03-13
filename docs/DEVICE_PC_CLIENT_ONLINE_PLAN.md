# Device / pc_client 在线状态与可用性实现计划

> 基于已确认方案：pc_client_id 持久绑定、vm_status_report 只写不清、pc_client online 决定 device 是否 available。

---

## 1. 方案回顾

### 1.1 状态层级

```
pc_client.online     → 物理 PC 是否已登录（Cloud Bridge 连接）
    ├─ offline       → device = unavailable（无法访问）
    └─ online        → device 有 running 状态
                        ├─ running   → 可用
                        └─ stopped   → 不可用
```

### 1.2 数据关系

| 概念 | 说明 |
|------|------|
| **pc_client_id** | 持久绑定，设备归属/曾在这台 PC 上，离线也保留 |
| **user → pc_client → devices** | 同一 pc 可被多 user 先后登录，当前仅一个 app_instance 在线 |
| **换用户登录** | 不清除 pc_client_id，通过 online available 区分 |

### 1.3 vm_status_report

- **只做写入**：为当前 user 上报的 vm_ids 设置 `devices.pc_client_id`
- **不做清除**：不根据 vm_status_report 清除 pc_client_id

---

## 2. 后端改动

### 2.1 vm_status_report 逻辑调整（pc_client.py）

**当前**：写入 + 清除（跨 user 清除未上报的 device）

**目标**：仅写入，不清除

| 步骤 | 操作 |
|------|------|
| 1 | 收到 vm_status_report，vm_ids = data["vm_ids"] |
| 2 | user_id = 连接上的 x-user-id |
| 3 | 对每个 vid in vm_ids：若 device 属于该 user，则 `UPDATE devices SET pc_client_id = ? WHERE id = vid` |
| 4 | ~~清除未上报的 device~~ → **删除此步骤** |

**文件**：`novaic-gateway/gateway/api/internal/pc_client.py`

---

### 2.2 pc_client.online 状态来源

**来源**：DeviceRegistry（Cloud Bridge 连接时写入）

- 连接建立 → pc_client online
- 连接断开 → pc_client offline
- `_p2p_registry` 或 DeviceRegistry 中 `is_connected` / `ws is not None` 可表示 online

**my-devices API**：已返回 `online` 字段（`entry.is_stale` 取反等），需确认与 DeviceRegistry 一致。

**检查点**：
- `novaic-gateway/gateway/api/p2p.py`：my-devices 的 devices[].online
- `novaic-gateway/gateway/api/internal/pc_client.py`：DeviceRegistry.DeviceState.is_connected

---

### 2.3 device 状态计算（Gateway 侧）

**需求**：API 返回 device 时，附带 `available` 或等效字段

| 条件 | available |
|------|-----------|
| device.pc_client_id 为空 | false（未绑定 PC） |
| pc_client offline | false（unavailable） |
| pc_client online 且 device 未运行 | false（stopped） |
| pc_client online 且 device 运行中 | true（running） |

**实现方式**：

1. **方案 A**：在 `GET /api/devices`、`GET /api/devices/:id` 响应中增加 `available: boolean`
   - 计算逻辑：查 DeviceRegistry 判断 pc_client 是否连接，再查 device 运行状态（vm_status 或 status 轮询结果）
2. **方案 B**：前端用现有 `devices` + `by_app_instance` 自行计算
   - 前端已有 listForUser + getMyDevices(by_app_instance)
   - 可推导：device.pc_client_id 在 by_app_instance 某楼层的 devices 中且该楼层有在线 pc → available 取决于 device 的 running 状态

**建议**：优先方案 B（前端计算），减少 Gateway 改动。若需统一语义，再在 Gateway 增加 `available` 字段。

---

### 2.4 Agent 调用 device 时的校验

**涉及接口**：device start、stop、status、VNC 相关、vm_users 等

**校验流程**：

1. 校验 device 归属：`device.user_id == 请求 user_id`
2. 若 device.pc_client_id 为空 → 返回 400/404，提示「设备未绑定物理 PC」
3. 查 DeviceRegistry：该 pc_client 是否连接且属于该 user
   - 若 pc offline 或属于其他 user → 返回 503，提示「设备当前不可用（PC 离线或被其他用户占用）」
4. 若 pc online 且属于该 user → 继续原有逻辑（转发 VmControl 等）

**文件**：
- `novaic-gateway/gateway/api/devices.py`：start、stop、status、setup 等
- `novaic-gateway/gateway/api/vm_users.py`：依赖 device 的操作
- `novaic-gateway/gateway/api/vm.py`：VNC、vm_status 等

**新增工具函数**：`check_device_available(device, user_id) -> bool` 或 `ensure_device_available(device, user_id) -> None`（不可用则 raise HTTPException）

---

## 3. 前端改动

### 3.1 Devices 列表按楼层展示（已完成）

- AgentDrawer devices tab：按 by_app_instance 分组
- 无楼层时扁平展示

### 3.2 device 状态展示

**当前**：DeviceStatusStore 轮询 `GET /api/devices/:id/status` 得到 running/stopped

**目标**：区分 unavailable / stopped / running

| 状态 | 展示 | 条件 |
|------|------|------|
| unavailable | 置灰、不可操作 | pc_client offline，或 device.pc_client_id 不在任何在线楼层 |
| stopped | 可启动 | pc_client online，device 未运行 |
| running | 可操作 | pc_client online，device 运行中 |

**实现**：
- 用 `by_app_instance` 判断 pc_client 是否在线（某楼层的 devices 中有对应 pc_client_id 且在线）
- 若 device.pc_client_id 不在任何在线楼层 → unavailable
- 若在在线楼层 → 用现有 status 轮询得到 stopped/running

### 3.3 前端类型与 UI

- 扩展 DeviceStatus 或增加 `available?: boolean`
- 列表项：unavailable 时禁用操作按钮，显示「不可用」或「PC 离线」

---

## 4. VmControl 改动

### 4.1 vm_status_report 发送（已完成）

- 连接后立即上报
- 心跳时定期上报

### 4.2 仅写入、不依赖清除

- 当前实现已满足「只写入」：仅对 vm_ids 设置 pc_client_id
- 需**移除清除逻辑**（见 2.1）

---

## 5. 任务拆解与优先级

### Phase 1：vm_status_report 只写不清

| 任务 | 文件 | 说明 | 状态 |
|------|------|------|------|
| P1-1 | pc_client.py | 移除 vm_status_report 中的「清除未上报 device」逻辑 | ✅ 已完成 |

### Phase 2：pc_client online 与 device available 语义

| 任务 | 文件 | 说明 | 状态 |
|------|------|------|------|
| P2-1 | 前端 AgentDrawer | 根据 by_app_instance 推导 device available | ✅ 已完成 |
| P2-2 | 前端 UI | unavailable 时置灰、禁用操作、展示「不可用」 | ✅ 已完成 |

### Phase 3：Agent 调用校验

| 任务 | 文件 | 说明 | 状态 |
|------|------|------|------|
| P3-1 | devices.py | 新增 ensure_device_available，start/stop/status 前调用 | ✅ 已完成 |
| P3-2 | vm_users.py、vm.py | 依赖 device 的接口增加校验 | ✅ 已完成 |
| P3-3 | 错误码与文案 | 503 + 明确提示「设备不可用」 | ✅ 已完成 |

### 扩展：VNC 相关

| 任务 | 文件 | 说明 | 状态 |
|------|------|------|------|
| Ext-1 | vm.py | get_vnc_status 增加 ensure_device_available 校验 | ✅ 已完成 |

### Phase 4：可选增强

| 任务 | 说明 | 状态 |
|------|------|------|
| P4-1 | Gateway devices API 返回 available 字段 | ✅ 已完成（GET /api/devices、GET /api/devices/:id 返回 available） |
| P4-2 | Android vm_status_report | ✅ 已完成（VmControl 上报 android_serials，Gateway 按 device_serial 映射） |

---

## 6. 依赖关系

```
P1-1 (移除清除) ─────────────────────────────────────────┐
                                                         │
P2-1 (前端 available 推导) ← by_app_instance + devices   │
P2-2 (UI unavailable) ← P2-1                             │
                                                         │
P3-1 (check_device_available) ← DeviceRegistry           │
P3-2 (接口校验) ← P3-1                                    │
P3-3 (错误文案) ← P3-1, P3-2                              │
```

---

## 7. 验收标准

1. **vm_status_report**：仅写入 pc_client_id，不清除
2. **pc_client offline**：其下 devices 在前端显示为 unavailable
3. **pc_client online**：device 显示 stopped/running，可正常操作
4. **Agent 调用 offline device**：返回 503，提示「设备不可用」
5. **换用户登录**：不清除 pc_client_id，通过 available 正确区分
