# OTA Mode VNC WebSocket Failure — Security Investigation Report

**Context**: In OTA mode, the frontend loads from `https://relay.gradievo.com/resource/frontend/v0.3.0/` instead of local bundled assets. The VNC WebSocket URL is `ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}` — the VncProxy runs locally in the Tauri Rust backend.

**Investigation focus**: When the WebView loads from HTTPS CDN, what security restrictions could block the WebSocket connection to `ws://127.0.0.1`?

---

## Executive Summary

**Primary root cause hypothesis**: **Mixed content blocking** — Browsers and WebKit (used by Tauri's WKWebView on iOS/macOS) block `ws://` (insecure WebSocket) connections from HTTPS pages. This is a standard security policy with no developer override in WKWebView.

**Secondary**: `NSAllowsLocalNetworking` (iOS ATS) does **not** relax mixed content for WebView page context. It only affects app-level network access.

---

## 1. Mixed Content: HTTPS Page → ws:// (Insecure WebSocket)

### Evidence

- **MDN / Browser behavior**: When an HTTPS page attempts to connect to `ws://`, browsers block it as "active mixed content". Error: *"Mixed Content: The page was loaded over HTTPS, but attempted to connect to the insecure WebSocket endpoint. This request has been blocked; this endpoint must be available over WSS."*
- **WebKit Bug 89068**: Explicitly documents blocking mixed-content WebSockets (`ws://` on `https://` pages).
- **CSP cannot override**: Content Security Policy does not relax this browser-level restriction.

### Code Path

| Step | Location | Behavior |
|------|----------|----------|
| OTA navigate | `setup.rs:212` | `w.navigate(nav_url)` → WebView loads `https://relay.gradievo.com/...` |
| Page origin | — | `origin = https://relay.gradievo.com` |
| VNC URL | `vnc_proxy.rs:161-162` | `format!("ws://127.0.0.1:{}/vnc/...", port)` |
| Frontend | `useVNCConnection.ts:58`, `vncStream.ts:255` | `new WebSocket(wsUrl)` with `ws://127.0.0.1:...` |
| Block | WebKit | Mixed content: secure context (HTTPS) → insecure subresource (ws://) → **blocked** |

---

## 2. iOS WKWebView: NSAllowsLocalNetworking

### Current Configuration

- **Info.plist** (`novaic-app/src-tauri/gen/apple/novaic_iOS/Info.plist`):
  ```xml
  <key>NSAppTransportSecurity</key>
  <dict>
      <key>NSAllowsLocalNetworking</key>
      <true/>
  </dict>
  ```
- **patch-ios-xcode.sh** (lines 21–26): Adds `NSAllowsLocalNetworking` for VncProxy WebSocket.

### Does it apply when page origin is remote (relay.gradievo.com)?

**No.** `NSAllowsLocalNetworking` is an **App Transport Security (ATS)** setting. It allows the **native app** to make HTTP/WebSocket requests to localhost. It does **not** change the **WebView page's** mixed content policy.

When the page loads from `https://relay.gradievo.com`:
- The page's origin is the CDN (remote HTTPS).
- The WebSocket is initiated by **JavaScript in the page** (`new WebSocket(wsUrl)`), not by native code.
- Mixed content is enforced in the **page context** (secure origin → insecure subresource).
- Web search and Apple forums confirm: *"On iOS, pages loaded over HTTPS cannot connect to non-secure WebSockets (ws://)"* — even with ATS fully relaxed.

---

## 3. macOS WebView

Same WebKit engine as iOS. Mixed content rules apply identically: HTTPS pages cannot open `ws://` connections. WKWebView does not provide a way to override TLS trust for WebSocket connections to localhost.

---

## 4. Tauri WebView Configuration

### Files checked

| File | Finding |
|------|---------|
| `tauri.conf.json` | `csp: null` — no CSP |
| `capabilities/remote-frontend.json` | `remote.urls`: `https://relay.gradievo.com/*`, `https://api.gradievo.com/*` — allows Tauri invoke from these origins |
| `permissions/allow-app-commands.toml` | Includes `get_vnc_proxy_url` — invoke works |

### Relevance

- Tauri capabilities control **IPC (invoke)** from remote URLs. They do **not** affect `new WebSocket()` in the page.
- The WebSocket is a plain browser API call from JavaScript. Mixed content is enforced by the WebView engine, not by Tauri.

---

## 5. Root Cause Hypotheses (Ranked)

| # | Hypothesis | Likelihood | Supporting Evidence |
|---|------------|------------|----------------------|
| 1 | **Mixed content blocking** (HTTPS → ws://) | **High** | WebKit bug 89068, MDN, Apple forums; matches OTA scenario exactly |
| 2 | NSAllowsLocalNetworking does not apply to page context | **High** | ATS vs. mixed content are separate; page origin is remote |
| 3 | device_id/agent_id bug (from IOS_VNC_WEBSOCKET_ERROR_ANALYSIS.md) | Medium | Only relevant if WebSocket *does* connect; doc says "After ATS fix, ws://127.0.0.1 is allowed" — that was for **local** page origin |
| 4 | CORS | Low | WebSocket to same-origin or localhost typically not CORS-bound; mixed content is the main blocker |

---

## 6. Recommended Solutions

### Option A: Tauri bridge (recommended)

Avoid `new WebSocket(wsUrl)` from the page. Instead:

1. Frontend invokes a Tauri command, e.g. `connect_vnc_stream(agentId, deviceId)`.
2. Rust backend opens `ws://127.0.0.1:{port}/vnc/...` (native code, no mixed content).
3. Backend streams VNC data to frontend via Tauri events or a binary channel.

**Pros**: No mixed content; works with OTA.  
**Cons**: Requires refactoring VNC connection flow.

### Option B: Serve VncProxy over WSS (wss://)

- Add TLS to VncProxy and serve `wss://127.0.0.1:{port}/vnc/...`.
- **Problem**: WKWebView does not allow overriding TLS trust for WebSocket. Self-signed certs for localhost are not trusted, and there is no delegate for WebSocket connections.

### Option C: Disable OTA when VNC is needed

- Use local assets when the user needs VNC; use OTA only for non-VNC flows.
- **Pros**: Simple.  
**Cons**: Limits OTA benefits.

### Option D: Load OTA over HTTP (not recommended)

- Serve OTA from `http://` instead of `https://` so the page is not a secure context.
- **Cons**: Insecure; many CDNs and deployments require HTTPS.

---

## 7. Files Reference

| File | Relevance |
|------|-----------|
| `novaic-app/src-tauri/src/setup.rs` | OTA navigate to CDN |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | `ws_url()` returns `ws://127.0.0.1:...` |
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | `get_vnc_proxy_url` |
| `novaic-app/src/components/Visual/useVNCConnection.ts` | `new WebSocket(wsUrl)` |
| `novaic-app/src/services/vncStream.ts` | `new WebSocket(url)` |
| `novaic-app/src-tauri/gen/apple/novaic_iOS/Info.plist` | NSAllowsLocalNetworking |
| `novaic-app/scripts/patch-ios-xcode.sh` | ATS patch |
| `novaic-app/src-tauri/capabilities/remote-frontend.json` | Remote URL capability |

---

## 8. Verification Steps

1. **Console error**: In OTA mode, open WebView devtools and attempt VNC. Look for: *"Mixed Content: ... insecure WebSocket ... blocked"*.
2. **Local vs OTA**: Compare local assets (`tauri://localhost` or `http://localhost`) vs OTA (`https://relay.gradievo.com`). VNC should work with local, fail with OTA.
3. **Platform**: Reproduce on both iOS and macOS to confirm WebKit behavior.
