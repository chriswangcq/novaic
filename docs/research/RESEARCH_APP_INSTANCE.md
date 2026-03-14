# AppInstance and my-devices Flow Research

This document traces the AppInstance abstraction, `app_instance_id`, Cloud Bridge, Relay connection, and my-devices API flow across the codebase.

---

## 1. Trace: get_app_instance → app_instance_id → Cloud Bridge → Relay → my-devices

### 1.1 AppInstance Creation and Identity

| Step | Location | Description |
|------|----------|-------------|
| **Creation** | `novaic-app/src-tauri/src/setup.rs:53-60` | `AppInstance::new_desktop()` or `AppInstance::new_mobile()` created at startup |
| **Identity** | `novaic-app/src-tauri/src/state/mod.rs:44-58` | `app_instance_id` = UUID v4, `machine_label` = `device_info::machine_label()` |
| **Ready** | `novaic-app/src-tauri/src/setup.rs:126-135` | `set_ready()` called when user logs in (after `login_notify`) |

### 1.2 Flow: Tauri → Cloud Bridge → Gateway

```
setup.rs (AppInstance created)
    ↓
lib.rs:249-251 (read app_instance_id, machine_label from AppInstanceState)
    ↓
lib.rs:273-280 (CloudBridgeConfig with app_instance_id, machine_label)
    ↓
VmControl::start() → Cloud Bridge WebSocket
    ↓
cloud_bridge.rs:175-209 (connect to ws://.../internal/pc/ws)
    Headers: x-device-id, x-app-instance-id, x-machine-label, Authorization
    ↓
Gateway pc_client.py:551-576 (WebSocket accept, registry.connect)
    DeviceRegistry stores: device_id, user_id, app_instance_id, machine_label
```

### 1.3 Flow: P2P Heartbeat (separate from Cloud Bridge)

```
VmControl P2P server starts (p2p rendezvous)
    ↓
rendezvous.rs:run_heartbeat_loop() → POST /api/p2p/heartbeat
    Body: { device_id, ext_addr, local_port, cert_der_b64 }
    ↓
p2p.py:150-189 (_p2p_registry stores P2PEntry)
    Note: Heartbeat does NOT carry app_instance_id; DeviceRegistry has it from WebSocket
```

### 1.4 Flow: my-devices API

```
Frontend / Rust: gateway_get("/api/p2p/my-devices") or gateway_get_impl(..., "/api/p2p/my-devices")
    Optional query: ?current_device_id=xxx (for is_local marking)
    ↓
p2p.py:326-366 (list_my_p2p_devices)
    - Iterate _p2p_registry (P2P entries from heartbeat)
    - For each: get DeviceRegistry.get_device(device_id) → enrich app_instance_id, machine_label
    - Build devices[] + by_app_instance{}
    - If current_device_id matches entry.device_id → item["is_local"] = True
```

### 1.5 Flow: Relay Connection (Phase 3)

```
Mobile: P2P punch fails → relay_request(target_device_id)
    ↓
p2p.py:231-281 (relay-request)
    - get_device_registry().get_device(target_device_id) → DeviceState
    - send_push_to_device(device, "connect_relay", {relay_url, session_id})
    ↓
Cloud Bridge receives IncomingMessage::ConnectRelay
    ↓
cloud_bridge.rs:279-323 (spawn connect_via_relay)
    p2p::relay::connect_via_relay(relay_url, jwt, session_id, RelayRole::Pc { device_id })
    ↓
Relay service validates session, PC connects, tunnel established
```

---

## 2. How app_instance is Used

### 2.1 Gateway (novaic-gateway)

| Component | Usage |
|-----------|-------|
| **pc_client.py** | `DeviceState.app_instance_id` from WebSocket header `x-app-instance-id`; stored when Cloud Bridge connects |
| **p2p.py** | `_build_device_item()` enriches each device with `app_instance_id`, `machine_label` from DeviceRegistry; `by_app_instance` groups devices by `app_instance_id` |

### 2.2 PC Client (DeviceRegistry)

| File | Usage |
|------|-------|
| **pc_client.py:41** | `DeviceState.app_instance_id: str = ""` |
| **pc_client.py:68-76** | `registry.connect(..., app_instance_id=..., machine_label=...)` |
| **pc_client.py:95-108** | On reconnect: update `device.app_instance_id`, `device.machine_label` from new headers |
| **pc_client.py:551-576** | WebSocket handler reads `x-app-instance-id`, `x-machine-label` from headers |

### 2.3 by_app_instance Grouping

```python
# p2p.py:343-364
by_app_instance: Dict[str, dict] = {}
for item in result:
    app_id = item.get("app_instance_id") or ""
    machine_label = item.get("machine_label") or ""
    if app_id not in by_app_instance:
        by_app_instance[app_id] = {
            "app_instance_id": app_id,
            "machine_label": machine_label,
            "devices": [],
        }
    by_app_instance[app_id]["devices"].append(item)
    if item.get("is_local"):
        by_app_instance[app_id]["is_local"] = True

return {"devices": result, "by_app_instance": list(by_app_instance.values())}
```

