# Device / PC Client Online Iteration — Second-Round Critical Review

> Cross-cutting architecture and documentation review. Focus: plan vs implementation, data flow, semantics, API contracts, error handling, security.

---

## 1. Plan vs Implementation (docs/DEVICE_PC_CLIENT_ONLINE_PLAN.md)

### 1.1 Phases Match Implementation ✅

| Phase | Plan | Implementation | Status |
|-------|------|----------------|--------|
| P1-1 | vm_status_report 只写不清 | pc_client.py:447–471 无清除逻辑，仅写入 | ✅ |
| P2-1 | 前端根据 by_app_instance 推导 available | AgentDrawer.tsx:125–133 pcClientOnlineMap | ✅ |
| P2-2 | unavailable 时置灰、禁用操作 | AgentDrawer.tsx:284–330 DeviceListItem | ✅ |
| P3-1 | ensure_device_available, start/stop/status 前调用 | devices.py:519,563,584,617 | ✅ |
| P3-2 | vm_users.py、vm.py 增加校验 | vm_users.py:98,156,182; vm.py:349,403,460,612,713 | ✅ |
| P4-1 | devices API 返回 available | devices.py:206–214 _compute_device_available, device_to_response | ✅ |
| P4-2 | Android vm_status_report | cloud_bridge.rs:193–212 android_serials; pc_client.py:459–466 | ✅ |

### 1.2 Plan Gaps / Inconsistencies

| Issue | Priority | Location | Fix |
|-------|----------|----------|-----|
| Plan 未描述 P2P 与 DeviceRegistry 双源 | **MEDIUM** | PLAN §2.2 | 补充：getMyDevices 依赖 `_p2p_registry` + DeviceRegistry，P2P 心跳与 Cloud Bridge 为两条独立通道 |
| Plan 未提及 setup/delete 是否需 ensure_device_available | **LOW** | PLAN §2.4 | 已确认：setup 不需要（设备可能无 pc_client_id）；delete 不需要（允许删除离线设备） |
| Plan 未记录 user_id=local 时 vm_status_report 跳过 DB | **LOW** | PLAN §1.3 | 补充：未认证连接（x-user-id 缺失）时跳过 DB 写入，避免跨用户 pc_client_id 绑定 |

---

## 2. Data Flow: VmControl → vm_status_report → pc_client → DeviceRegistry + DB

### 2.1 Flow Summary

```
VmControl (cloud_bridge.rs)
  └─ fetch_running_device_ids() → (vm_ids, android_serials)
  └─ vm_status_report over WebSocket
       │
       ▼
Gateway pc_client.py _handle_device_message
  └─ vm_ids → devices.pc_client_id (WHERE user_id = x-user-id)
  └─ android_serials → devices.pc_client_id (WHERE device_serial = serial)
  └─ 无清除逻辑 ✅
       │
       ├─ DeviceRegistry: 由 /internal/pc/ws connect 写入，vm_status_report 不更新
       └─ DB: devices 表 pc_client_id 列
```

### 2.2 Gaps

| Gap | Priority | Detail | Fix |
|-----|----------|--------|-----|
| P2P 与 DeviceRegistry 不同步 | **HIGH** | `_p2p_registry` 由 `/api/p2p/heartbeat` 写入，DeviceRegistry 由 Cloud Bridge WS 写入。PC 可仅连 Cloud Bridge 而无 P2P 心跳 → getMyDevices 不包含该 PC → 前端 isAvailable=false，但 devices API available 可能为 true | 文档化：available（devices API）= Cloud Bridge 可用；前端 isAvailable = P2P + Cloud Bridge 可用（VNC 需 P2P）。或：getMyDevices 也包含仅 Cloud Bridge 在线的 PC，并标注 `p2p_ready: false` |
| user_id 来源不一致 | **MEDIUM** | vm_status_report 用 `device.user_id`（来自 WS 连接时的 x-user-id）；若 nginx 未注入 x-user-id，fallback 为 "local"，此时跳过 DB 写入 | 确保生产环境 nginx 正确注入 x-user-id；或在 plan 中明确部署要求 |
| android_serials 映射条件 | **LOW** | pc_client.py:459 `device_serial = ?` 仅匹配已存在 device；若 device 尚未创建或 device_serial 未设置，不会更新 | 符合预期：仅对已存在且 device_serial 匹配的 Android 设备更新 pc_client_id |

---

## 3. available vs online Semantics

### 3.1 Definitions

