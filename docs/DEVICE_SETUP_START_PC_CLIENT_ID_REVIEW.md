# AddLinuxVMUserModal & AddAndroidModal — pc_client_id Review

## Summary

Both modals create **new** devices and call `api.devices.setup` and `api.devices.start` **without** passing `pcClientId`. The backend falls back to the **first connected PC** for the user, which is incorrect for "create on this PC" when the user has multiple PCs.

---

## 1. Do they pass pcClientId?

**No.** Neither modal passes `pcClientId`.

| File | Line | Call | pcClientId |
|------|------|------|------------|
| `AddLinuxVMUserModal.tsx` | 90 | `api.devices.setup(device.id, { source_image: imagePath, use_cn_mirrors: useCnMirrors })` | ❌ Not passed |
| `AddLinuxVMUserModal.tsx` | 93 | `api.devices.start(device.id)` | ❌ Not passed |
| `AddAndroidModal.tsx` | 234 | `api.devices.setup(device.id)` | ❌ Not passed |
| `AddAndroidModal.tsx` | 240 | `api.devices.start(device.id)` | ❌ Not passed |

---

## 2. Where would pc_client_id come from for NEW devices?

For **new** devices:
- `device.pc_client_id` is `undefined` (device just created, backend does not set it on create)
- Create endpoints (`createLinuxForUser`, `createAndroidForUser`) do **not** accept `pc_client_id`
- The intended source: **current app instance's PC** → resolve via `app_instance_id` + `my-devices` API

**Resolution path:**
1. `useAppStore(s => s.appInstanceId)` — available in frontend (populated by `get_app_instance` Tauri command)
2. Call `GET /api/p2p/my-devices?current_app_instance_id={appInstanceId}`
3. Find device where `app_instance_id === appInstanceId` (or `is_local` in `by_app_instance`)
4. That device's `device_id` (or `pc_client_id`) = current PC's `pc_client_id`

---

## 3. For new device setup, which PC should run setup?

**Correct behavior:** The **current app instance's PC** — i.e. the PC where the user is running the app and clicked "Add Linux VM" / "Add Android".

**Required:** `app_instance_id` + `my-devices` to resolve `pc_client_id` for the current app instance.

---

## 4. If pcClientId not passed, backend uses first connected PC — correct?

**No.** Backend logic:

```python
# _get_pc_manager_for_device(device, user_id, pc_client_id=None)
target = (pc_client_id or "").strip() or getattr(device, "pc_client_id", None) or ""
# → target = "" for new devices

# get_pc_client_manager(user_id, target=None)
# target_id empty → returns devices[0] from get_connected_devices(user_id)
```

**Issue:** When the user has multiple PCs (e.g. desktop + laptop), `devices[0]` is arbitrary (first in registry iteration order). The setup/start may run on the **wrong** PC.

**Severity:** **High** — user may create a VM on a different machine than the one they're using.

---

## 5. appInstanceId in store — can modals access it to resolve pc_client_id?

**Yes.** `useAppStore(s => s.appInstanceId)` is available. The store has:

```typescript
// store.ts:100-101
/** P2-5: 本实例 app_instance_id，供 my-devices 等调用时标注 is_local */
appInstanceId: string | null;
```

**Gap:** The frontend `api` service does **not** expose `my-devices`. The Tauri commands (`vnc_urls.rs`, `vnc_bridge.rs`) call it internally. Modals would need:

1. Either add `api.p2p.getMyDevices(appInstanceId?: string)` 
2. Or use `invoke('gateway_get', { path: `/api/p2p/my-devices?current_app_instance_id=${appInstanceId}` })` directly

---

## 6. Other callers of api.devices.setup/start that need pc_client_id

| Caller | File:Line | Passes pcClientId? | Issue |
|--------|-----------|-------------------|-------|
| **AddLinuxVMUserModal** | `AddLinuxVMUserModal.tsx:90,93` | ❌ | New device — should use current PC |
| **AddAndroidModal** | `AddAndroidModal.tsx:234,240` | ❌ | New device — should use current PC |
| **useDeviceVNCConnection** | `useDeviceVNCConnection.ts:99,124,150` | ✅ | Uses `device?.pc_client_id` — correct for existing devices |
| **DeviceManagerModal** | `DeviceManagerModal.tsx:216,227` | ❌ | `api.devices.start(id)`, `api.devices.stop(id)` — no pcClientId |
| **DeviceVNCView** | via `useDeviceVNCConnection` | ✅ | Uses device's pc_client_id |

**DeviceManagerModal** also uses `api.devices.start(id)` and `api.devices.stop(id)` without `pcClientId`. It has `device` in context — should pass `device.pc_client_id` if available.

---

## Issues with File:Line and Severity

| # | File | Line | Severity | Description |
|---|------|------|----------|-------------|
| 1 | `AddLinuxVMUserModal.tsx` | 90 | **High** | `api.devices.setup(device.id, ...)` — no pcClientId; new device setup may run on wrong PC |
| 2 | `AddLinuxVMUserModal.tsx` | 93 | **High** | `api.devices.start(device.id)` — no pcClientId; VM may start on wrong PC |
| 3 | `AddAndroidModal.tsx` | 234 | **High** | `api.devices.setup(device.id)` — no pcClientId; AVD creation may run on wrong PC |
| 4 | `AddAndroidModal.tsx` | 240 | **High** | `api.devices.start(device.id)` — no pcClientId; emulator may start on wrong PC |
| 5 | `DeviceManagerModal.tsx` | 216 | **Medium** | `api.devices.start(id)` — no pcClientId; has device in context, should pass device.pc_client_id |
| 6 | `DeviceManagerModal.tsx` | 227 | **Medium** | `api.devices.stop(id)` — no pcClientId |
| 7 | `DeviceManagerModal.tsx` | 242 | **Medium** | `api.devices.delete(id)` — no pcClientId (delete also supports it per api.ts:827) |
| 8 | `api.ts` | — | **Low** | No `api.p2p.getMyDevices()` or equivalent for frontend to resolve app_instance_id → pc_client_id |

---

## Recommendations

1. **Add `api.p2p.getMyDevices(appInstanceId?: string)`** — returns `{ devices, by_app_instance }` so modals can resolve current PC's `pc_client_id`

2. **Modals: resolve pc_client_id before setup/start**
   - `useAppStore(s => s.appInstanceId)` 
   - Call `getMyDevices(appInstanceId)` 
   - Find device with matching `app_instance_id` or `is_local` 
   - Use its `device_id` as `pcClientId` for setup/start

3. **DeviceManagerModal** — pass `device.pc_client_id` to start/stop/delete when available

4. **Backend create endpoints** — consider accepting optional `pc_client_id` so new devices are created with the correct host PC from the start (avoids setup/start fallback entirely)
