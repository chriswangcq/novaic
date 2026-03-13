# Device / PC Client Online — R3 Critical Review: AgentDrawer & Types

> Focus: `isAvailable` fallback logic, API contracts, `devicesByFloor` key collision, race conditions, type safety.

**Context (R2 fixes):** Promise.allSettled; console.error; `isAvailable` fallback to `device.available` when `pcClientOnlineMap` missing key.

---

## 1. isAvailable = `pcClientOnlineMap.get(device.pc_client_id) ?? device.available`

**Location:** `AgentDrawer.tsx:542`

```typescript
isAvailable={!!(device.pc_client_id && (pcClientOnlineMap.get(device.pc_client_id) ?? device.available))}
```

### Semantics — Correct ✅

| Case | `pcClientOnlineMap.get(...)` | Result |
|------|------------------------------|--------|
| pcOnline explicitly `false` | `false` | `false ?? device.available` = `false` ✅ |
| Key missing (undefined) | `undefined` | `undefined ?? device.available` = `device.available` ✅ |
| pcOnline `true` | `true` | `true` ✅ |

### When `device.available` is undefined

| Case | Result |
|------|--------|
| `device.available === undefined` | `undefined ?? undefined` = `undefined` → `!!(pc_client_id && undefined)` = `false` ✅ |

**Verdict:** Logic is correct. Device is treated as unavailable when both P2P map and API `available` are undefined.

---

## 2. devices from listForUser — Does API Always Return `available`?

**Location:** `novaic-gateway/gateway/api/devices.py:206–214`, `272–278`

```python
def device_to_response(device: Device, user_id: Optional[str] = None) -> DeviceResponse:
    if user_id:
        data['available'] = _compute_device_available(device, user_id)
    return DeviceResponse(**data)

# list_all_user_devices:
return DeviceListResponse(devices=[device_to_response(d, user_id) for d in devices])
```

**Current Gateway:** Always passes `user_id` (from `get_current_user`), so `available` is always set.

**Old Gateway:** If an older deployment did not compute `available`, devices could omit it. Frontend `?? device.available` would see `undefined` and treat as unavailable.

| Issue | Severity | Fix |
|-------|----------|-----|
| Old Gateway may omit `available` | **LOW** | Frontend already handles `undefined` safely. Document API contract. |

---

## 3. devicesByFloor — Floor with Empty `app_instance_id` / Key Collision?

**Location:** `AgentDrawer.tsx:136–163`

```typescript
result.push({
  key: floor.app_instance_id || 'unknown',
  label: floor.machine_label || floor.app_instance_id?.slice(0, 8) || '未知',
  ...
});
```

**Backend:** `p2p.py` groups by `app_id = item.get("app_instance_id") or ""`. All PCs without `app_instance_id` merge into one floor with `app_instance_id: ""`. At most one floor has empty `app_instance_id`.

**Frontend:** `key = floor.app_instance_id || 'unknown'` → empty string becomes `'unknown'`.

| Scenario | Result |
|----------|--------|
| One floor with `app_instance_id: ""` | Single floor, `key='unknown'` ✅ |
| Literal `app_instance_id: "unknown"` | Would collide with fallback `'unknown'` |

| Issue | Severity | Fix |
|-------|----------|-----|
| Literal `app_instance_id="unknown"` would collide | **MEDIUM** | Use unique key, e.g. `key: floor.app_instance_id || \`__empty_${index}\`` or `\`floor-${index}\`` |

---

## 4. loadDevices — appInstanceId null → getMyDevices Not Called

**Location:** `AgentDrawer.tsx:81–109`

When `appInstanceId` is null/undefined:

```typescript
appInstanceId ? api.p2p.getMyDevices(appInstanceId) : Promise.resolve({ devices: [], by_app_instance: [] })
```

- `getMyDevices` is not called.
- `by_app_instance = []` → `pcClientOnlineMap` is empty.
- `isAvailable` falls back to `device.available`.

**listForUser when no P2P:** `listForUser` is always called. Current Gateway computes `available` via `_compute_device_available` (DeviceRegistry + Cloud Bridge). It does **not** depend on P2P. So `device.available` is set even when P2P is not used.

