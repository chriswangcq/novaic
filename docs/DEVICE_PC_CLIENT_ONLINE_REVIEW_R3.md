# Device/PC Client Online Iteration — Third-Round Critical Review

> **Scope**: Cross-API consistency and contract review. Focus: data merge, status codes, error handling, get_pc_client_manager semantics, early-return patterns.

---

## 1. devices list vs p2p getMyDevices — available vs online, frontend merge

### 1.1 Data Sources

| Source | Field | Location | Semantics |
|--------|-------|----------|-----------|
| **devices list** | `available` | `devices.py:206-214` `_compute_device_available` | pc_client in DeviceRegistry + is_connected + user_id match + device.status=RUNNING |
| **p2p getMyDevices** | `online` in `by_app_instance[].devices[]` | `p2p.py:371-394` `_build_device_item` | p2p_online (non-stale, ext_addr≠0.0.0.0) AND cloud_connected (DeviceRegistry.get_device + is_connected) |

### 1.2 Frontend Merge Logic

**AgentDrawer.tsx:542**:
```typescript
isAvailable={!!(device.pc_client_id && (pcClientOnlineMap.get(device.pc_client_id) ?? device.available))}
```

- `pcClientOnlineMap`: built from `by_app_instance` floors; key = `device_id` (pc_client_id), value = `online ?? false`
- Merge: `pcOnline ?? device.available` — when `pc_client_id` not in by_app_instance, falls back to `device.available`

### 1.3 When Both Missing

| Scenario | pcClientOnlineMap.get(pc_client_id) | device.available | isAvailable |
|----------|-------------------------------------|------------------|-------------|
| pc_client_id empty | N/A (short-circuit) | any | **false** |
| pc in by_app_instance, online=true | true | any | **true** |
| pc in by_app_instance, online=false | false | any | **false** |
| pc NOT in by_app_instance (e.g. Cloud Bridge only) | undefined | true | **true** (fallback) |
| pc NOT in by_app_instance | undefined | false/undefined | **false** |

**Conclusion**: When both missing (pc not in by_app_instance AND device.available undefined/false), `isAvailable=false`. Behavior is correct; fallback to `device.available` handles "Cloud Bridge only, no P2P" case.

### 1.4 Issues

| Severity | Issue | Location | Fix |
|----------|------|----------|-----|
| **LOW** | `DeviceConfig` has `available?: boolean` (types/index.ts:31) — API contract documented | types/index.ts | ✅ Already present |
| **LOW** | If `listForUser` fails but `getMyDevices` succeeds, devices come from `[]`; `device.available` never present | AgentDrawer:88-98 | Consider surfacing partial failure to user |

---

## 2. ensure_device_available — 400 vs 503, call site handling

### 2.1 ensure_device_available Semantics (devices.py:166-186)

| Condition | Status | Detail |
|-----------|--------|--------|
| pc_client_id empty | **400** | "设备未绑定物理 PC，请先完成 setup" |
| dev_state is None or not is_connected | **503** | "设备当前不可用：PC 离线或未连接" |
| dev_state.user_id != user_id | **503** | "设备当前不可用：PC 已被其他用户占用" |

### 2.2 Call Sites

| Module | Endpoint/Function | Handles 400? | Handles 503? |
|--------|-------------------|--------------|-------------|
| devices.py | start_device (L523) | via HTTPException | via HTTPException |
| devices.py | stop_device (L567) | via HTTPException | via HTTPException |
| devices.py | get_device_status (L596) | N/A — early return before ensure | N/A |
| devices.py | sync_device_vmuse (L629) | via HTTPException | via HTTPException |
| vm.py | _ensure_device_available_for_vm → ensure_device_available | via HTTPException | via HTTPException |
| vm_users.py | create_vm_user (L98) | via HTTPException | via HTTPException |
| vm_users.py | restart_vm_user_vnc (L161) | via HTTPException | via HTTPException |
| vm_users.py | delete_vm_user (L187) | via HTTPException | via HTTPException |

All call sites propagate `HTTPException`; FastAPI returns the status code and detail to the client. No special handling of 400 vs 503 at call site — both surface as HTTP errors.

### 2.3 Frontend Handling

