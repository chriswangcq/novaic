# vm.py Second-Round Critical Review

**Scope**: Device/PC client online/availability iteration — `_ensure_device_available_for_vm` and related flows.

---

## 1. `_ensure_device_available_for_vm` Coverage

### Endpoints that use it (correct)
- `start_vm` (L349)
- `stop_vm` (L403)
- `get_vm_status` (L460)
- `is_vm_running` (L447)
- `get_vnc_status` (L513)

### Endpoints that do NOT use it

| Endpoint | Line | Assessment |
|----------|------|------------|
| **get_all_vm_status** | 412 | **OK** — Uses `vm_list()` once, no per-agent `vm_status(vm_id)`. Agents without devices simply don't appear in the result. No ensure needed. |
| **stop_all** | 315 | **Design choice** — Intentionally skips ensure. Best-effort shutdown on app exit; failures are collected in `results[vm_id] = {"error": str(e)}`. Acceptable. |

**Verdict**: Coverage is correct. `get_all_vm_status` and `stop_all` do not need per-agent ensure.

---

## 2. `_resolve_vm_id_for_agent` + 400 "Device not found" UX

**Behavior**: When agent has no binding, returns `agent_id` as `vm_id`. `_ensure_device_available_for_vm` then does `SELECT ... FROM devices WHERE id = ?` with `agent_id`. Since `devices.id` is device_id (not agent_id), no row is found → 400 "Device not found for this agent".

**Chat-only agents (no device)**:
- Calling `/api/vm/status/{agent_id}` or start/stop for a chat-only agent → 400 "Device not found for this agent".
- **Assessment**: Semantically correct — VM endpoints are for VM operations; an agent without a device cannot have VM status.
- **UX improvement (LOW)**: Consider a clearer message, e.g. `"Agent has no device binding"` or `"Agent is not configured for VM"`, to distinguish from "device exists but not found".

**Verdict**: 400 is appropriate. Optional: refine message for chat-only agents.

---

## 3. Endpoints that bypass `_ensure_device_available_for_vm`

| Endpoint | Line | Needs ensure? | Notes |
|----------|------|---------------|------|
| `setup_vm` | 253 | No | Setup creates disk before device binding; uses first connected PC. |
| `deploy_wait` | 219 | No | Part of setup flow; no device yet. |
| `get_setup_status` | 691 | No | Returns hardcoded "complete"; no vmcontrol call. |
| `deploy-vmuse` | 558 | No | Uses agent ports; targets already-running VM. No vmcontrol VM lifecycle. |
| `vmuse-health` | 641 | No | Health check via agent ports; no vmcontrol. |

**Verdict**: No VM lifecycle endpoints incorrectly bypass ensure.

---

## 4. `pc_manager.vm_status(vm_id)` when `device_row` was None — setup wizard impact

**Before**: When `device_row` was None, ensure was skipped; code could reach `pc_manager.vm_status(vm_id)`.

**After**: `device_row` None → 400 before any vmcontrol call.

**Setup wizard flow**:
- `get_setup_status` does not call `vm_status`; it returns hardcoded "complete".
- Setup uses `setup_vm`, `deploy_wait` — neither calls `_ensure_device_available_for_vm`.
- `get_vm_status` is used after setup, when the user expects a running VM.

**When would `device_row` be None?**
1. Agent has no device binding (chat-only) → 400 is correct.
2. Agent has binding but `device_id` not in `devices` table → data inconsistency; 400 is reasonable.

**Verdict**: No legitimate setup-wizard flow is broken. 400 on missing device is correct.

---

## 5. `vm_start` inside try block — HTTPException propagation

```python
# L341-391
try:
    ...
    vm_id = _resolve_vm_id_for_agent(request.agent_id, db)
    _ensure_device_available_for_vm(vm_id, user_id, db)  # Can raise HTTPException
    ...
    ctrl_result = await pc_manager.vm_start(...)
    ...
except HTTPException:
    raise   # Re-raises
except Exception as e:
    ...
```

**Assessment**: `HTTPException` is not caught by `except Exception` (FastAPI/Starlette treat it specially). The explicit `except HTTPException: raise` is redundant but safe. Propagation is correct.

**Verdict**: No issue.

---

## 6. HIGH Priority Issues

