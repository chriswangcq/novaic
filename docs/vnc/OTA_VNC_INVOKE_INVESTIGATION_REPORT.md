# OTA Mode VNC Connection — Invoke Investigation Report

**Date:** 2026-03-12  
**Focus:** Whether `invoke('get_vnc_proxy_url', { agentId, deviceId })` works in OTA mode (page from relay.gradievo.com), and what happens when it fails.

---

## Executive Summary

**Invoke should succeed in OTA mode** when the WebView is loaded from `https://relay.gradievo.com/*` or `https://api.gradievo.com/*`. The configuration is correctly set up. If VNC fails in OTA mode, the more likely cause is **WebSocket connection failure** (e.g. `ws://127.0.0.1:port/vnc/...` unreachable) rather than invoke failure.

---

## 1. Tauri Remote Frontend Capability

**File:** `novaic-app/src-tauri/capabilities/remote-frontend.json`

```json
{
  "identifier": "remote-frontend-capability",
  "description": "Allow OTA frontend CDN URLs to use Tauri API (relay/api.gradievo.com)",
  "windows": ["main"],
  "remote": {
    "urls": [
      "https://relay.gradievo.com/*",
      "https://api.gradievo.com/*"
    ]
  },
  "permissions": [
    "core:default",
    "allow-app-commands",
    ...
  ]
}
```

- When the WebView navigates to `relay.gradievo.com` or `api.gradievo.com`, Tauri matches the current URL against `remote.urls` and applies this capability.
- The capability grants `allow-app-commands`, which enables the command allowlist from `allow-app-commands.toml`.

---

## 2. Command Allowlist — `get_vnc_proxy_url` Is Allowed

**File:** `novaic-app/src-tauri/permissions/allow-app-commands.toml`

```toml
commands.allow = [
  ...
  "get_vnc_proxy_url",
  "get_scrcpy_proxy_url",
]
```

`get_vnc_proxy_url` is explicitly allowed. Without this, invoke would fail with **"Not allowed to request resource"** (as noted in the file comments).

---

## 3. Origin / URL Validation

| Layer | Validation | Effect on OTA |
|-------|------------|---------------|
| **OTA navigate** | `setup.rs` → `OTA_ALLOWED_HOSTS` = `["relay.gradievo.com", "api.gradievo.com"]` | Only these hosts are navigated to; others fall back to local assets |
| **Tauri capability** | `remote.urls` glob: `https://relay.gradievo.com/*`, `https://api.gradievo.com/*` | Invoke allowed only when WebView is on these origins |
| **Frontend fallback** | `main.tsx` → `OTA_ORIGINS` = `['https://relay.gradievo.com', 'https://api.gradievo.com']` | If `__TAURI__` is absent (pure browser), shows `TauriRequiredFallback` instead of App |

**Potential invoke failure in OTA mode:**

1. **Different CDN host**  
   If Gateway returns a URL like `https://cdn.gradievo.com/...` or another host, it would:
   - Be rejected by `OTA_ALLOWED_HOSTS` in `setup.rs` → no navigate to that URL.
   - If navigate were allowed elsewhere, the capability would not match → invoke would fail with "Not allowed to request resource".

2. **Pure browser**  
   If the user opens the CDN URL in a normal browser (not inside the Tauri app), `__TAURI__` is absent → `TauriRequiredFallback` is shown and the App (and thus invoke) is never used.

---

## 4. End-to-End Flow

```
Frontend (OTA: relay.gradievo.com)
    │
    ├─ vmService.getVncUrl(agentId, deviceId)
    │       │
    │       └─ invoke('get_vnc_proxy_url', { agentId, deviceId })
    │               │
    │               ├─ Tauri checks: WebView origin matches remote.urls? ✓
    │               ├─ Capability grants allow-app-commands? ✓
    │               └─ get_vnc_proxy_url in commands.allow? ✓
    │
    └─ Returns: "ws://127.0.0.1:<port>/vnc/<device_id>/<agent_id>"
            │
            └─ new WebSocket(url)  ← possible failure point
```

**Call sites:**

- `vm.ts` L164–167: `vmService.getVncUrl()` → `invoke('get_vnc_proxy_url', ...)`
- `vncStream.ts` L131–137: `vmService.getVncUrl(agentId, deviceId)` with `.catch()` for invoke errors
- `useVNCConnection.ts` L56: `vmService.getVncUrl(agentId, deviceId ?? undefined)`
- `useDeviceVNCConnection.ts` L52: `vmService.getVncUrl(deviceId)`
- `VmUserVNCView.tsx` L42: `vmService.getVncUrl(\`${deviceId}:${username}\`)`

---

## 5. Error Handling and User-Visible Behavior

### If `invoke` fails

| Caller | Handling | User-visible |
|--------|-----------|--------------|
| `vncStream.ts` | `.catch()` → `notifySubscribers(state, 'error', msg)` | Subscribers see error; status → `'error'` |
| `VmUserVNCView.tsx` | `try/catch` → `setErrorMsg(e?.message ?? 'Failed to get VNC URL')` | Error message shown in UI |
| `useVNCConnection.ts` | `checkWebSocket` catch → `setWsReady(false)`, status `'starting'` | Retries; no explicit error message |
| `useDeviceVNCConnection.ts` | `checkWebSocket` catch → `setStatus('starting')` | Retries; no explicit error message |

### If `invoke` succeeds but WebSocket fails

- `vncStream.ts`: `testWebSocket()` fails → `state.wsUrl = null`, throws `'VNC WebSocket not available'` → subscribers get error.
- `VmUserVNCView.tsx`: RFB connection fails → `setErrorMsg(e?.message ?? 'RFB connection failed')`.
- `useVNCConnection.ts` / `useDeviceVNCConnection.ts`: WebSocket probe fails → status stays `'starting'`, retries every 3s.

---

## 6. Conclusions and Recommendations

### Invoke in OTA mode

- Configuration is correct: `get_vnc_proxy_url` is allowed for `relay.gradievo.com` and `api.gradievo.com`.
- Invoke should succeed when the WebView is loaded from these OTA origins.

### If VNC fails in OTA mode

1. **Invoke failure**  
   - Check console for "Not allowed to request resource" or similar.  
   - Confirm Gateway `frontend_url` uses `relay.gradievo.com` or `api.gradievo.com` (not another host).

2. **WebSocket failure (more likely)**  
   - `ws://127.0.0.1:port/vnc/...` must be reachable from the WebView.  
   - On mobile (e.g. iOS), `127.0.0.1` refers to the device itself; if the VNC proxy runs on a different host (e.g. desktop), the WebSocket will fail.  
   - Check `vnc_proxy.rs` and how `ws_url` is built for remote vs local.

### Debugging

- Set `sessionStorage.setItem('novaic_ota_debug', '1')` and reload to log `{ hasTauri, origin }` in `main.tsx`.
- Add logging around `invoke('get_vnc_proxy_url', ...)` and `new WebSocket(url)` to distinguish invoke vs WebSocket failures.

---

## 7. File Reference

| File | Role |
|------|------|
| `capabilities/remote-frontend.json` | Grants OTA origins access to Tauri API |
| `permissions/allow-app-commands.toml` | Allowlist including `get_vnc_proxy_url` |
| `commands/vnc_urls.rs` | `get_vnc_proxy_url` implementation |
| `src/services/vm.ts` | `getVncUrl()` → invoke |
| `src/main.tsx` | OTA origin check, `TauriRequiredFallback` |
| `src-tauri/src/setup.rs` | OTA navigate, `OTA_ALLOWED_HOSTS` |
