# Device/PC Client Online Iteration — Third-Round Security & Data Integrity Review

> **Scope**: Security and data integrity. Focus: user_id validation, pc_client_id routing, vm_status_report isolation, DeviceRegistry, JWT/x-user-id, SQL injection, IDOR.

---

## Executive Summary

| Severity | Count | Summary |
|----------|-------|---------|
| HIGH | 0 | — |
| MEDIUM | 4 | update_device pc_client_id; user_id=local deployment; stop-all; debug leak |
| LOW | 4 | Token reuse semantics; debug endpoint; setup/deploy-wait; list_vm_users |

---

## 1. user_id Validation Before ensure_device_available

**Question**: Do all device/VM endpoints check ownership before `ensure_device_available`?

### 1.1 devices.py ✅

| Endpoint | Ownership Check | ensure_device_available |
|----------|-----------------|-------------------------|
| `POST /devices/{id}/start` | `_check_device_owner` L503 | L523 (skip if Android CREATED) |
| `POST /devices/{id}/stop` | `_check_device_owner` L566 | L567 |
| `GET /devices/{id}/status` | `_check_device_owner` L594 | L601 |
| `POST /devices/{id}/vmuse/sync` | `_check_device_owner` L627 | L628 |
| `POST /devices/{id}/setup` | `_check_device_owner` L416 | ❌ (by design) |
| `DELETE /devices/{id}` | `_check_device_owner` L350 | ❌ (by design) |

**Verdict**: ✅ All endpoints that call `ensure_device_available` first call `_check_device_owner`.

### 1.2 vm.py ✅

| Endpoint | Ownership Check | ensure_device_available |
|----------|-----------------|-------------------------|
| `POST /start` | `check_agent_access` + `_ensure_device_available_for_vm` (includes `device_row.user_id == user_id`) | via `_ensure_device_available_for_vm` |
| `POST /stop` | same | same |
| `GET /status/{agent_id}` | same | same |
| `GET /is-running/{agent_id}` | same | same |
| `GET /vnc/status/{agent_id}` | same | same |

**Verdict**: ✅ `_ensure_device_available_for_vm` (vm.py:321–333) enforces `device_row.user_id == user_id` before calling `ensure_device_available`.

### 1.3 vm_users.py ✅

| Endpoint | Ownership Check | ensure_device_available |
|----------|-----------------|-------------------------|
| `POST /devices/{id}/vm-users` | `_require_device` L97 | L98 |
| `POST /devices/{id}/vm-users/{username}/restart` | `_require_device` L158 | L161 |
| `DELETE /devices/{id}/vm-users/{username}` | `_require_device` L186 | L187 |
| `GET /devices/{id}/vm-users` | `_require_device` L82 | ❌ (read-only, no routing) |

**Verdict**: ✅ All write endpoints that need routing check ownership first. `list_vm_users` does not call `ensure_device_available` (read-only, no PC routing). **LOW**: Consider adding `ensure_device_available` if the UI needs to know device availability for display; currently it does not affect security.

---

## 2. pc_client_id in Request — Can User Route to Another User's PC?

**Question**: Can a user pass arbitrary `pc_client_id` to route commands to another user's PC?

### 2.1 Flow Analysis

```
devices.py: _get_pc_manager_for_device(device, user_id, pc_client_id)
  → target = pc_client_id or device.pc_client_id
  → get_pc_client_manager(user_id, target)

pc_client.py: get_pc_client_manager(user_id, pc_client_id)
  → device = _registry.get_device(target_id)
  → if device and device.is_connected:
       if user_id is None or device.user_id == user_id:
           return _DeviceManagerAdapter(device)
  → return _DisconnectedAdapter()
```

**Verdict**: ✅ **Protected**. When `pc_client_id` belongs to another user, `device.user_id != user_id` → `_DisconnectedAdapter()` → commands fail with `ConnectionError` (503). User cannot route to another user's PC.

### 2.2 MEDIUM: update_device Allows Arbitrary pc_client_id

**Location**: `devices.py:419–334`, `UpdateDeviceRequest.pc_client_id`

**Issue**: User can PATCH their device with `pc_client_id: "other-user-pc-id"`. The device record is updated. On subsequent start/stop, `ensure_device_available` uses `device.pc_client_id` → looks up `other-user-pc-id` in DeviceRegistry → `dev_state.user_id != user_id` → 503. So no cross-user command routing.

**Risk**: Data integrity. User can poison their own device with an invalid `pc_client_id`, making it unusable until fixed. Also, no validation that `pc_client_id` belongs to the user or exists in DeviceRegistry.

**Fix**:
```python
# In update_device, when pc_client_id is in updates:
if 'pc_client_id' in updates:
    pc_id = (updates.get('pc_client_id') or '').strip()
    if pc_id:
        registry = get_device_registry()
        dev_state = registry.get_device(pc_id)
        if dev_state is None or dev_state.user_id != user_id:
            raise HTTPException(400, "pc_client_id must be a PC that belongs to you and is connected")
```