| Component | Action | Error handling |
|-----------|--------|----------------|
| DeviceManagerModal | start/stop | `catch (e: any)` — logs/surfaces generically |
| DeviceFloatingPanel | stop | `catch(e) { console.error(e); }` |
| DeviceSidebar | start/stop | `catch (error)` — generic |
| AddLinuxVMUserModal | start | `catch (err: any)` — may show message |
| AddAndroidModal | start | `catch (startErr)` |
| DeviceDesktopView | start/stop | `catch` — best-effort |
| DeviceVNCView | start/stop | `catch` — best-effort |

**Conclusion**: Frontend does not distinguish 400 vs 503. Both result in generic error display. For UX, consider:
- **400** (setup needed): "请先完成设备 setup"
- **503** (PC offline): "PC 离线或未连接，请检查网络"

| Severity | Issue | Location | Fix |
|----------|------|----------|-----|
| **MEDIUM** | Frontend does not differentiate 400 vs 503 for user-friendly messages | DeviceManagerModal, DeviceFloatingPanel, etc. | Parse `e?.response?.data?.detail` or status; show localized message for 400 vs 503 |
| **LOW** | 400/503 both propagate correctly; no backend bug | — | — |

---

## 3. get_pc_client_manager(user_id, pc_client_id=None) — when None, "first connected PC"

### 3.1 Implementation (pc_client.py:545-572)

```python
def get_pc_client_manager(user_id: Optional[str] = None, pc_client_id: Optional[str] = None):
    """
    行为：
      - pc_client_id 非空：返回该 PC 的 adapter（需属于 user_id 或 user_id 为空）
      - user_id=None：返回任意已连接设备（旧全局单例语义）
      - user_id=xxx：返回该用户的第一台已连接设备
    """
    target_id = (pc_client_id or "").strip()
    if target_id:
        # ... return specific PC or _DisconnectedAdapter
    if user_id is None:
        for device in _registry._devices.values():
            if device.is_connected:
                return _DeviceManagerAdapter(device)
        return _DisconnectedAdapter()
    devices = _registry.get_connected_devices(user_id)
    if devices:
        return _DeviceManagerAdapter(devices[0])  # FIRST connected device
    return _DisconnectedAdapter()
```

### 3.2 When pc_client_id=None

- **user_id=None**: Returns first connected device from entire registry (any user).
- **user_id=xxx**: Returns first connected device for that user (`get_connected_devices(user_id)[0]`).

Order depends on `_registry._devices.values()` / `get_connected_devices` iteration — implementation-defined, not guaranteed stable.

### 3.3 Documentation

| Location | Documented? |
|----------|-------------|
| pc_client.py docstring | ✅ Yes — "返回该用户的第一台已连接设备" |
| DEVICE_PC_CLIENT_ONLINE_PLAN.md | ❌ Not explicitly |
| UNIFIED_DEVICE_SECTION_AUDIT.md | ✅ "get_pc_client_manager 始终用第一个连接的设备" |
| docs/unify-vnc/06-phase2-multi-pc-design.md | ✅ "get_pc_client_manager(user_id) 始终返回该用户第一台已连接 PC" |

### 3.4 Call Sites Passing pc_client_id=None

| Module | Endpoint | Passes pc_client_id? |
|--------|----------|----------------------|
| vm.py | stop_all_vms (L438) | No — `get_pc_client_manager(user_id=user_id)` |
| vm.py | get_all_vm_status (L525) | No |
| vm.py | get_running_agents (L582) | No |
| vm.py | start_vm, stop_vm, get_vm_status, is_vm_running, get_vnc_status | Yes — via device_row.get("pc_client_id") |
| vm_users.py | create/restart/delete | Yes — `pc_client_id = device_row.get("pc_client_id") or None` |
| devices.py | _get_pc_manager_for_device | Yes — uses device.pc_client_id or explicit param |

**Conclusion**: When `pc_client_id` is None (e.g. device has no pc_client_id), vm_users would not reach get_pc_client_manager — ensure_device_available raises 400 first. vm.py stop_all / get_all_vm_status / get_running intentionally use "first PC" for batch operations.

