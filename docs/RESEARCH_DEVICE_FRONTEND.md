# Device Management Frontend Research

**Workspace:** novaic-app  
**Date:** 2025-03-12

## 1. Data Flow

### 1.1 API Layer (`api.devices.*`)

| API | Path | Used By |
|-----|------|---------|
| `listForUser()` | `GET /api/devices` | DeviceManagerPage, AgentDrawer, DeviceManagerModal |
| `list(agentId)` | `GET /api/agents/{id}/devices` | (Agent list includes devices) |
| `get(deviceId)` | `GET /api/devices/{id}` | useAgentBinding, DeviceFloatingPanel |
| `start(deviceId)` | `POST /api/devices/{id}/start` | DeviceManagerPage, DeviceManagerModal, DeviceSidebar, DeviceFloatingPanel, useDeviceVNCConnection |
| `stop(deviceId)` | `POST /api/devices/{id}/stop` | Same as start |
| `status(deviceId)` | `GET /api/devices/{id}/status` | DeviceSidebar, DeviceFloatingPanel, useDeviceVNCConnection |
| `delete(deviceId)` | `DELETE /api/devices/{id}` | DeviceManagerModal, DeviceSidebar |
| `createLinuxForUser()` | `POST /api/devices/linux` | AddLinuxVMModal, AddLinuxVMUserModal |
| `createAndroidForUser()` | `POST /api/devices/android` | AddAndroidModal |

### 1.2 `getAgentBinding` / `useAgentBinding`

- **Location:** `api.getAgentBinding(agentId)` → `GET /api/agents/{id}/binding`
- **Hook:** `useAgentBinding(agentId, initialBinding?)` in `src/hooks/useAgentBinding.ts`
- **Flow:** Uses `initialBinding` from agent list when available, else calls `getAgentBinding`. Then fetches device via `api.devices.get(binding.device_id)`.
- **Used by:** `DeviceFloatingPanel` only.

### 1.3 Component Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DeviceManagerPage                                                           │
│  ├─ api.devices.listForUser() → devices, patchState(deviceManagerDevices)     │
│  ├─ selectedDeviceId from store → sync selectedDevice                        │
│  └─ Renders: DeviceVNCView | VmUserVNCView (no DeviceListPanel)              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  AgentDrawer (Devices tab)                                                   │
│  ├─ api.devices.listForUser() → devices, patchState(deviceManagerDevices)     │
│  ├─ selectedDeviceId from store → openDevice(deviceId)                       │
│  ├─ api.vmUsers.list(deviceId) for Linux VM users                            │
│  └─ Renders: device list (inline), no DeviceListPanel                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  DeviceSidebar (NOT RENDERED IN APP)                                         │
│  ├─ currentAgent.devices from useAgent (agent.devices)                       │
│  ├─ api.devices.status(deviceId) per device, 5s poll                         │
│  └─ api.devices.start/stop/delete                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  DeviceFloatingPanel (NOT RENDERED IN APP)                                    │
│  ├─ useAgentBinding(currentAgentId, currentAgent?.binding)                    │
│  │   → getAgentBinding + api.devices.get(binding.device_id)                   │
│  ├─ api.devices.status(deviceId), 5s poll                                    │
│  └─ api.devices.start/stop                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  DeviceManagerModal                                                          │
│  ├─ api.devices.listForUser() when open                                       │
│  └─ api.devices.start/stop/delete                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  useDeviceVNCConnection (DeviceVNCView)                                       │
│  └─ api.devices.start/stop/status                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. How Devices Are Loaded and Displayed

### 2.1 Device List Sources

| Source | Scope | API | Used By |
|-------|-------|-----|---------|
| User devices | All user devices | `api.devices.listForUser()` | DeviceManagerPage, AgentDrawer, DeviceManagerModal |
| Agent devices | Per-agent | `agent.devices` (from agents list) | DeviceSidebar |
| Agent binding | Single device per agent | `getAgentBinding` + `devices.get` | DeviceFloatingPanel |

### 2.2 Selection Flow

1. **AgentDrawer** → Devices tab shows devices from `api.devices.listForUser()`.
2. User clicks device → `setSelectedDeviceId(id)` in store.
3. **DeviceManagerPage** reads `selectedDeviceId` from store, finds device in `devices` state.
4. Renders `DeviceVNCView` (Linux) or `VmUserVNCView` (sub-user).

### 2.3 Device Status

- **DeviceManagerPage / AgentDrawer:** Uses `device.status` from list response (running, ready, stopped, etc.).
- **DeviceSidebar:** Polls `api.devices.status(id)` every 5s, maps to `online`/`offline`/`connecting`.
- **DeviceFloatingPanel:** Polls `api.devices.status(id)` every 5s.
- **useDeviceVNCConnection:** Calls `api.devices.status(id)` on init and during polling (3s interval).

