# Phase 2.3 多 PC 路由 — 10 Subagent 审核汇总

> 2025-03-12：对 Phase 2.3 改动进行 10 名 subagent 全面审核，客观评估并吸收确实有问题之处。

---

## 一、审核范围

本次审核覆盖的改动：

- **后端**：`devices.py`（`_is_linux_device_running`、`_is_android_device_running`、`delete_device`、`_delete_avd`、`_get_pc_manager_for_device`）、`pc_client.py`、schema v54、DeviceRepository
- **前端**：`api.ts` devices API、`useDeviceVNCConnection`、`useDeviceStatusPolling`、`DeviceManagerModal`、Add modals、vmService/vncBridge

---

## 二、Subagent 发现汇总

### 2.1 已确认并修复的问题

| # | 文件:行 | 严重性 | 问题 | 处理 |
|---|---------|--------|------|------|
| 1 | devices.py:474 | **Critical** | `_setup_android_device(device, setup_req, repo)` 缺少 `user_id`、`pc_client_id`，Android CREATED 自动 setup 会 `TypeError` | ✅ 已修复：传入 `user_id, pc_client_id` |
| 2 | useDeviceVNCConnection.ts:62,69 | **High** | `getVncTransport(deviceId)`、`getVncUrl(deviceId)` 未传 `pcClientId`，多 PC 时 VNC 路由错误 | ✅ 已修复：传入 `pcClientId ?? undefined` |
| 3 | useDeviceVNCConnection.ts:92 | **High** | `checkWebSocket` 依赖数组缺少 `pcClientId` | ✅ 已修复：加入 `pcClientId` |
| 4 | DeviceManagerModal.tsx:216,227,242 | **Medium** | `handleStart`、`handleStop`、`handleDelete` 未传 `pc_client_id` | ✅ 已修复：从 `devices.find` 取 `pc_client_id` 传入 |
| 5 | devices.py:173 | **Low** | `device.pc_client_id` 未 strip，仅空格时可能误用 | ✅ 已修复：`(getattr(...) or "").strip()` |
| 6 | VmUserVNCView | **Medium** | 子用户 VNC 未传 pc_client_id | ✅ 已修复：增加 `pcClientId` prop，DeviceManagerPage 传入 |

### 2.2 原暂缓项（已全部实现）

| # | 问题 | 状态 |
|---|------|------|
| 1 | **schema.py** 迁移失败 re-raise | ✅ 已实现 |
| 2 | **ConnectionError → 503** | ✅ 已实现 |
| 3 | **delete_device AVD 失败反馈** | ✅ 已实现：返回 partial_success + warnings |
| 4 | **pc_client.py _pending lock** | ✅ 已实现：add/pop 时持 device._lock |
| 5 | **DeviceStatusStore 碰撞** | 误判，无需修改 |
| 6 | **vm.py / agents.py 传 user_id** | ✅ 已实现 |
| 7 | **Add modals 传 pcClientId** | ✅ 已实现 |
| 8 | **VmUserVNCView** | ✅ 已修复 |
| 9 | **startDevice/stopDevice 取消** | ✅ 已实现：actionGenRef |
| 10 | **checkWebSocket errorMsg** | ✅ 已实现 |

### 2.3 各 Subagent 结论摘要

| Subagent | 关注点 | 主要发现 |
|----------|--------|----------|
| 1 | devices.py 逻辑 | Critical: 474 行 `_setup_android_device` 缺参；Medium: AVD 删除无反馈、status 离线边缘 |
| 2 | pc_client.py | Medium: ConnectionError→500；Low: _pending lock、user_id 校验 |
| 3 | schema/Repository | Medium: 迁移失败仍 bump version；Low: UpdateDeviceRequest 无 pc_client_id |
| 4 | api.ts | Low: deviceId 未 encode、whitespace pcClientId；Medium: DeviceStatusStore 碰撞（误判） |
| 5 | useDeviceVNCConnection | High: VNC 未传 pcClientId、无取消、checkWebSocket 缺 deps |
| 6 | useDeviceStatusPolling | Medium: 缺 pc_client_id 时查错 PC；Low: useMemo 依赖 |
| 7 | Add modals | High: setup/start 未传 pcClientId；需 my-devices 解析 |
| 8 | vmService/vncBridge | Critical: useDeviceVNCConnection 未传 pc_client_id；VmUserVNCView 同理 |
| 9 | 集成流程 | Critical: 474 行；Medium: VNC transport；Low: DeviceListPanel 未用 |
| 10 | 安全 | OK：user_id 校验、设备归属正确；High: vm.py 未传 user_id（非本 Phase） |

---

## 三、本次已修复项

1. **devices.py:474** — `_setup_android_device` 增加 `user_id, pc_client_id`
2. **useDeviceVNCConnection.ts** — `getVncTransport`、`getVncUrl` 传入 `pcClientId`；`checkWebSocket` 依赖加入 `pcClientId`
3. **DeviceManagerModal.tsx** — `handleStart`、`handleStop`、`handleDelete` 传入 `device.pc_client_id`
4. **devices.py:173** — `_get_pc_manager_for_device` 对 `device.pc_client_id` 做 strip
5. **VmUserVNCView** — 增加 `pcClientId` prop，`getVncTransport` 传入；DeviceManagerPage 传入 `effectiveSelectedDevice.pc_client_id`