| Severity | Issue | Location | Fix |
|----------|------|----------|-----|
| **LOW** | "First connected" order is implementation-defined | pc_client.py | Document that order is not guaranteed; for multi-PC, prefer explicit pc_client_id |
| **LOW** | Plan doc does not mention "first PC" semantics | DEVICE_PC_CLIENT_ONLINE_PLAN.md | Add: "get_pc_client_manager(user_id, pc_client_id=None): when pc_client_id is None, returns first connected PC for user" |

---

## 4. HTTP Status Codes — 400/403/404/503 consistency

### 4.1 devices.py

| Scenario | Code | Message |
|----------|------|---------|
| Device not found | 404 | "Device not found" |
| Access denied (wrong user) | 403 | "Access denied" |
| pc_client_id empty | 400 | "设备未绑定物理 PC，请先完成 setup" |
| PC offline / not connected | 503 | "设备当前不可用：PC 离线或未连接" |
| PC occupied by other user | 503 | "设备当前不可用：PC 已被其他用户占用" |
| Invalid subject_type | 400 | "Invalid subject_type: ..." |
| Device not ready to start | 400 | "Device is still being set up..." / "Device not ready to start..." |

### 4.2 vm.py

| Scenario | Code | Message |
|----------|------|---------|
| Device not found for agent | 400 | "Device not found for this agent" |
| Access denied | 403 | "Access denied" |
| VM not found | 404 | "VM not found" |
| Agent not found | 404 | "Agent not found: ..." |
| ConnectionError | 503 | "CloudBridge not connected" / "PC client not connected" / "vmcontrol unavailable" |

### 4.3 vm_users.py

| Scenario | Code | Message |
|----------|------|---------|
| Device not found | 404 | "Device not found" |
| Access denied | 403 | "Access denied" |
| VM Users only for Linux | 400 | "VM Users are only supported for Linux devices" |
| Device not running | 400 | "Device must be running to add users..." |
| VM user not found | 404 | "VM user '...' not found" |
| ensure_device_available | 400/503 | (delegates to devices.ensure_device_available) |

### 4.4 Inconsistencies

| Severity | Issue | Detail | Fix |
|----------|------|--------|-----|
| **MEDIUM** | "Device not found for this agent" uses 400 | vm.py:328; REST convention often uses 404 for "resource not found" | Consider 404; or document 400 = "binding/request error" |
| **LOW** | 503 message varies | devices: "设备当前不可用：PC 离线或未连接"; vm: "CloudBridge not connected" / "PC client not connected" | Unify to single convention, e.g. "Device unavailable: PC offline or not connected" |
| **LOW** | Chinese vs English mixed | devices: Chinese; vm/vm_users: mostly English | See §5 |

---

## 5. Error Messages — Chinese vs English

### 5.1 Current Usage

| Module | Language | Examples |
|--------|----------|----------|
| devices.py | **Chinese** | "设备未绑定物理 PC，请先完成 setup", "设备当前不可用：PC 离线或未连接", "设备当前不可用：PC 已被其他用户占用" |
| vm.py | **English** | "Device not found for this agent", "CloudBridge not connected", "PC client not connected" |
| vm_users.py | **English** | "Device not found", "Access denied", "VM user '...' not found" |
| p2p.py | **English** | "target device not in P2P registry", "Not your device" |

### 5.2 Recommendation

| Severity | Issue | Fix |
|----------|------|-----|
| **MEDIUM** | Mixed Chinese/English in user-facing errors | Choose one: (a) All English for API consistency, or (b) All Chinese if product is CN-only. Document in API contract. |
| **LOW** | "setup" in Chinese message | "请先完成 setup" — consider "请先完成设备初始化" for full Chinese |

---

## 6. devices.get_device_status early return — similar patterns elsewhere

### 6.1 devices.get_device_status (devices.py:578-617)

```python
pc_id = (getattr(device, "pc_client_id", None) or "").strip()
if not pc_id:
    return {
        "device_id": device_id,
        "type": device.type.value,
        "status": device.status.value,
        "running": False,
    }
ensure_device_available(device, user_id)
# ... fetch runtime status
```

**Behavior**: When `pc_client_id` is empty, returns 200 with `running: false` without calling ensure_device_available. Lenient — allows status check for devices not yet bound to a PC.

### 6.2 vm.get_vm_status (vm.py:456-505)

Calls `_ensure_device_available_for_vm` → `ensure_device_available`. If `pc_client_id` is empty, **raises 400** before any status fetch.