- **devices**: Flat list of all user devices (from _p2p_registry).
- **by_app_instance**: Grouped by `app_instance_id`; each group has `devices[]`, `machine_label`, `is_local` (if any device in group is local).

---

## 3. current_device_id and is_local Logic

### 3.1 current_device_id

| Location | Purpose |
|----------|---------|
| **p2p.py:329** | Query param: `current_device_id: str = ""` |
| **p2p.py:336** | `current_device_id = current_device_id.strip()` |
| **p2p.py:315** | `if current_device_id and entry.device_id == current_device_id: item["is_local"] = True` |
| **p2p.py:357-358** | If any device has `is_local`, the app_instance group gets `is_local = True` |

**Source of current_device_id**: `get_local_device_id` Tauri command returns `local_vmcontrol.device_id` (desktop only; mobile returns `None`).

### 3.2 is_local Logic

| Location | Logic |
|----------|-------|
| **p2p.py:315-316** | `item["is_local"] = True` when `entry.device_id == current_device_id` |
| **p2p.py:357-358** | `by_app_instance[app_id]["is_local"] = True` when any device in group has `is_local` |

### 3.3 Where current_device_id is Used

| Caller | Passes current_device_id? |
|--------|---------------------------|
| **vnc_urls.rs** | No — calls `gateway_get_impl(..., "/api/p2p/my-devices")` without query params |
| **vnc_bridge.rs** | No — same as above |
| **Frontend gateway_get** | Could pass `path: "/api/p2p/my-devices?current_device_id=" + localId` — **not currently implemented** |

**Gap**: The frontend does not appear to call my-devices directly for UI. It is only used internally by `get_vnc_proxy_url`, `get_scrcpy_proxy_url`, `vnc_bridge_connect` when resolving `device_id` on mobile. Those callers do not pass `current_device_id`, so `is_local` is never set in practice unless the frontend explicitly fetches my-devices with that param.

---

## 4. Key Files Summary

| File | Purpose |
|------|---------|
| **novaic-app/src-tauri/src/commands/app_instance.rs** | `get_app_instance`, `get_local_device_id` Tauri commands |
| **novaic-app/src-tauri/src/state/mod.rs** | `AppInstance` struct, `AppInstanceState` |
| **novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs** | Cloud Bridge WebSocket; sends `x-app-instance-id`, `x-machine-label`; handles `ConnectRelay` |
| **novaic-app/src-tauri/src/setup.rs** | Creates AppInstance, spawns ready task |
| **novaic-app/src-tauri/src/lib.rs** | Reads app_instance_id for CloudBridgeConfig, registers commands |
| **novaic-gateway/gateway/api/internal/pc_client.py** | DeviceRegistry, DeviceState, WebSocket `/internal/pc/ws` handler |
| **novaic-gateway/gateway/api/p2p.py** | my-devices, heartbeat, locate, relay-request; `_build_device_item`, `by_app_instance` |

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Tauri App (Desktop)                                                          │
│  AppInstance (app_instance_id, machine_label)                                 │
│  VmControl (device_id = Ed25519 hex)                                           │
└─────────────────────────────────────────────────────────────────────────────┘
         │                                    │
         │ Cloud Bridge WS                    │ P2P Heartbeat
         │ x-device-id, x-app-instance-id      │ device_id, ext_addr
         ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Gateway                                                                      │
│  DeviceRegistry (device_id → DeviceState: app_instance_id, machine_label)     │
│  _p2p_registry (device_id → P2PEntry: ext_addr, cert, last_seen)              │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ my-devices: merge _p2p_registry + DeviceRegistry by device_id
         │ Optional: current_device_id → is_local on matching device/group
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Response: { devices: [...], by_app_instance: [...] }                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Identifiers Summary

| ID | Format | Source | Used For |
|----|--------|--------|----------|
| **app_instance_id** | UUID v4 | Tauri AppInstance (new at each app launch) | Grouping devices in my-devices; machine identity |
| **device_id** | Ed25519 hex (64 chars) | VmControl (persisted in data_dir) | P2P locate, relay, WebSocket routing |
| **machine_label** | String (e.g. "MacBookPro18,1 (hostname)") | `device_info::machine_label()` | Display in UI |

---

## 7. Recommendations

1. **Frontend my-devices + current_device_id**: If the UI needs to show "this device" in a multi-PC list, call `gateway_get("/api/p2p/my-devices?current_device_id=" + (await invoke('get_local_device_id')) ?? "")` so `is_local` is populated.
2. **AppInstance vs device_id**: `app_instance_id` changes per app launch; `device_id` is persistent. For "same machine" detection, `device_id` is the canonical key; `app_instance_id` is for grouping/display.
3. **Mobile**: `get_local_device_id` returns `None`; `current_device_id` would be empty, so no device is ever marked `is_local` on mobile (correct).