| 概念 | 来源 | 含义 |
|------|------|------|
| **devices API `available`** | devices.py `_compute_device_available` | pc_client 在 DeviceRegistry 且 is_connected，且属于当前 user，且 device.status == RUNNING |
| **p2p getMyDevices `online`** | p2p.py `_build_device_item` | `p2p_online and cloud_connected`；p2p_online = 非 stale 且 ext_addr 非 0.0.0.0；cloud_connected = DeviceRegistry.get_device 且 is_connected |
| **前端 isAvailable** | AgentDrawer pcClientOnlineMap | `device.pc_client_id` 在 by_app_instance 某楼层的 devices 中，且该设备 `online === true` |

### 3.2 Consistency

| 场景 | devices API available | getMyDevices online | 前端 isAvailable |
|------|----------------------|---------------------|------------------|
| PC 仅 Cloud Bridge，无 P2P 心跳 | true（若 device running） | N/A（PC 不在列表中） | false |
| PC Cloud Bridge + P2P 心跳，device running | true | true | true |
| PC 离线 | false | false / 不在列表 | false |
| 换用户登录，PC 被 User B 占用 | false | User A 的 getMyDevices 不含该 PC | false |

### 3.3 Issues

| Issue | Priority | Detail | Fix |
|-------|----------|--------|-----|
| 前端未使用 devices API 的 available | **MEDIUM** | AgentDrawer 完全用 by_app_instance 推导 isAvailable，忽略 `device.available` | 可选：当 `device.pc_client_id` 不在 by_app_instance 时，fallback 到 `device.available`，避免「API 认为可用但 UI 显示不可用」 |
| by_app_instance 仅含 P2P 注册 PC | **MEDIUM** | 仅 Cloud Bridge 在线的 PC 不会出现在 getMyDevices → 无法按楼层展示 | 若需支持「仅 Cloud Bridge」场景，需扩展 getMyDevices 或新增接口返回 DeviceRegistry 中的 PC |

---

## 4. API Contracts & Frontend Merge

### 4.1 Data Sources

- **devices.listForUser()** → `GET /api/devices` → 返回 `devices[]`，含 `available`、`pc_client_id`
- **p2p.getMyDevices(appInstanceId)** → `GET /api/p2p/my-devices` → 返回 `devices[]`、`by_app_instance[]`

### 4.2 Frontend Merge (AgentDrawer.tsx)

```typescript
// 82-109: 并行请求
api.devices.listForUser()
api.p2p.getMyDevices(appInstanceId)

// 125-133: pcClientOnlineMap 从 by_app_instance 推导
pcClientOnlineMap: Map<pc_client_id, online>

// 137-165: devicesByFloor 按 by_app_instance 分组
// 设备归属楼层：device.pc_client_id 在 floor.devices 的 device_id 中

// 418: isAvailable = pc_client_id 在 pcClientOnlineMap 且 online
isAvailable={!!(device.pc_client_id && pcClientOnlineMap.get(device.pc_client_id))}
```

### 4.3 Gaps

| Issue | Priority | Detail | Fix |
|-------|----------|--------|-----|
| 无合并冲突处理 | **LOW** | devices 与 by_app_instance 可能不同步（轮询间隔、网络延迟） | 当前设计可接受；若需更强一致性，可考虑单一接口返回 devices + 楼层 + available |
| Device 类型未声明 available | **LOW** | types/index.ts DeviceConfig 无 `available?` | 在 DeviceConfig 中增加 `available?: boolean` 以匹配 API 响应 |

---

## 5. Error Handling Consistency

### 5.1 Current Usage

| 场景 | 状态码 | 位置 |
|------|--------|------|
| device 不存在 | 404 | devices.py:160 _check_device_owner |
| device 非当前用户 | 403 | devices.py:162 |
| pc_client_id 为空 | 400 | devices.py:179 ensure_device_available |
| pc_client offline | 503 | devices.py:184 |
| pc_client 被其他用户占用 | 503 | devices.py:186 |
| agent 无 device 绑定 | 400 | vm.py:328 _ensure_device_available_for_vm |
| VM not found | 404 | vm.py:364,394 |

### 5.2 Inconsistencies

| Issue | Priority | Detail | Fix |
|-------|----------|--------|-----|
| vm.py "Device not found" 用 400 | **LOW** | vm.py:328 `device_row is None` → 400。REST 惯例「资源不存在」常用 404 | 可改为 404，或保留 400 并注明为「请求参数/绑定错误」 |
| 503 文案不统一 | **LOW** | devices.py 用「设备当前不可用：PC 离线或未连接」；vm.py 用「CloudBridge not connected」 | 统一为「设备当前不可用：PC 离线或未连接」 |
| ConnectionError → 503 | **OK** | 各处 ConnectionError 均映射为 503 | 一致 |