**Severity**: MEDIUM (data integrity, self-DoS).

---

## 3. vm_status_report — Can Malicious Payload Affect Other Users?

**Question**: Only updates `d.user_id == user_id`. Can malicious `vm_ids` affect other users?

**Location**: `pc_client.py:603–644`

```python
for vid in vm_ids:
    if vid:
        d = repo.get(vid)
        if d and d.user_id == user_id:
            repo.update(vid, pc_client_id=pc_id)
for serial in android_serials:
    if serial:
        rows = db.fetchall(
            "SELECT id FROM devices WHERE user_id = ? AND type = 'android' AND device_serial = ?",
            (user_id, serial),
        )
        for row in rows:
            repo.update(row["id"], pc_client_id=pc_id)
```

**Verdict**: ✅ **Protected**. 
- Linux: Only updates devices where `d.user_id == user_id`. Attacker sending `vm_ids: ["victim-device-id"]` → `repo.get("victim-device-id")` returns device with `user_id != attacker_id` → skip.
- Android: Query filters by `user_id = ?` and `device_serial = ?`. Only the connecting user's devices can be updated.

**No cross-user data corruption.**

---

## 4. DeviceRegistry — device_id + user_id, Token Reuse

### 4.1 Same device_id Different user — Reject ✅

**Location**: `pc_client.py:84–95`

```python
if device_id in self._devices:
    device = self._devices[device_id]
    if device.user_id != user_id:
        raise ValueError("device_id already registered to a different user")
```

**Verdict**: ✅ Correctly rejects when same `device_id` (pc_client_id) connects with different `user_id`.

### 4.2 Token Reuse

**Question**: What about token reuse?

**Analysis**:
- **WebSocket session**: No traditional token. Connection identity = `(device_id, user_id)` from headers. `user_id` comes from nginx/JWT (`x-user-id`). If JWT is compromised, attacker could connect their PC with victim's `user_id` — general JWT compromise, not DeviceRegistry-specific.
- **DeviceRegistry**: When `device_id` already exists with `user_id` A, new connection with `user_id` B is rejected. No "reuse" of a device slot to switch users.
- **Physical PC, user switch**: User A logs out, User B logs in on same PC. Cloud Bridge reconnects with `device_id=X`, `user_id=B`. Registry has `device_id` with `user_id=A` → reject. User B cannot connect until User A's session is cleaned. (Known from R2: "换用户登录时 DeviceRegistry 阻塞".)

**Verdict**: ✅ No token reuse vulnerability. DeviceRegistry semantics are correct.

**LOW**: Document that on user switch, the old connection must disconnect (or implement explicit session handover) before the new user can connect.

---

## 5. JWT/nginx x-user-id — user_id=local, Other Paths?

### 5.1 vm_status_report Skips DB When user_id=local ✅

**Location**: `pc_client.py:618–621`

```python
user_id = device.user_id or "local"
if user_id == "local":
    logger.debug("[PcClient] vm_status_report skipped (user_id=local, no DB update)")
else:
    # DB update
```

**Verdict**: ✅ Correct. Unauthenticated connections (no `x-user-id`) do not write to DB.

### 5.2 Other Paths Using user_id=local?

**Analysis**:
- **API endpoints**: All use `Depends(get_current_user)` → 401 if no valid JWT. No API path uses `user_id=local`.
- **WebSocket /internal/pc/ws**: Only path where `user_id=local` can occur (when `x-user-id` is missing). The only message handler that uses `user_id` for DB writes is `vm_status_report`, which skips when `user_id=local`.

**Verdict**: ✅ No other path uses `user_id=local` for sensitive operations.

### 5.3 MEDIUM: Deployment Dependency on x-user-id

**Issue**: If nginx does not inject `x-user-id`, all Cloud Bridge connections use `user_id=local` → no DB updates from `vm_status_report` → devices never get `pc_client_id` persisted → `available` logic breaks.

**Fix**: Document deployment requirement: nginx must inject `x-user-id` from JWT for production. Add health check or startup validation that rejects misconfiguration.

---

## 6. SQL Injection, IDOR

### 6.1 SQL Injection

**Review**: All DB access uses parameterized queries.

| File | Pattern | Safe? |
|------|---------|-------|
| devices.py | `db.fetchall("SELECT ports FROM devices WHERE ports != '{}'")` | ✅ No user input |
| devices.py | `(device.id,)` in fetchall | ✅ Parameterized |
| vm.py | `(vm_id,)` in fetchone | ✅ Parameterized |
| vm_users.py | `(device_id,)`, `(device_id, username)` | ✅ Parameterized |
| pc_client.py | `(user_id, serial)` in fetchall | ✅ Parameterized |
| device.py (repo) | `(device_id,)` in all queries | ✅ Parameterized |
| DeviceRepository.update | `set_clauses = [f"{k} = ?" for k in kwargs.keys()]` | ✅ Keys from Pydantic model, values parameterized |