---

## 3. API Usage by Component

| Component | listForUser | list | get | start | stop | status | delete | getAgentBinding |
|-----------|-------------|------|-----|-------|------|--------|--------|----------------|
| DeviceManagerPage | ✓ | | | | | | | |
| AgentDrawer | ✓ | | | | | | | |
| DeviceManagerModal | ✓ | | | ✓ | ✓ | | ✓ | |
| DeviceSidebar | | | | ✓ | ✓ | ✓ | ✓ | |
| DeviceFloatingPanel | | | ✓ | ✓ | ✓ | ✓ | | ✓ (via hook) |
| useDeviceVNCConnection | | | | ✓ | ✓ | ✓ | | |

---

## 4. Redundancy, Inconsistency, & Complexity

### 4.1 Redundancy

1. **Duplicate device loading:** DeviceManagerPage and AgentDrawer both call `api.devices.listForUser()` and patch `deviceManagerDevices`. DeviceManagerPage also loads on mount and syncs from store on error.
2. **Multiple status polling:** DeviceSidebar, DeviceFloatingPanel, and useDeviceVNCConnection each poll status independently (5s, 5s, 3s).
3. **Device list UI:** AgentDrawer has inline device list; DeviceManagerPage defines `DeviceListPanel` but never renders it.

### 4.2 Inconsistency

1. **Device scope:** DeviceSidebar uses `agent.devices` (agent-scoped); DeviceManagerPage/AgentDrawer use `listForUser` (user-scoped). Same device can appear in different contexts with different semantics.
2. **Status representation:** Device status is mapped differently (e.g. `running` vs `online`, `stopped` vs `offline`).
3. **Add-modals:** AddLinuxVMModal vs AddLinuxVMUserModal vs AddLinuxVMUserModal naming and usage vary across components.

### 4.3 Complexity

1. **DeviceManagerPage:** Loads devices, syncs with store, handles fallback from AgentDrawer, manages selectedDevice/selectedVmUser, but does not render a list.
2. **DeviceListPanel:** Exported from DeviceManagerPage but unused; appears to be dead code or from an older layout.
3. **Orphaned components:** DeviceSidebar and DeviceFloatingPanel are implemented but not imported or rendered anywhere. App.tsx comments refer to DeviceSidebar, but it is not in the component tree.

---

## 5. Key Files and Responsibilities

| File | Responsibility |
|------|----------------|
| `src/services/api.ts` | `api.devices.*`, `api.getAgentBinding`, `api.setAgentBinding`, `api.clearAgentBinding` |
| `src/hooks/useAgentBinding.ts` | Fetch agent binding + device; used by DeviceFloatingPanel |
| `src/components/hooks/useAgent.ts` | Bridge to store; `agents`, `currentAgent`, `loadAgents` |
| `src/components/VM/DeviceManagerPage.tsx` | Main device page; loads devices, shows VNC/Scrcpy for selected device; defines but does not use DeviceListPanel |
| `src/components/Layout/AgentDrawer.tsx` | Drawer with Agents + Devices tabs; loads devices via listForUser, shows device list, sets selectedDeviceId |
| `src/components/Layout/DeviceSidebar.tsx` | Right sidebar with agent devices; **not rendered** |
| `src/components/Layout/DeviceFloatingPanel.tsx` | Floating device preview/overlay; **not rendered** |
| `src/components/VM/DeviceManagerModal.tsx` | Modal device list with start/stop/delete |
| `src/components/Visual/DeviceVNCView.tsx` | Linux VNC + Android Scrcpy view for a device |
| `src/components/VM/VmUserVNCView.tsx` | Sub-user VNC view; used in DeviceManagerPage and DeviceFloatingPanel |
| `src/components/Visual/useDeviceVNCConnection.ts` | VNC lifecycle (start/stop/status) for DeviceVNCView |
| `src/application/store.ts` | `deviceManagerDevices`, `selectedDeviceId`, `selectedVmUser`, add-modals state |

---

## 6. Summary

- **Active device UI:** AgentDrawer (Devices tab) + DeviceManagerPage (VNC/Scrcpy view).
- **Device data:** Primarily from `api.devices.listForUser()`; shared via `deviceManagerDevices` in store.
- **Orphaned:** DeviceSidebar, DeviceFloatingPanel, DeviceListPanel (exported but unused).
- **Main issues:** Duplicate loading, multiple status polling, inconsistent device scope (user vs agent), and unused components increasing maintenance cost.