| Issue | Severity | Fix |
|-------|----------|-----|
| No P2P path uses `device.available` | **OK** | Correct. |
| listForUser returns `available` without P2P | **OK** | Yes; `_compute_device_available` uses DeviceRegistry only. |

---

## 5. Device Type — `available?: boolean` Optional

**Location:** `novaic-app/src/types/index.ts:31`

```typescript
available?: boolean;
```

**Usage:** `AgentDrawer.tsx:542` passes `!!(...)` which coerces to `boolean`. `DeviceListItem` always receives a `boolean`.

| Issue | Severity | Fix |
|-------|----------|-----|
| Optional `available` | **OK** | Callers handle `undefined`; no unsafe assumptions. |
| Assumptions that `available` exists | **NONE** | Only use is in `??` fallback, which is correct. |

---

## 6. Race — devices load vs byAppInstance load

**Location:** `AgentDrawer.tsx:84–100`

```typescript
const [devicesSettled, myDevicesSettled] = await Promise.allSettled([...]);
setDevices(next);
setByAppInstance(Array.isArray(floors) ? floors : []);
```

**Same batch:** Both results applied in one block. No intermediate state within a single `loadDevices` call.

**Different polls:** On a subsequent poll, `getMyDevices` can fail while `listForUser` succeeds. Then `myDevicesRes = null` → `floors = undefined` → `setByAppInstance([])`. Result: `pcClientOnlineMap` empty, `isAvailable` falls back to `device.available`. No incorrect state.

**Flicker risk:** When `byAppInstance` goes from populated → empty (transient reject), `isAvailable` switches from P2P-based to `device.available`. If API `available` differs from P2P `online`, UI can flicker.

| Issue | Severity | Fix |
|-------|----------|-----|
| Flicker when getMyDevices fails intermittently | **MEDIUM** | Consider preserving previous `byAppInstance` on reject (functional `setByAppInstance(prev => ...)`), or document as acceptable |
| DeviceStatusStore vs isAvailable timing | **LOW** | Status and availability update at different intervals; minor visual inconsistency. Acceptable. |

---

## Summary: Issue Matrix

### HIGH

*None.*

### MEDIUM

| # | File:Line | Issue | Fix |
|---|-----------|-------|-----|
| 1 | AgentDrawer.tsx:110–116 | Intermittent `getMyDevices` failure clears `byAppInstance`; `isAvailable` can flicker | Preserve previous `byAppInstance` on reject, or document |
| 2 | AgentDrawer.tsx:152 | `key: floor.app_instance_id \|\| 'unknown'` — literal `"unknown"` would collide | Use unique key, e.g. `\`floor-${index}\`` |

### LOW

| # | File:Line | Issue | Fix |
|---|-----------|-------|-----|
| 1 | types/index.ts:31 | `available?: boolean` optional | Already correct |
| 2 | devices.py | Old Gateway may omit `available` | Document API contract |
| 3 | AgentDrawer.tsx | DeviceStatusStore vs isAvailable timing | Document as acceptable |

---

## Recommended Fixes

### 8.1 devicesByFloor Key Uniqueness (MEDIUM)

```typescript
// AgentDrawer.tsx:152 — change key to avoid collision when app_instance_id is empty or literal "unknown"
key: floor.app_instance_id || `__empty_${i}`,
// Requires changing loop to: byAppInstance.forEach((floor, i) => { ... })
```

### 8.2 Optional: Preserve byAppInstance on getMyDevices Reject (MEDIUM)

```typescript
// AgentDrawer.tsx:99-100 — use functional update to keep previous on reject
setByAppInstance(prev => {
  const floors = myDevicesRes?.by_app_instance;
  if (Array.isArray(floors)) return floors;
  if (myDevicesSettled.status === 'rejected') return prev;
  return [];
});
```

---

## Verification Checklist

- [x] `pcClientOnlineMap.get(id)` returns `undefined` when key missing — fallback works
- [x] `false ?? x` = `false` (not x) — explicit offline stays false
- [x] `device.available` undefined → `!!(x && undefined)` = false — safe
- [x] listForUser always receives `user_id` → `available` computed
- [x] appInstanceId null → byAppInstance=[] → fallback to device.available
- [x] Device type `available?` — no unsafe assumptions
- [x] Promise.allSettled — both results applied together; no same-call race