**Verdict**: ✅ No SQL injection. All user input is passed as parameters.

### 6.2 IDOR (Insecure Direct Object Reference)

**Review**:
- **devices**: `device_id` from path → `_check_device_owner` enforces `device.user_id == user_id`. ✅
- **vm**: `agent_id` from path/body → `check_agent_access` enforces ownership. `vm_id` resolved from agent binding → `_ensure_device_available_for_vm` enforces `device_row.user_id == user_id`. ✅
- **vm_users**: `device_id` from path → `_require_device` enforces `row["user_id"] == user_id`. `username` from path → scoped to `device_id` which is already validated. ✅
- **p2p**: `relay-request` uses `target_device_id` → `entry.user_id != user_id` → 403. ✅

**Verdict**: ✅ No IDOR. All endpoints validate resource ownership.

---

## 7. Additional Findings

### 7.1 MEDIUM: update_device pc_client_id Validation (Data Integrity)

**Location**: `devices.py:419–334`

**Issue**: User can set `pc_client_id` to any string. No validation that:
1. The PC belongs to the user
2. The PC exists in DeviceRegistry

**Impact**: Self-DoS (device unusable), or inconsistent data (device points to non-existent PC).

**Fix**: Validate `pc_client_id` when updating (see §2.2).

### 7.2 MEDIUM: vm/stop-all Does Not Use ensure_device_available

**Location**: `vm.py:319–352`

**Issue**: `stop_all_vms` iterates over user's agents, resolves `vm_id`, and calls `pc_manager.vm_shutdown(vm_id)` for each. It uses `get_pc_client_manager(user_id)` (first connected PC) without `_ensure_device_available_for_vm`. If user has multiple PCs and VMs spread across them, `stop-all` might only reach the first PC.

**Security impact**: Low (user can only stop their own VMs). Functional impact: Some VMs may not be stopped.

**Fix**: Either document that stop-all targets the "first" PC, or iterate per-device and call `_ensure_device_available_for_vm` per VM (more complex).

### 7.3 LOW: p2p/debug Returns Full Registry to Any Authenticated User

**Location**: `p2p.py:453–461`

**Issue**: `p2p_debug` returns `registry_summary` with all `_p2p_registry` entries. Filtering is done in `_build_device_item` but the loop is `for e in _p2p_registry.values()` — so all devices from all users are included.

**Impact**: Authenticated user can see other users' device_ids (pc_client_ids) and online status in debug output.

**Fix**: Filter to `entry.user_id == user_id` before building items:
```python
registry_summary=[
    _build_device_item(e, registry)
    for e in _p2p_registry.values()
    if e.user_id == user_id
],
```

### 7.4 LOW: setup_vm / deploy_wait — No ensure_device_available

**Location**: `vm.py:254`, `vm.py:222`

**Issue**: `setup_vm` and `deploy_wait` use `get_pc_client_manager(user_id)` (first PC) without `ensure_device_available`. By design (plan says setup doesn't require it). If user has multiple PCs, setup may target the wrong one.

**Security**: No issue (user's own resources). **LOW** documentation/UX.

---

## 8. Summary Table

| # | Severity | File:Line | Issue | Fix |
|---|----------|-----------|-------|-----|
| 1 | MEDIUM | devices.py:419–334 | update_device allows arbitrary pc_client_id; no validation | Validate pc_client_id belongs to user and is in DeviceRegistry when updating |
| 2 | MEDIUM | devices.py:419 | pc_client_id in PATCH can poison device record | Same as #1 |
| 3 | MEDIUM | Deployment | x-user-id required for vm_status_report DB writes | Document; add startup/misconfiguration check |
| 4 | MEDIUM | vm.py:319–352 | stop-all uses first PC only, no per-VM ensure | Document or refactor to per-device |
| 5 | LOW | pc_client.py | Token reuse / user switch semantics | Document session handover requirement |
| 6 | LOW | p2p.py:453–461 | debug returns all users' devices | Filter by user_id |
| 7 | LOW | vm_users.py:79 | list_vm_users has no ensure_device_available | Optional: add if UI needs availability |
| 8 | LOW | vm.py:254,222 | setup/deploy-wait target first PC | Document multi-PC behavior |

---

## 9. Recommendations

1. **Immediate**: Add `pc_client_id` validation in `update_device` (MEDIUM).
2. **Short-term**: Filter p2p/debug by user_id (LOW).
3. **Documentation**: Deployment requirements for x-user-id; multi-PC semantics for stop-all, setup, deploy-wait.
4. **Optional**: Implement DeviceRegistry session handover for user switch to avoid blocking.
