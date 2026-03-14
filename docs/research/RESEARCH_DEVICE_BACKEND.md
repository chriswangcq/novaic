# Device Management Backend Research

**Date:** 2025-03-12  
**Scope:** Gateway devices API, DeviceRepository, PC Client, vmcontrol device routes, frontend expectations

---

## 1. Trace: Architecture Overview

### 1.1 Two Distinct "Device" Concepts

| Concept | Table | Purpose |
|---------|-------|---------|
| **Logical devices** (VM/AVD) | `devices` | Agent-managed Linux VMs and Android emulators; config + lifecycle |
| **Physical PC clients** | `pc_clients` | Machines running VmControl; WebSocket registry for CloudBridge |

### 1.2 Gateway Devices API (`/api/devices`)

**File:** `novaic-gateway/gateway/api/devices.py`

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/devices` | GET | List all devices for current user (`list_by_user`) |
| `/api/devices/linux` | POST | Create Linux device (user-owned) |
| `/api/devices/android` | POST | Create Android device (user-owned) |
| `/api/devices/{device_id}` | GET | Get device |
| `/api/devices/{device_id}` | PATCH | Update device |
| `/api/devices/{device_id}` | DELETE | Delete device + files |
| `/api/devices/{device_id}/subjects` | GET | List execution subjects (main, vm_user, default) |
| `/api/devices/{device_id}/tool-capabilities` | GET | Get tool capabilities |
| `/api/devices/{device_id}/setup` | POST | Setup device (Linux: disk+cloud-init; Android: AVD) |
| `/api/devices/{device_id}/start` | POST | Start device |
| `/api/devices/{device_id}/stop` | POST | Stop device |
| `/api/devices/{device_id}/status` | GET | Get runtime status |
| `/api/devices/{device_id}/vmuse/sync` | POST | Hot-sync VMUSE into running Linux VM |

### 1.3 DeviceRepository

**File:** `novaic-gateway/gateway/db/repositories/device.py`

- **Storage:** SQLite `devices` table
- **Methods:** `create`, `get`, `list_by_user`, `list_by_type`, `update`, `update_status`, `delete`
- **No `list_by_agent`** — agents load devices via `AgentConfigManager._load_devices_for_agent`, which calls `device_repo.list_by_agent(agent_id)` — **this method does not exist** (see Gaps).

### 1.4 Agent–Device Binding

**File:** `novaic-gateway/gateway/db/repositories/agent_device_binding.py`

- **Table:** `agent_device_bindings`
- **Schema:** `agent_id`, `device_id`, `subject_type`, `subject_id`, `mounted_tools`
- **Relationship:** One agent → one device subject (main, vm_user, or default)
- **API:** `/api/agents/{id}/binding` (GET/PUT/DELETE) in `gateway/api/agents.py`

### 1.5 PC Client (DeviceRegistry)

**File:** `novaic-gateway/gateway/api/internal/pc_client.py`

- **WebSocket:** `/internal/pc/ws` — Tauri App connects with `x-device-id`, `x-user-id`
- **DeviceRegistry:** In-memory map of `device_id` → `DeviceState` (ws, vm_ids, online, etc.)
- **PcClientRepository:** Persists to `pc_clients` table (device_id, user_id, name, online, first_seen, last_seen)
- **Compatibility:** `get_pc_client_manager(user_id)` returns adapter for first connected device of user (or any if user_id=None)

### 1.6 my-devices (P2P)

**File:** `novaic-gateway/gateway/api/p2p.py`

- **Endpoint:** `GET /api/p2p/my-devices`
- **Source:** `_p2p_registry` (in-memory P2P entries) + `DeviceRegistry` (app_instance_id, machine_label)
- **Returns:** `{ devices: [...], by_app_instance: [...] }` — physical PCs with P2P registration
- **Used by:** Mobile VNC/Scrcpy proxy URL resolution when no local VmControl

### 1.7 vmcontrol Device-Related Routes

**Files:** `novaic-app/src-tauri/vmcontrol/src/api/routes/`

| Route | Purpose |
|-------|---------|
| `/api/vms` | List/register VMs (local QMP socket discovery) |
| `/api/vms/:id` | Get VM info |
| `/api/vms/:id/setup` | VM disk + cloud-init |
| `/api/vms/:id/start`, `/stop`, `/shutdown` | VM lifecycle |
| `/api/vms/:id/users` | VM users (TigerVNC sub-users) |
| `/api/vms/:id/vnc` | VNC WebSocket |
| `/api/android/devices` | List Android devices |
| `/api/android/avds` | List AVDs |
| `/api/android/emulator/start`, `/stop` | Emulator control |

Gateway forwards device operations to vmcontrol via **PC Client WebSocket** (CloudBridge), not direct HTTP.

---

## 2. How Devices Are Stored

### 2.1 `devices` Table Schema

```sql
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    type TEXT CHECK(type IN ('linux', 'android')),
    name TEXT, created_at TEXT, status TEXT,
    memory INTEGER, cpus INTEGER, data_path TEXT, ports TEXT,
    -- Linux: backend, os_type, os_version, image_path, cloud_init_complete
    -- Android: avd_name, device_serial, managed, system_image
);
```

- **Ownership:** `user_id` (direct owner; v49 migration)
- **Status:** created | setup | ready | running | stopped | error

### 2.2 `pc_clients` Table

```sql
CREATE TABLE pc_clients (
    device_id TEXT PRIMARY KEY,  -- VmControl UUID
    user_id TEXT NOT NULL,
    name TEXT, online INTEGER,
    first_seen TEXT, last_seen TEXT
);
```

- **device_id:** Same as DeviceRegistry key (VmControl Ed25519 or legacy UUID)
- **online:** Whether Agent control is enabled

### 2.3 `agent_device_bindings` Table

```sql
-- agent_id -> device_id, subject_type, subject_id, mounted_tools
```

### 2.4 `vm_users` Table

```sql
-- device_id, username, display_num (for Linux VM sub-users)
```

---

## 3. How Binding Works

1. **Create device:** `POST /api/devices/linux` or `/api/devices/android` → `DeviceRepository.create` → `devices` row
2. **Bind agent:** `PUT /api/agents/{id}/binding` → `AgentDeviceBindingRepository.upsert` → `agent_device_bindings` row
3. **Runtime resolution:** `resolve_agent_runtime_context(db, agent_id)` → binding → device → subject → `build_runtime_context`

Subject types:
- **main:** Linux main desktop (display :10)
- **vm_user:** Linux sub-user (display :11, :12, …)
- **default:** Android default session

---

## 4. How my-devices Is Built

1. **P2P heartbeat:** PC sends `device_id`, `ext_addr`, `local_port` → `_p2p_registry`
2. **CloudBridge WS:** PC connects with `x-device-id` → `DeviceRegistry` + `PcClientRepository.upsert`
3. **my-devices request:** `GET /api/p2p/my-devices`
   - Iterate `_p2p_registry` for `user_id`
   - Enrich with `DeviceRegistry.get_device()` (app_instance_id, machine_label)
   - Group by `app_instance_id` → `by_app_instance`
   - Mark `is_local` if `current_device_id` matches

**Important:** my-devices returns **physical PC devices** (P2P/VmControl hosts), not logical `devices` (VM/AVD configs).

---

## 5. Gaps: Frontend vs Backend

### 5.1 Missing Route: `/api/agents/{agentId}/devices`

**Frontend:** `api.devices.list(agentId)` → `GET /api/agents/${agentId}/devices`  
**Backend:** No such route. Agents API does not expose `GET /api/agents/{id}/devices`.

**Impact:** Frontend call will 404.

**Workaround:** Use `api.devices.listForUser()` (GET /api/devices) and filter client-side, or add the route.

### 5.2 Missing Method: `DeviceRepository.list_by_agent`

**Caller:** `AgentConfigManager._load_devices_for_agent(agent_id)`  
**Expected:** `device_repo.list_by_agent(agent_id)`  
**Reality:** `DeviceRepository` has no `list_by_agent`.

**Impact:** `_load_devices_for_agent` will raise `AttributeError` when loading agent config.

**Fix options:**
- Add `list_by_agent(agent_id)` joining `agent_device_bindings` + `devices`
- Or change to `list_by_user(user_id)` where user_id comes from agent

### 5.3 Two Different "device_id" Semantics

| Context | device_id meaning |
|---------|-------------------|
| `devices` table | Logical device UUID (VM/AVD config) |
| `pc_clients` / my-devices | Physical PC ID (VmControl Ed25519 or legacy UUID) |

VNC proxy and P2P use **physical** device_id; Device API uses **logical** device_id. Frontend must not conflate them.

### 5.4 get_pc_client_manager Multi-Device

`get_pc_client_manager(user_id)` returns the **first** connected device. With multiple PCs, device operations (start VM, Android, etc.) always target that first device. No way to target a specific PC from the Device API.

### 5.5 VM Users API Path

**Frontend:** `api.vmUsers.list(deviceId)` → `GET /api/devices/{deviceId}/vm-users`  
**Backend:** Implemented in `gateway/api/vm_users.py` ✓

---

## 6. Key Files

### novaic-gateway

| File | Role |
|------|------|
| `gateway/api/devices.py` | Unified Device CRUD + lifecycle |
| `gateway/api/vm_users.py` | VM sub-users (TigerVNC) |
| `gateway/api/agents.py` | Agent binding, agent config |
| `gateway/api/vm.py` | VM/Android proxy (agent-based legacy) |
| `gateway/api/vmcontrol.py` | VmControl REST proxy (local) |
| `gateway/api/p2p.py` | P2P my-devices, heartbeat, relay |
| `gateway/api/internal/pc_client.py` | PC Client WebSocket, DeviceRegistry |
| `gateway/db/repositories/device.py` | DeviceRepository |
| `gateway/db/repositories/agent_device_binding.py` | AgentDeviceBindingRepository |
| `gateway/db/repositories/pc_client.py` | PcClientRepository |
| `gateway/db/schema.py` | devices, pc_clients, vm_users, agent_device_bindings |
| `gateway/config/devices.py` | Device, LinuxDevice, AndroidDevice models |
| `gateway/agent_binding.py` | Subjects, runtime context, mounted tools |
| `gateway/config/agents_db.py` | AgentConfigManager, _load_devices_for_agent |

### novaic-app/src-tauri/vmcontrol

| File | Role |
|------|------|
| `src/api/routes/mod.rs` | Route registration |
| `src/api/routes/vm.rs` | VM CRUD, start/stop, users |
| `src/api/routes/android.rs` | Android devices, AVDs, emulator |
| `src/api/routes/setup.rs` | VM setup (disk, cloud-init) |
| `src/cloud_bridge.rs` | CloudBridge client (Gateway WS) |

### novaic-app (Frontend)

| File | Role |
|------|------|
| `src/services/api.ts` | api.devices.*, api.vmUsers.* |
| `src/services/vm.ts` | vmService, getVncUrl (uses my-devices) |
| `src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url, my-devices fallback |
| `src-tauri/src/commands/vnc_bridge.rs` | VncBridgeTransport, my-devices |

---

## 7. Recommendations

1. **Implement `DeviceRepository.list_by_agent`**  
   Join `agent_device_bindings` with `devices` on `device_id` where `agent_id = ?`, or return devices owned by the agent’s user that have a binding for that agent.

2. **Add `GET /api/agents/{agentId}/devices`**  
   Return devices available for the agent (e.g. user’s devices or devices with bindings).

3. **Clarify device_id in docs**  
   Distinguish logical device_id (Device API) from physical device_id (my-devices, VNC proxy).

4. **Multi-PC targeting**  
   Consider a `pc_device_id` or similar parameter for Device operations when the user has multiple PCs.