### 6.3 vm.get_vnc_status (vm.py:688-759)

Same as get_vm_status — `_ensure_device_available_for_vm` → **400** when pc_client_id empty.

### 6.4 vm.is_vm_running (vm.py:609-634)

Same — `_ensure_device_available_for_vm`; returns `{"running": false}` on ConnectionError/Timeout but would **400** on empty pc_client_id (from ensure_device_available).

### 6.5 Inconsistency

| Endpoint | pc_client_id empty | Behavior |
|----------|--------------------|----------|
| GET /api/devices/{id}/status | 200, `running: false` | Early return, lenient |
| GET /api/vm/status/{agent_id} | 400 | Strict, ensure_device_available |
| GET /api/vm/vnc/status/{agent_id} | 400 | Strict |
| GET /api/vm/is-running/{agent_id} | 400 | Strict |

**Rationale difference**: devices API operates on device_id directly; VM API resolves agent→device and assumes device is "ready" for VM ops. Devices status can be queried for setup/ready devices without PC binding; VM status implies "can we run/connect to VM" which requires PC.

| Severity | Issue | Location | Fix |
|----------|------|----------|-----|
| **MEDIUM** | Inconsistent handling: devices status returns 200 when pc_id empty; vm status/vnc status raise 400 | devices.py:588-596 vs vm.py | Document: devices status = "best-effort, may return running:false without PC"; vm/vnc status = "requires PC binding, 400 if not ready". Or align: devices status also call ensure_device_available and 400 when pc_id empty for consistency. |
| **LOW** | get_all_vm_status / get_running_agents do not call _ensure_device_available_for_vm per agent | vm.py:508-563, 566-606 | By design — batch ops use first PC; agents without device binding are skipped (vm_id=agent_id, no device row). Acceptable. |

---

## 7. Summary: Priority Matrix

### HIGH

- *(None in this round — previous rounds covered P2P/DeviceRegistry sync, user switch blocking.)*

### MEDIUM

1. **Frontend does not differentiate 400 vs 503** — DeviceManagerModal, DeviceFloatingPanel, etc. — Parse status/detail; show "请先完成 setup" vs "PC 离线或未连接".
2. **Status endpoint inconsistency** — devices.get_device_status returns 200 when pc_id empty; vm.get_vm_status/get_vnc_status raise 400 — Document or align.
3. **Error message language mix** — devices: Chinese; vm/vm_users: English — Standardize Chinese or English.

### LOW

4. **get_pc_client_manager "first PC" order** — Document as implementation-defined.
5. **Plan doc missing get_pc_client_manager semantics** — Add to DEVICE_PC_CLIENT_ONLINE_PLAN.md.
6. **"Device not found for this agent" 400 vs 404** — Consider 404 for REST alignment.
7. **503 message wording** — Unify across devices/vm.

---

## 8. Recommended Fixes (Concrete)

### 8.1 Frontend 400/503 handling (DeviceManagerModal, etc.)

```typescript
catch (e: any) {
  const status = e?.response?.status ?? e?.status;
  const detail = e?.response?.data?.detail ?? e?.detail ?? e?.message;
  const msg = status === 400 && /setup|绑定|物理 PC/i.test(String(detail))
    ? '请先完成设备 setup 并绑定物理 PC'
    : status === 503
    ? '设备当前不可用：PC 离线或未连接'
    : detail || '操作失败';
  // show msg to user
}
```

### 8.2 Document status endpoint contract

In DEVICE_PC_CLIENT_ONLINE_PLAN.md or API docs:

- `GET /api/devices/{id}/status`: When `pc_client_id` is empty, returns 200 with `running: false` (device not bound to PC).
- `GET /api/vm/status/{agent_id}`, `GET /api/vm/vnc/status/{agent_id}`: Require device with `pc_client_id`; return 400 when not set.

### 8.3 Unify error message language

Either:
- **Option A**: Use English for all API `detail` (e.g. "Device not bound to PC, please run setup first").
- **Option B**: Use Chinese for all (e.g. vm.py messages → Chinese).

### 8.4 get_pc_client_manager docstring addition

```python
# When pc_client_id is None: returns first connected device for user_id (or any if user_id is None).
# Order is implementation-defined; for multi-PC scenarios, always pass pc_client_id when known.
```