---

## 四、后续建议（已全部实现）

| 优先级 | 项 | 说明 |
|--------|-----|------|
| P1 | Add modals 传 pcClientId | ✅ 已实现：api.p2p.getMyDevices + resolveCurrentPcClientId |
| P1 | ~~VmUserVNCView 传 pc_client_id~~ | ✅ 已实现 |
| P2 | ConnectionError → 503 | ✅ 已实现：_setup_android_device、_start_android_device、_stop_device Android |
| P2 | 迁移失败 re-raise | ✅ 已实现：schema v54 非 duplicate 错误 re-raise |
| P2 | startDevice/stopDevice 取消 | ✅ 已实现：actionGenRef 世代计数 |
| P3 | checkWebSocket 设置 errorMsg | ✅ 已实现：catch 中 setErrorMsg |
| P3 | UpdateDeviceRequest 支持 pc_client_id | ✅ 已实现 |
| P3 | vm.py/agents.py 传 user_id | ✅ 已实现：vm.py、agents.py、vm_users.py 全部传入 user_id |

---

## 五、验收结论

- **Critical/High**：已全部修复
- **Medium**：DeviceManagerModal、VmUserVNCView 已修复；Add modals 留待后续
- **Low**：`_get_pc_manager_for_device` strip 已修复；其余为优化项

Phase 2.3 多 PC 路由核心功能已就绪，单 PC 兼容，多 PC 下 start/stop/status/delete 及 VNC 连接可正确路由。

---

## 六、第二轮 Subagent 审核（9 暂缓项实现后）

> 对 9 项暂缓实现完成后的代码进行再次审核，吸收确实有问题之处并修复。

### 6.1 高优先级（已修复）

| 文件 | 行 | 问题 | 修复 |
|------|-----|------|------|
| vm_users.py | 100 | `device['status']` 应为 `device_row['status']`，否则 NameError | ✅ `device_row['status']` |
| agents.py | 568 | `vm_shutdown(agent_id)` 应使用 `vm_id`（device_id） | ✅ `_resolve_vm_id_for_agent` 解析后传入 |
| devices.py | 409-411 | `except Exception` 会吞掉 `HTTPException(503)`，delete 仍返回 200 | ✅ 先 `except HTTPException: raise` |

### 6.2 中优先级（已修复）

| 文件 | 行 | 问题 | 修复 |
|------|-----|------|------|
| devices.py | 768-775 | `android_devices()` 的 `ConnectionError` 被 `except Exception` 捕获 | ✅ 单独 `except ConnectionError` 并 raise 503 |
| devices.py | 755-757 | Linux `_stop_device` 在 ConnectionError 时返回 200，与 Android 不一致 | ✅ raise HTTPException(503) |
| AddLinuxVMUserModal.tsx | 80 | 未检查 `pcClientId === undefined`，可能路由到错误 PC | ✅ 检查并提示「请选择目标 PC 或确保 Tauri 应用已连接」 |
| AddAndroidModal.tsx | 222 | 同上 | ✅ 同上 |
| api.ts | 1111-1114 | `api.devices.delete` 返回 `Promise<void>`，无法处理 partial_success | ✅ 改为返回 `{ status, message?, warnings? }` |
| DeviceManagerModal.tsx | 244 | 未处理 delete 返回的 partial_success 和 warnings | ✅ 解析 `res.warnings` 并 setError 展示 |
| useDeviceVNCConnection.ts | 153-154 | `deviceId` 变为 null 时未增加 actionGenRef，旧异步操作仍可能更新状态 | ✅ 在 reset 前 `actionGenRef.current += 1` |
| useDeviceVNCConnection.ts | 181-184 | 设备为 stopped 时未清空 errorMsg，旧错误会残留 | ✅ `setErrorMsg('')` |

### 6.3 低优先级/暂不处理

- **pc_client _handle_device_message**：当前单协程流程下无实际竞态，加锁仅为一致性和未来防护
- **schema v54 re-raise**：逻辑正确，失败时不会 bump version，会重试
- **UpdateDeviceRequest pc_client_id**：无校验，可接受

### 6.4 本次修复清单

1. **vm_users.py** — `device_row['status']` 修正 NameError
2. **agents.py** — `remove_vm_config` 中通过 `_resolve_vm_id_for_agent` 得到 vm_id 再调用 `vm_shutdown`
3. **devices.py** — delete_device 中 `except HTTPException: raise`；Linux/Android `_stop_device` ConnectionError 统一 raise 503；`android_devices()` 单独处理 ConnectionError
4. **useDeviceVNCConnection.ts** — deviceId null 时 bump actionGenRef；stopped 时清空 errorMsg
5. **AddLinuxVMUserModal** / **AddAndroidModal** — pcClientId 为 undefined 时提示并中止
6. **api.ts** — `devices.delete` 返回响应体
7. **DeviceManagerModal** — 处理 partial_success 和 warnings
