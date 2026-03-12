# VNC WebSocket OTA Mode — Mixed Content Investigation Report

**Date**: 2026-03-12  
**Context**: VNC WebSocket connection failure in OTA mode  
**Scenario**: Page loads from `https://relay.gradievo.com`, JavaScript does `new WebSocket('ws://127.0.0.1:port')`  
**Question**: Could mixed content (HTTPS page → ws://) block the WebSocket in WKWebView?

---

## Executive Summary

**Yes, `ws://` from an HTTPS remote page can be blocked in WKWebView** due to mixed-content restrictions. This is **independent of App Transport Security (ATS)** and `NSAllowsLocalNetworking`. The blocking occurs at the WebKit content layer, not the app layer.

| Factor | Finding |
|--------|---------|
| **ATS / NSAllowsLocalNetworking** | Does **not** override WebSocket mixed-content blocking in WebView content |
| **Mixed content** | WebKit blocks ws:// from HTTPS pages by design (Bug 89068) |
| **OTA vs local** | OTA (remote HTTPS origin) is the problematic case; local asset load may behave differently |
| **Platform** | iOS and macOS WKWebView share the same WebKit engine and mixed-content rules |

---

## 1. Current Configuration

### 1.1 iOS Info.plist (novaic_iOS/Info.plist)

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

- **NSAllowsLocalNetworking**: Present and `true`
- **NSAllowsArbitraryLoads**: Not present
- **NSExceptionDomains**: Not present

### 1.2 patch-ios-xcode.sh

The script injects only:

- `NSAppTransportSecurity` dict
- `NSAllowsLocalNetworking` = `true`

**Purpose** (from script comment): Allow `ws://127.0.0.1` (VncProxy WebSocket) that iOS would otherwise block.

**Scope**: ATS applies to **app-level** network requests (e.g. Rust `reqwest`, native HTTP). It does **not** control WebView content security policy.

---

## 2. ATS vs Mixed Content — Two Layers

| Layer | What it controls | Applies to OTA scenario? |
|-------|------------------|---------------------------|
| **ATS** | App’s own HTTP/HTTPS/WebSocket to localhost | No — page content is in WebView |
| **Mixed content** | Web content: HTTPS page → insecure subresources (ws://, http://) | Yes — page origin is `https://relay.gradievo.com` |

In OTA mode:

1. `setup.rs` navigates to `https://relay.gradievo.com/resource/frontend/v0.3.0/`
2. Page origin = `https://relay.gradievo.com` (secure context)
3. `vncStream.ts` / noVNC does `new WebSocket('ws://127.0.0.1:port/vnc/...')`
4. This is **active mixed content**: secure context → insecure WebSocket

WebKit treats this as mixed content and blocks it, regardless of ATS settings.

---

## 3. WebKit / WKWebView Behavior

### 3.1 WebKit Bug 89068

- **Title**: Do not allow mixed-content WebSockets (ws:// WebSockets on an https:// page)
- **Status**: Resolved / Configuration Changed
- **Effect**: WebKit blocks ws:// connections from HTTPS pages by design.

### 3.2 Apple Developer Forums / Community

- WebSocket validation in WKWebView is **separate** from ATS.
- ATS exceptions (including `NSAllowsLocalNetworking`) **do not** affect WebSocket mixed-content blocking.
- Apple DTS recommends `WKScriptMessage` for web-to-native communication instead of WebSockets to avoid these restrictions.

### 3.3 WebKit PR #27270 (April 2024)

- **Scope**: Passive resources (images, video, audio) and localhost.
- **Change**: Don’t upgrade connections to localhost; keep previous mixed-content behavior on iOS via Linked-On-Or-After.
- **Does not apply**: Active mixed content (WebSocket, XHR, scripts) — still blocked.

### 3.4 iOS 18 Regression

- Regression: iOS 18 blocked loading localhost content from HTTPS.
- Fix: Treat localhost as a potentially trustworthy origin, but this applies to **passive** content (e.g. images), not to WebSocket.

---

## 4. OTA vs Local Load

| Scenario | Page origin | Mixed content? | ws:// likely |
|----------|-------------|----------------|--------------|
| **Local assets** | `asset://localhost/` or `tauri://localhost/` or file | Depends on context | Possibly allowed |
| **OTA** | `https://relay.gradievo.com` | Yes | **Blocked** |

`IOS_VNC_WEBSOCKET_ERROR_ANALYSIS.md` states: “After ATS fix (NSAllowsLocalNetworking), ws://127.0.0.1 is allowed. Connection attempts but fails with reset.”

- That analysis was for **connection reset** (P2P locate failure), not for mixed-content blocking.
- It may have been observed in **local** load mode (no OTA), where mixed content is not an issue.
- In OTA mode, the page is loaded from HTTPS, so mixed content is expected to block ws:// before any connection attempt.

---

## 5. Platform-Specific Behavior

| Platform | WKWebView | Mixed content | ws:// from HTTPS |
|----------|-----------|---------------|-------------------|
| **iOS** | Yes | Same WebKit rules | Blocked |
| **macOS** | Yes | Same WebKit rules | Blocked |

Both use the same WebKit engine and mixed-content policy. macOS behavior is effectively the same as iOS.

---

## 6. Conclusion

**Yes, `ws://` from an HTTPS remote page can be blocked in WKWebView** due to mixed-content restrictions. This is **independent of ATS** and `NSAllowsLocalNetworking`.

| Question | Answer |
|----------|--------|
| Does ATS/NSAllowsLocalNetworking allow ws:// in WebView? | No — it does not affect WebView content security. |
| Does mixed content block ws:// from HTTPS? | Yes — WebKit blocks ws:// from HTTPS pages by design. |
| Does remote-origin page get different treatment? | Yes — remote HTTPS origin is a secure context; ws:// is active mixed content and blocked. |
| OTA vs local? | OTA (remote HTTPS) is the problematic case; local asset load may behave differently. |

---

## 7. Recommended Workarounds

1. **Use WKScriptMessage instead of WebSocket** (Apple’s recommendation)  
   - Native bridge: JS → WebView → native handler → WebSocket.  
   - Avoids mixed content entirely.

2. **Avoid OTA for VNC**  
   - Load VNC from local assets (e.g. asset:// or local file) so origin is not HTTPS.  
   - Mixed content rules may not apply.

3. **Use wss://**  
   - Requires a valid TLS certificate for `127.0.0.1:port`.  
   - Self-signed certs for localhost cannot be overridden in WKWebView (unlike regular HTTPS requests).

4. **Proxy via relay**  
   - Relay accepts wss:// and proxies to local ws://.  
   - Requires relay infrastructure changes.

5. **Tauri invoke + native WebSocket**  
   - Frontend: `invoke('get_vnc_stream')` or similar.  
   - Rust: native WebSocket client to local VncProxy; stream data via IPC or bridge.  
   - Avoids WebView WebSocket entirely.

---

## 8. References

| Source | Location |
|--------|----------|
| WebKit Bug 89068 | https://bugs.webkit.org/show_bug.cgi?id=89068 |
| WebKit PR #27270 (localhost mixed content) | https://github.com/WebKit/WebKit/pull/27270 |
| Apple Developer Forums (mixed content) | https://developer.apple.com/forums/thread/120869 |
| iOS VNC WebSocket Error Analysis | `novaic-app/docs/IOS_VNC_WEBSOCKET_ERROR_ANALYSIS.md` |
| HANDOVER.md VNC sections | `HANDOVER.md` (lines ~1006–1010) |
| patch-ios-xcode.sh | `novaic-app/scripts/patch-ios-xcode.sh` |
| Info.plist | `novaic-app/src-tauri/gen/apple/novaic_iOS/Info.plist` |