### 5.3 Recommended Convention (for docs)

| 状态码 | 使用场景 |
|--------|----------|
| 400 | 请求错误：pc_client_id 为空、无效 subject_type、设备状态不允许操作 |
| 403 | 权限：非设备所有者、device_id 属于其他用户 |
| 404 | 资源不存在：device、vm_user、subject、session |
| 503 | 服务不可用：PC 离线、Cloud Bridge 未连接、被其他用户占用 |

---

## 6. Security

### 6.1 User Isolation

| 检查点 | 实现 | 状态 |
|--------|------|------|
| devices list | `repo.list_by_user(user_id)` | ✅ |
| device get | `_check_device_owner` | ✅ |
| ensure_device_available | `dev_state.user_id != user_id` → 503 | ✅ |
| getMyDevices | `if entry.user_id == user_id` | ✅ |
| p2p heartbeat | `entry.user_id != user_id` → 403 | ✅ |
| vm_status_report | `d.user_id == user_id` 才更新 | ✅ |

### 6.2 Security Concerns

| Issue | Priority | Detail | Fix |
|-------|----------|--------|-----|
| 换用户登录时 DeviceRegistry 阻塞 | **HIGH** | pc_client.py:86–95：同一 device_id 已存在且 user_id 不同时直接拒绝连接。User A 断开后 DeviceState 仍保留，User B 无法连接 | 在 disconnect 时若 `device.ws is None` 且超过一定时间无重连，可考虑移除或允许新 user 覆盖；或显式实现「用户切换」流程 |
| P2P 换用户时心跳 403 | **HIGH** | p2p.py:183–188：已存在 entry 且 user_id 不同时返回 403。User A 断开后 entry 仍存在，User B 心跳被拒 | 当 entry 已 stale（如 >60s）时，允许新 user 覆盖；或 disconnect 时清理 P2P entry |
| user_id=local 时 vm_status_report 跳过 | **OK** | pc_client.py:455–457 避免未认证连接写 DB | 已防护 |
| x-user-id 依赖 nginx | **MEDIUM** | 若 nginx 未注入，user_id 为 "local"，所有 vm_status_report 不写 DB | 文档化部署要求，确保生产环境注入 x-user-id |

---

## 7. Summary: Priority Matrix

### HIGH

1. **P2P / DeviceRegistry 双源不同步** — 仅 Cloud Bridge 在线的 PC 不在 getMyDevices，前端 isAvailable 恒为 false。
2. **换用户登录时 DeviceRegistry 阻塞** — 旧 DeviceState 阻止新用户连接。
3. **P2P 换用户时心跳 403** — 旧 P2P entry 阻止新用户心跳。

### MEDIUM

4. **前端未使用 devices API 的 available** — 可能与 API 语义不一致。
5. **Plan 未描述 P2P 与 DeviceRegistry 双源** — 文档不完整。
6. **user_id / x-user-id 部署要求** — 需在文档中明确。

### LOW

7. **vm.py "Device not found" 用 400** — 可考虑改为 404。
8. **503 文案不统一** — 建议统一。
9. **Device 类型缺少 available** — 类型与 API 对齐。
10. **Plan 未记录 setup/delete 不需 ensure_device_available** — 文档补充。

---

## 8. Recommended Fixes (Concrete)

### 8.1 DeviceRegistry 换用户 (pc_client.py)

```python
# In disconnect(): consider removing DeviceState when ws closes and no pending
# Or: add TTL-based cleanup for disconnected devices
# Or: on connect, if existing device has ws=None and last_seen > 5min, allow user takeover
```

### 8.2 P2P 换用户 (p2p.py)

```python
# In p2p_heartbeat: when entry exists and entry.user_id != user_id,
# if entry.is_stale: allow takeover (overwrite entry with new user_id)
```

### 8.3 Plan 文档更新 (DEVICE_PC_CLIENT_ONLINE_PLAN.md)

- 增加「P2P 与 DeviceRegistry 双源」说明。
- 增加「user_id=local 时跳过 DB」说明。
- 增加「setup/delete 不需 ensure_device_available」说明。
- 增加部署要求：nginx 必须注入 x-user-id。

### 8.4 前端可选增强 (AgentDrawer.tsx)

```typescript
// Fallback to API available when pc_client_id not in by_app_instance
isAvailable={
  !!(device.pc_client_id && pcClientOnlineMap.get(device.pc_client_id)) ||
  (device as { available?: boolean }).available === true
}
```