### 6.1 Multi-PC routing: `get_pc_client_manager` ignores device's `pc_client_id`

**Location**: `get_vm_status` (L462), `get_vnc_status` (L521), `is_vm_running` (L451)

**Problem**: These endpoints call `get_pc_client_manager(user_id=user_id)` without `pc_client_id`. That returns the first connected device. If the user has multiple PCs and the target device is on a different PC, the request is sent to the wrong PC.

**Example**:
- Device A on PC-1, Device B on PC-2; both PCs online.
- User asks for status of agent bound to Device A.
- `_ensure_device_available_for_vm` passes (Device A's pc_client PC-1 is online).
- `get_pc_client_manager(user_id)` returns PC-2 (first in iteration).
- `vm_status(device_A)` is sent to PC-2 → 404 "VM not found".

**Fix**: Use the device's `pc_client_id` when calling `get_pc_client_manager`. Refactor `_ensure_device_available_for_vm` to return `device_row`, or fetch it again:

```python
# Option: have _ensure return device_row
def _ensure_device_available_for_vm(vm_id: str, user_id: str, db) -> dict:
    device_row = db.fetchone("SELECT id, user_id, pc_client_id FROM devices WHERE id = ?", (vm_id,))
    if device_row is None:
        raise HTTPException(status_code=400, detail="Device not found for this agent")
    ...
    return device_row

# In get_vm_status:
device_row = _ensure_device_available_for_vm(vm_id, user_id, db)
pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=device_row.get("pc_client_id"))
```

**Same pattern** applies to `start_vm` and `stop_vm` when `request.pc_client_id` is None — they should fall back to `device_row["pc_client_id"]` for correct routing.

---

## 7. MEDIUM Priority Issues

### 7.1 `get_vm_status` / `get_vnc_status` / `is_vm_running` — missing `pc_client_id` fallback

Same root cause as 6.1. These endpoints do not accept `pc_client_id` in the request, so they must use the device's `pc_client_id` from the DB. Currently they use the first connected PC.

### 7.2 `stop_all` — agents without device binding

**Location**: L331

```python
vm_ids_to_stop = {_resolve_vm_id_for_agent(aid, db) for aid in user_agent_ids}
```

For agents without binding, `vm_id = agent_id`. `vm_shutdown(agent_id)` is then sent to vmcontrol. No VM with that ID exists → vmcontrol returns error → `results[vm_id] = {"error": str(e)}`. Behavior is acceptable but generates noisy errors for chat-only agents.

**Optional improvement**: Filter out agents without device binding before calling `vm_shutdown`:

```python
vm_ids_to_stop = set()
for aid in user_agent_ids:
    vm_id = _resolve_vm_id_for_agent(aid, db)
    if db.fetchone("SELECT 1 FROM devices WHERE id = ?", (vm_id,)):
        vm_ids_to_stop.add(vm_id)
```

---

## 8. LOW Priority Issues

### 8.1 Error message for chat-only agents

**Location**: L327

**Current**: `"Device not found for this agent"`

**Suggestion**: Differentiate cases:
- No binding: `"Agent has no device binding"` or `"Agent is not configured for VM"`
- Binding but device missing: `"Device not found for this agent"`

### 8.2 `deploy-vmuse` / `vmuse-health` — no device check

These use `_get_device_ports(agent)` which falls back to defaults (20000, 18000) when the agent has no device. Deploy may fail or target the wrong VM. Low impact; these are manual/debug endpoints.

---

## Summary Table

| Priority | Issue | File:Line | Fix |
|----------|-------|-----------|-----|
| HIGH | Multi-PC routing: status/VNC/is_running use first PC instead of device's pc_client_id | vm.py:462, 521, 451 | Return device_row from _ensure; pass pc_client_id to get_pc_client_manager |
| HIGH | start/stop: when request.pc_client_id is None, should use device's pc_client_id | vm.py:362, 405 | Fallback to device_row["pc_client_id"] when request.pc_client_id is None |
| MEDIUM | stop_all: noisy errors for chat-only agents | vm.py:331 | Filter out agents without device before vm_shutdown |
| LOW | Clearer error for chat-only vs missing device | vm.py:327 | Differentiate error messages |
| LOW | deploy-vmuse/vmuse-health: no device validation | vm.py:558, 641 | Optional: add ensure for consistency |
