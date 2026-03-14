# OTA Flow & Capability Switch Documentation

This document traces the frontend OTA (Over-The-Air) flow in novaic-app, specifically when `navigate()` to the relay URL happens and at what exact moment the capability switches from `main-cap` (local) to `remote-frontend-capability` (remote).

## 1. Entry Point & Trigger

**Location:** `novaic-app/src-tauri/src/setup.rs`

- `setup_shared()` is called during Tauri app setup (from `lib.rs` desktop path or `mobile.rs`).
- At the end of `setup_shared()` (line 88):
  ```rust
  spawn_frontend_ota_task(app.clone(), read_gateway_url(&gw_url));
  ```
- The OTA task is **spawned asynchronously** and does not block app startup.

## 2. When Does `navigate()` to Relay URL Happen?

**Location:** `setup.rs` lines 119–162

### Timing

`navigate()` is called **only when all of the following are true**:

1. **Release build** (not `cfg!(debug_assertions)`) — dev mode skips OTA entirely.
2. **Gateway fetch succeeds** within 6 seconds:
   - `GET {gw_url}/api/config/frontend` returns 200
   - Response JSON has non-empty `frontend_url` string
   - `frontend_url` parses as valid URL
3. **Window exists** — `app.get_webview_window("main")` returns `Some`.

### Exact Code Path

```
spawn_frontend_ota_task()
  → tokio::async_runtime::spawn(async move { ... })
  → tokio::time::timeout(6s, async { ... })
  → client.get(url).send().await
  → if resp.status().is_success()
  → json.get("frontend_url").and_then(|v| v.as_str())
  → if !frontend_url.is_empty()
  → url::Url::parse(frontend_url) → Ok(nav_url)
  → w.navigate(nav_url)   ← LINE 142
```

### Window Visibility

- Window is created with `visible: false` (tauri.conf.json).
- `show_window()` is called **only at the end** of the OTA task (after success or timeout).
- So the window stays hidden until OTA completes (or times out at 6s).
- If OTA succeeds: `navigate()` is called, then `show_window()`.
- If OTA fails or times out: only `show_window()` runs — user sees local content.

### Gateway Response

**Source:** `novaic-gateway/main_gateway.py` lines 520–537

- Default: `https://relay.gradievo.com/resource/frontend/v0.3.0/`
- Overridable via `FRONTEND_CDN_URL` env var.

## 3. Exact Moment Capability Switches

### Capability Definitions

| Capability | Identifier | Applies to | Permissions |
|------------|------------|------------|-------------|
| **main-cap** | `main-cap` | Local only (`local: true`, no `remote`) | `core:event`, `shell:allow-open`, `opener:allow-open-path`, etc. |
| **remote-frontend-capability** | `remote-frontend-capability` | Local + `https://relay.gradievo.com/*` | `core:default`, `shell:default`, `dialog:default`, etc. |

**Source:** `main.json` and `remote-frontend.json`; merged schema in `gen/schemas/capabilities.json`.

### Capability Resolution (Tauri 2)

- **Local:** Content from bundled app (`tauri://`, asset protocol, etc.).
- **Remote:** Content from `https://` URLs. A capability applies to a remote URL only if its `remote.urls` matches (URLPattern).

### Switch Moment

The capability switches when the **webview’s current document changes**:

1. **Before `navigate()`:** Webview shows local dist (e.g. `tauri://localhost/` or `asset://`).
   - **main-cap** applies (local).
   - **remote-frontend-capability** also applies (it has `local: true`).

2. **`navigate()`:** Starts a navigation; does not wait for load.

3. **During navigation:** Old document may still be active; capabilities still apply to the old URL.

4. **After new document loads:** The webview’s URL becomes `https://relay.gradievo.com/...`.
   - **main-cap** no longer applies (no `remote` config).
   - **remote-frontend-capability** applies (URL matches `https://relay.gradievo.com/*`).

So the switch happens when the **new document becomes the active document** (e.g. `load` event fires).

## 4. Edge Cases

### 4.1 Both Capabilities Apply (Local)

| Scenario | main-cap | remote-frontend-capability |
|----------|----------|----------------------------|
| **Local bundled frontend** | ✅ Yes | ✅ Yes |

Both have `local: true` and target `main`. The user gets the union of permissions.

### 4.2 Neither Capability Applies

| Scenario | main-cap | remote-frontend-capability |
|----------|----------|----------------------------|
| **Gateway returns non-relay URL** | ❌ No | ❌ No |

Example: `FRONTEND_CDN_URL` set to `https://cdn.example.com/frontend/`.

- `navigate()` goes to that URL.
- Page is no longer local → main-cap does not apply.
- URL does not match `https://relay.gradievo.com/*` → remote-frontend-capability does not apply.
- Result: Tauri API calls are denied (no capability).

**Mitigation:** Ensure Gateway returns `https://relay.gradievo.com/*` or update `remote-frontend.json` to include that URL pattern.

### 4.3 Only main-cap (Remote URL Not Relay)

If Gateway returns a URL that is not in `remote.urls`, only main-cap applies to local. After navigation, the remote page has no capability.

### 4.4 OTA Failure / Timeout

- Fetch fails, non-200, 6s timeout, or invalid JSON/URL.
- `navigate()` is never called.
- Page stays on local dist.
- `main-cap` and `remote-frontend-capability` (local) both apply.

### 4.5 Dev Mode

- `spawn_frontend_ota_task` returns early.
- No fetch, no `navigate()`.
- Always local.

### 4.6 User-Initiated Navigation

If the frontend later navigates to another URL (e.g. via `window.location` or `href`):

- Capability is re-evaluated for the new URL.
- If the new URL is not local and not `https://relay.gradievo.com/*`, neither capability applies.

## 5. Sequence Diagram (Release, OTA Success)

```
App start
  │
  ├─ setup_shared()
  │    └─ spawn_frontend_ota_task()  [async, non-blocking]
  │
  ├─ Window "main" created (visible: false)
  │    └─ Loads local dist (index.html)
  │         → main-cap + remote-frontend-capability (local)
  │
  └─ OTA task (parallel):
       │
       ├─ GET /api/config/frontend  [0–6s]
       │
       ├─ Success: frontend_url = "https://relay.gradievo.com/..."
       │    └─ w.navigate(nav_url)   ← NAVIGATE
       │
       ├─ show_window()
       │
       └─ Webview loads new document
            → Capability switches to remote-frontend-capability only
```

## 6. Summary

| Question | Answer |
|----------|--------|
| **When does `navigate()` happen?** | After successful fetch of `/api/config/frontend` (within 6s), in release mode.
| **When does capability switch?** | When the new document from `https://relay.gradievo.com/*` becomes the active document.
| **Both apply?** | Yes, on local: main-cap and remote-frontend-capability both apply.
| **Neither apply?** | Yes, if Gateway returns a URL that is not `https://relay.gradievo.com/*` and the app navigates there.
